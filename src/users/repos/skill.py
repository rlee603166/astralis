# src/users/repos/skill.py

# from fastapi import HTTPException
# from database.client import supabase_client
# from .base import BaseRepository
# from ..schema import SkillCreate, SkillUpdate
#
#
# class SkillRepository(BaseRepository[dict, SkillCreate, SkillUpdate]):
#     def __init__(self):
#         super().__init__(supabase_client, "skills", pk="skill_id")
#
#     def get_by_user(self, user_id: int):
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .eq("user_id", user_id)
#                     .execute()
#             )
#             if not response.data:
#                 return None
#             return response.data
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
