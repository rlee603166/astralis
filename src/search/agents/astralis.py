# src/search/astralis.py

import re
import json
import asyncio
from uuid import UUID
import redis.asyncio as redis
from openai import AsyncOpenAI
from fastapi import HTTPException
from search.services.rag_service import RAGService
from search.services.prompt_manager import PromptManager
from typing import List, Dict, Any, AsyncGenerator
from sqlalchemy import select, and_, or_, func, text, inspect 
from sqlalchemy.orm import selectinload, aliased
from database.models import User, Experience, Skill
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


SESSION_EXPIRATION_SECONDS = 3600

class Astralis:
    """
    Secret Sauce bbg - Now with Session Memory!
    """
    def __init__(
        self,
        model: str,
        client: AsyncOpenAI,
        psql_db: async_sessionmaker[AsyncSession],
        vector_db: RAGService,
        prompt_manager: PromptManager,
        redis_client: redis.Redis
    ):
        self.model = model
        self.client = client
        self.psql_db_factory = psql_db
        self.vector_db = vector_db
        self.prompt_manager = prompt_manager
        self.redis_client = redis_client

    """
    Core Functions
    """
    async def run(self, user_query: str, session_id: UUID) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the agentic search process, now with clarification handling.
        Loads history from Redis, processes the query, and saves history back.
        """
        self.context: Dict[str, Any] = {}
        self.context["conversation"] = await self._load_history(session_id)
        self.context["user_query"] = user_query
        user_msg = { "role": "user", "content": user_query }
        await self._save_message(session_id, user_msg)

        self.context.pop('needs_clarification', None)
        self.context.pop('clarification_question', None)

        print(f"[RUN START]: Session {session_id}, Query: '{user_query}', History Len: {len(self.context['conversation'])}")
        yield { "type": "start", "message": "Starting to process your query", "session_id": session_id }

        try:
            while True:
                # --- Thought Generation ---
                thought = ""
                async for thought_chunk in self._generate_thought():
                    thought += thought_chunk
                    yield { "type": "thought", "message": thought_chunk }
                print(f"[THOUGHT]: {thought}")
                # --- End Thought Generation ---

                # --- Action Determination ---
                yield { "type": "status", "message": "Determining next action" }
                raw_action = ""
                async for raw_chunk in self._determine_action(thought):
                    raw_action += raw_chunk
                closed_raw_action = self._ensure_closing_tags(raw_action, "action")
                closed_raw_action = self._ensure_closing_tags(closed_raw_action, "input")
                action_raw = self._extract_xml(closed_raw_action, "action").strip()
                action = action_raw.strip('[]').strip()
                input_text = self._extract_xml(closed_raw_action, "input").strip()
                yield { "type": "action", "message": action }
                print(f"[ACTION]: {action}")
                print(f"[INPUTS]: {input_text}")

                # Parse action inputs carefully
                action_inputs: Dict[str, Any] = {}
                if action not in ["finish"] and input_text:
                    try:
                        action_inputs = json.loads(input_text)
                        print(f"Action inputs parsed: {action_inputs}")
                    except json.JSONDecodeError:
                        print(f"[ERROR]: Failed to parse action input JSON: {input_text}")
                        # Decide how to handle bad input format from LLM
                        # Option 1: Ask for clarification about the format?
                        # Option 2: Try to finish gracefully?
                        # Option 3: Raise an internal error?
                        # For now, let's yield an error and force finish
                        yield { "type": "error", "message": f"Invalid action input format received: {input_text}" }
                        action = "finish"
                        action_inputs = {}
                # --- End Action Determination ---

                yield { "type": "status", "message": f"Executing action: {action}" }

                # --- Action Execution ---
                result_users: List[User] = []
                # Reset clarification flag before executing action
                self.context['needs_clarification'] = False
                self.context['clarification_question'] = None

                if action != "finish":
                    try:
                        result_users = await self._execute_action(action, action_inputs)
                        if result_users and not self.context.get('needs_clarification'):
                            yield { "type": "users", "message": [res.to_dict() for res in result_users] }
                        print(f"[RESULT]: Found {len(result_users)} users.")
                    except HTTPException as e:
                        print(f"[ERROR] HTTP Exception during action execution: {e.detail}")
                        yield { "type": "error", "message": f"Action failed: {e.detail}" }
                        result_users = [] # Ensure result is empty on error
                    except Exception as e:
                        print(f"[ERROR] Unexpected Exception during action execution: {e}")
                        yield { "type": "error", "message": f"An unexpected error occurred: {e}" }
                        result_users = []
                # --- End Action Execution ---

                # --- Handle Clarification Request ---
                # Check if the action execution decided clarification is needed
                if self.context.get('needs_clarification'):
                    question = self.context.get('clarification_question', "Could you please provide more details?")
                    print(f"[CLARIFICATION]: Asking user: '{question}'")
                    yield {
                        "type": "clarification_request",
                        "message": question
                    }
                    # Append the clarification attempt to history *before* saving and returning
                    # Ensure action_inputs contains the question dict if parsed, otherwise use default
                    clarification_input = action_inputs if action == "request_clarification" else {"question": question}
                    self.context.setdefault('memory', []).append({
                        "thought": thought,
                        "action": "request_clarification",
                        "action_input": clarification_input,
                        "result": []
                    })
                    # await self._save_history(session_id, self.context['memory'])
                    yield { "type": "end", "message": "Waiting for user clarification." }
                    print(f"[RUN END]: Paused for clarification in session {session_id}.")
                    return
                # --- End Handle Clarification Request ---

                # --- History Update (only if not clarification) ---
                # Prepare result for history (use for_llm format)
                history_result = [res.for_llm() for res in result_users] if result_users else []
                self.context.setdefault('memory', []).append({
                    "thought": thought,
                    "action": action,
                    "action_input": action_inputs,
                    "result": history_result
                })
                # --- End History Update ---

                # --- Completion Check ---
                # Check if the *last appended action* was 'finish'
                if self._is_task_complete():
                    final_response_content = ""
                    async for final_chunk in self._generate_final_response():
                        final_response_content += final_chunk
                        yield { "type": "response", "message": final_chunk }

                    final_users = []
                    async for user in self._generate_final_users(final_response_content):
                        final_users.append(user)


                    yield { "type": "users_found", "message": final_users }

                    print(f"[FINAL USERS]: {final_users}")
                    print(f"[RESPONSE]: Final response generated.")
                    print(f"[RESPONSE CONTENT]: {final_response_content}")

                    yield { "type": "end", "message": "Task completed successfully." }
                    # await self._save_history(session_id, self.context['memory'])

                    final_users_str = json.dumps(final_users)

                    final_response_content += f"""\n
                    <full profiles> 
                    {final_users_str}
                    </full profiles>
                    """

                    astralis_msg = { "role": "assistant", "content": final_response_content }
                    await self._save_message(session_id, astralis_msg)

                    return 
                # --- End Completion Check ---

                # Loop continues if not finished and no clarification needed

        except Exception as e:
            print(f"[ERROR] Unhandled exception in agent run loop for session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            yield { "type": "error", "message": f"An unexpected error occurred during processing: {e}" }
            yield { "type": "end", "message": "Task ended due to an error." }
            # if 'memory' in self.context:
            #     await self._save_session(session_id)
                 # await self._save_history(session_id, self.context['memory'])

        finally:
            print(f"[RUN END]: Session {session_id} processing finished.")


    async def _generate_thought(self):
        memory = self.context.get('memory', [])
        formatted_hist = self._formatted_history(memory)

        THOUGHT_PROMPT = self.prompt_manager.get_prompt(
            "THOUGHT_PROMPT",
            query=self.context.get('user_query', ''),
            observation_history=formatted_hist
        )
        async for chunk in self._llm_call(user_prompt=THOUGHT_PROMPT):
            yield chunk


    async def _determine_action(self, thought):
        ACTION_PROMPT = self.prompt_manager.get_prompt("ACTION_PROMPT", thought=thought)
        async for chunk in self._llm_call(ACTION_PROMPT):
            yield chunk


    def _is_task_complete(self) -> bool:
        history = self.context.get('memory', [])
        if history:
            last_step = history[-1]
            print(f"Checking completion: Last action was '{last_step.get('action')}'")
            return last_step.get('action') == 'finish'
        return False


    async def _generate_final_response(self):
        memory = self.context.get('memory', [])
        formatted_hist = self._formatted_history(memory)
        RESPONSE_PROMPT = self.prompt_manager.get_prompt(
            "RESPONSE_PROMPT",
            query=self.context.get('user_query', ''),
            observation_history=formatted_hist
        )
        async for chunk in self._llm_call(RESPONSE_PROMPT):
            yield chunk

    async def _generate_final_users(self, final_response):
        memory = self.context.get('memory', [])
        formatted_hist = self._formatted_history(memory) + final_response
        FORMAT_USERS_PROMPT = self.prompt_manager.get_prompt(
            "FORMAT_USERS_PROMPT",
            observation_history=formatted_hist
        )
        final_chunks = ""
        async for chunk in self._llm_call(FORMAT_USERS_PROMPT):
            final_chunks += chunk

        print(f"[USERS]: {final_chunks}")
        user_ids = self._extract_xml(final_chunks, "user_id")
        user_ids = json.loads(user_ids)
        for user_id in user_ids:
            user = await self._get_user_profile(user_id)
            yield user.to_dict()


    async def _llm_call(self, user_prompt: str = ''):
        if not user_prompt:
            print("[WARN] LLM call attempted with empty prompt.")
            yield ""
            return

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    { "role": "user", "content": user_prompt }
                ],
                model=self.model,
                stream=True,
                temperature=0.1,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"[ERROR] LLM API call failed: {e}")
            yield f"Error communicating with LLM: {e}"


    async def _load_history(self, session_id: UUID):
        async with self.psql_db_factory() as session:
            try:
                query = text(f"""
                SELECT role, content
                FROM chat_messages
                WHERE session_id = :session_id
                ORDER BY created_at;
                """)
                result = await session.execute(
                    query,
                    { "session_id": str(session_id) }
                )
                rows = result.mappings().all()
                if not rows:
                    print(f"[INFO] There is not session with session_id: {session_id}")
                    return []
                return rows
            except Exception as e:
                print(f"[ERROR] Database error fetching session {session_id}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error fetching session {session_id}"
                )


    async def _save_message(self, session_id, message):
        async with self.psql_db_factory() as session:
            try:
                role = message["role"]
                content = message["content"]

                query = text(f"""
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (:session_id, :role, :content)
                """)

                await session.execute(
                    query,
                    {
                        "session_id": str(session_id),
                        "role": role,
                        "content": content
                    }
                )
                await session.commit()

            except Exception as e:
                print(f"[ERROR] Database error saving message, session_id: {session_id}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error saving message, session_id: {session_id}"
                )



    def _formatted_conversation(self) -> str:
        formatted = ""
        conversation = self.context.get("conversation", []) 

        if not conversation:
            return "<no history yet>" 

        formatted += "<conversation>\n"
        for message in conversation:
            if message["role"] == "user":
                formatted += f"<user>{message['content']}</user>\n"
            elif message["role"] == "assistant":
                formatted += f"<assistant>{message['content']}</assistant>\n"
        formatted += "</conversation>\n"

        return formatted
                

    def _formatted_history(self, memory: List[Dict[str, Any]]) -> str:
        formatted = self._formatted_conversation()
        if not memory:
            return formatted

        formatted += "<thought_chain>\n"
        for i, obs in enumerate(memory):
            thought = obs.get('thought', 'N/A')
            action = obs.get('action', 'N/A')
            action_input = json.dumps(obs.get('action_input', {}))
            result = json.dumps(obs.get('result', 'N/A'))

            formatted += f"<step index=\"{i}\">\n"
            formatted += f"  <thought>{thought}</thought>\n"
            formatted += f"  <action>{action}</action>\n"
            formatted += f"  <action_input>{action_input}</action_input>\n"
            formatted += f"  <result>{result}</result>\n"
            formatted += f"</step>\n"
        formatted += "</thought_chain>\n"
        return formatted

    def _ensure_closing_tags(self, response_text: str, tag_name: str) -> str:
        open_tag = f"<{tag_name}>"
        close_tag = f"</{tag_name}>"
        if open_tag in response_text and close_tag not in response_text:
            return response_text.rstrip() + f"\n{close_tag}"
        return response_text

    def _extract_xml(self, text: str, tag: str) -> str:
        match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> List[User]:
        action = action.lower()
        print(f"Executing action: {action} with input: {action_input}")

        if action == "search_vector_db":
            query = action_input.get("query")
            namespace = action_input.get("namespace")
            top_k = action_input.get("top_k", 5)

            if not query or not namespace:
                print("[ERROR] Missing 'query' or 'namespace' for search_vector_db")
                raise HTTPException(status_code=400, detail="Missing required parameters for vector search.")

            allowed_namespaces = ['experience', 'education', 'skill', 'summary']
            if namespace not in allowed_namespaces:
                print(f"[ERROR] Invalid namespace '{namespace}' for search_vector_db")
                raise HTTPException(status_code=400, detail=f"Invalid namespace '{namespace}'. Allowed: {allowed_namespaces}")

            try:
                vector_results = self.vector_db.query_vector(
                    query=str(query),
                    namespace=str(namespace),
                    top_k=int(top_k)
                )

                user_ids = []
                if vector_results and 'matches' in vector_results:
                    for match in vector_results['matches']:
                        if 'metadata' in match and 'user_id' in match['metadata']:
                            user_ids.append(match['metadata']['user_id'])
                        else:
                            print(f"[WARN] Vector match missing metadata or user_id: {match.get('id')}")

                unique_user_ids = list(set(user_ids))
                print(f"Found {len(unique_user_ids)} unique user IDs from vector search.")

                if not unique_user_ids:
                    return []

                tasks = [self._get_user_profile(uid) for uid in unique_user_ids]
                fetched_users_results = await asyncio.gather(*tasks, return_exceptions=True)

                fetched_users = []
                for i, result in enumerate(fetched_users_results):
                    if isinstance(result, User):
                        fetched_users.append(result)
                    elif isinstance(result, Exception):
                        print(f"[ERROR] Failed to fetch profile for user_id {unique_user_ids[i]}: {result}")

                return fetched_users

            except Exception as e:
                print(f"[ERROR] Failed during vector search or profile fetching: {e}")
                raise HTTPException(status_code=500, detail=f"Vector search/profile fetch failed: {e}")

        elif action == "fetch_profile":
            user_id = None
            if isinstance(action_input, str):
                user_id = action_input
            elif isinstance(action_input, dict):
                user_id = action_input.get("user_id")

            if not user_id:
                print("[ERROR] Missing 'user_id' for fetch_profile")
                raise HTTPException(status_code=400, detail="Missing user_id for fetch_profile action.")

            try:
                user = await self._get_user_profile(str(user_id))
                return [user] if user else []
            except HTTPException as e:
                print(f"[INFO] Fetch profile: User {user_id} not found.")
                return []
            except Exception as e:
                print(f"[ERROR] Failed fetching profile for {user_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch profile {user_id}: {e}")

        elif action == "filter_structured":
            filters = action_input.get("filters", {})
            user_ids = action_input.get("user_ids", [])

            if not isinstance(user_ids, list) or not user_ids:
                print("[WARN] filter_structured called without valid user_ids list.")
                return []

            if not isinstance(filters, dict) or not filters:
                 print("[WARN] filter_structured called without filters. Returning original list.")
                 tasks = [self._get_user_profile(uid) for uid in user_ids]
                 fetched_users_results = await asyncio.gather(*tasks, return_exceptions=True)
                 fetched_users = [res for res in fetched_users_results if isinstance(res, User)]
                 return fetched_users

            print(f"Applying structured filters: {filters} to {len(user_ids)} user IDs.")

            # Base query to select user IDs from the input list
            query = select(User.user_id).where(User.user_id.in_(user_ids)).distinct()

            filter_conditions = []

            # --- Filter Translation Logic ---

            # Location Filter (Experience)
            if "location" in filters:
                location_filter = filters["location"]
                if isinstance(location_filter, str) and location_filter.strip():
                    location_subquery = (
                        select(Experience.experience_id)
                        .where(
                            Experience.user_id == User.user_id,
                            Experience.location.ilike(f"%{location_filter.strip()}%")
                        )
                        .exists()
                    )
                    filter_conditions.append(location_subquery)
                    print(f"  - Added location filter: ILIKE '%{location_filter.strip()}%'")
                else:
                    print(f"[WARN] Invalid or empty location filter value: {location_filter}. Skipping.")

            # Company Name Filter (Experience)
            if "company_name" in filters:
                company_filter = filters["company_name"]
                if isinstance(company_filter, str) and company_filter.strip():
                    company_subquery = (
                        select(Experience.experience_id)
                        .where(
                            Experience.user_id == User.user_id,
                            Experience.company_name.ilike(f"%{company_filter.strip()}%")
                        )
                        .exists()
                    )
                    filter_conditions.append(company_subquery)
                    print(f"  - Added company_name filter: ILIKE '%{company_filter.strip()}%'")
                else:
                    print(f"[WARN] Invalid or empty company_name filter value: {company_filter}. Skipping.")

            # Job Title Filter (Experience)
            if "job_title" in filters:
                title_filter = filters["job_title"]
                if isinstance(title_filter, str) and title_filter.strip():
                     title_subquery = (
                         select(Experience.experience_id)
                         .where(
                             Experience.user_id == User.user_id,
                             Experience.job_title.ilike(f"%{title_filter.strip()}%")
                         )
                         .exists()
                     )
                     filter_conditions.append(title_subquery)
                     print(f"  - Added job_title filter: ILIKE '%{title_filter.strip()}%'")
                else:
                     print(f"[WARN] Invalid or empty job_title filter value: {title_filter}. Skipping.")

            # Skill Filter (Skill)
            if "skill" in filters:
                skill_filter = filters["skill"]
                if isinstance(skill_filter, str) and skill_filter.strip():
                    skill_subquery = (
                        select(Skill.skill_id)
                        .where(
                            Skill.user_id == User.user_id,
                            func.lower(Skill.skill_name) == func.lower(skill_filter.strip())
                        )
                        .exists()
                    )
                    filter_conditions.append(skill_subquery)
                    print(f"  - Added skill filter: = '{skill_filter.strip()}' (case-insensitive)")
                else:
                    print(f"[WARN] Invalid or empty skill filter value: {skill_filter}. Skipping.")

            ### IMPORTANT: Add more supported filter translations here in the future... ###

            # --- End Filter Translation ---

            # Apply the combined filters if any were added
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
                print(f"Applied {len(filter_conditions)} filter conditions.")
            else:
                 print("[INFO] No valid filters applied.")
                 pass

            # Execute the query to get the filtered user IDs
            filtered_ids = []
            try:
                async with self.psql_db_factory() as session:
                    print(f"Executing filter query...")
                    # Optional: Print compiled SQL for debugging
                    # from sqlalchemy.dialects import postgresql
                    # print(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
                    result = await session.execute(query)
                    filtered_ids = result.scalars().all()
                print(f"Filter query returned {len(filtered_ids)} user IDs.")
            except Exception as e:
                 print(f"[ERROR] Database error during structured filtering: {e}")
                 raise HTTPException(status_code=500, detail=f"Database error during filtering: {e}")

            filtered_users: List[User] = []
            if filtered_ids:
                unique_filtered_ids = list(set(filtered_ids))
                if len(unique_filtered_ids) < len(filtered_ids):
                    print(f"[INFO] Deduplicated filtered IDs from {len(filtered_ids)} to {len(unique_filtered_ids)}")

                tasks = [self._get_user_profile(uid) for uid in unique_filtered_ids]
                fetched_users_results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, res in enumerate(fetched_users_results):
                     if isinstance(res, User):
                         filtered_users.append(res)
                     elif isinstance(res, Exception):
                         print(f"[ERROR] Failed to fetch profile post-filter for user_id {unique_filtered_ids[i]}: {res}")
            else:
                 print("No users matched the structured filters.")

            return filtered_users

        elif action == "request_clarification":
            question = action_input.get("question", "Could you please provide more details?")
            if not isinstance(question, str) or not question.strip():
                 print("[WARN] Invalid or empty question provided for clarification. Using default.")
                 question = "Could you please provide more details or clarify your request?"

            self.context['needs_clarification'] = True
            self.context['clarification_question'] = question.strip()
            print(f"  - Set clarification flags. Question: '{self.context['clarification_question']}'")
            return [] 

        elif action == "finish":
            print("[INFO] 'finish' action recognized.")
            return []
        else:
            print(f"[WARN] Unknown action received: {action}")
            return []

    async def _get_user_profile(self, user_id: str) -> User | None:
        print(f"Fetching profile for user_id: {user_id}")
        query = (
            select(User)
            .options(
                selectinload(User.projects),
                selectinload(User.educations),
                selectinload(User.experiences),
                selectinload(User.skills)
            )
            .where(User.user_id == user_id)
        )

        async with self.psql_db_factory() as session:
            try:
                result = await session.execute(query)
                user = result.scalars().first()
                if not user:
                    print(f"[INFO] User profile not found for id: {user_id}")
                    return None
                return user
            except Exception as e:
                print(f"[ERROR] Database error fetching profile {user_id}: {e}")
                raise HTTPException(status_code=500, detail=f"Database error fetching profile {user_id}")

    # async def _load_history(self, session_id: str) -> List[Dict[str, Any]]:
    #     """Loads conversation history from Redis."""
    #     history_key = f"session:{session_id}:history"
    #     try:
    #         history_json = await self.redis_client.get(history_key)
    #         if history_json:
    #             try:
    #                 history = json.loads(history_json)
    #                 if isinstance(history, list):
    #                     print(f"[CONTEXT]: Loaded {len(history)} history entries for session {session_id}")
    #                     await self.redis_client.expire(history_key, SESSION_EXPIRATION_SECONDS)
    #                     return history
    #                 else:
    #                     print(f"[ERROR]: Invalid history format found for session {session_id}. Discarding.")
    #                     await self.redis_client.delete(history_key)
    #                     return []
    #             except json.JSONDecodeError:
    #                 print(f"[ERROR]: Failed to decode history JSON for session {session_id}. Discarding.")
    #                 await self.redis_client.delete(history_key)
    #                 return []
    #         else:
    #             print(f"[CONTEXT]: No history found for session {session_id}. Starting fresh.")
    #             return []
    #     except redis.exceptions.RedisError as e:
    #         print(f"[ERROR]: Redis error loading history for session {session_id}: {e}")
    #         return []
    #
    # async def _save_history(self, session_id: str, history: List[Dict[str, Any]]):
    #     """Saves conversation history to Redis."""
    #     history_key = f"session:{session_id}:history"
    #     try:
    #         history_to_save = json.dumps(history)
    #         await self.redis_client.set(history_key, history_to_save, ex=SESSION_EXPIRATION_SECONDS)
    #         print(f"[CONTEXT]: Saved {len(history)} history entries for session {session_id}")
    #     except TypeError as e:
    #         print(f"[ERROR]: Failed to serialize history for session {session_id}: {e}")
    #     except redis.exceptions.RedisError as e:
    #         print(f"[ERROR]: Redis error saving history for session {session_id}: {e}")
