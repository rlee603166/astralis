# src/search/stream.py
import requests
import json
import sys

# --- Configuration ---
BASE_URL = "http://localhost:8000/search/"
DEFAULT_QUERY = "software engineers at google"
query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY

# --- Session Handling ---
# Set SESSION_ID = "your-session-id" to continue a conversation
SESSION_ID = None

# --- Request ---
headers = {"Accept": "text/event-stream"}
if SESSION_ID: headers["X-Session-ID"] = SESSION_ID
payload = {'query': query}

print(f"--- Sending Request ---")
print(f"URL: {BASE_URL}")
print(f"Query: {payload['query']}")
if SESSION_ID: print(f"Session ID: {SESSION_ID}")
print(f"-----------------------\n")

try:
    with requests.post(BASE_URL, json=payload, headers=headers, stream=True) as r:
        r.raise_for_status()
        returned_session_id = r.headers.get("X-Session-ID")
        if returned_session_id:
            print(f"*** Received Session ID: {returned_session_id} ***\n"
                  f"Use this ID in the SESSION_ID variable above for the next request.\n")

        print("--- Streaming Response ---")
        clarification_needed = False
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    try:
                        json_data = decoded_line[len('data:'):].strip()
                        if json_data:
                            data = json.loads(json_data)
                            event_type = data.get('type', 'N/A')
                            message = data.get('message', '')

                            print(f"Type: {event_type}")

                            if event_type == 'users' and isinstance(message, list):
                                print(f"Users ({len(message)}):")
                                for user in message[:3]: print(f"  - {user.get('first_name')} {user.get('last_name')} ({user.get('user_id')})")
                                if len(message) > 3: print(f"  ... and {len(message) - 3} more.")
                            elif event_type == 'clarification_request':
                                print(f"*** AGENT ASKS: {message} ***")
                                clarification_needed = True
                            elif event_type == 'response':
                                print(f"Message Chunk: {message}")
                            elif event_type == 'thought':
                                print(f"Thought Chunk: {message.strip()}")
                            else:
                                print(f"Message: {message}")

                            print("-" * 10)
                    except json.JSONDecodeError:
                        print(f"Received non-JSON data line: {decoded_line}")
                    except Exception as e:
                        print(f"Error processing line: {decoded_line}, Error: {e}")

        print("\n--- Stream Ended ---")
        if clarification_needed:
            print("\n*** Please provide clarification in your next query using the same Session ID. ***")

except requests.exceptions.RequestException as e:
    print(f"\n--- Request Failed ---")
    print(f"Error: {e}")
    if e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")