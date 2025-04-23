# src/users/repos/user.py

# from fastapi import HTTPException
# from database.client import supabase_client
# from .base import BaseRepository
# from ..schema import UserCreate, UserUpdate
#
#
# class UserRepository(BaseRepository[dict, UserCreate, UserUpdate]):
#     def __init__(self):
#         super().__init__(supabase_client, "users", pk="user_id")
#
#
#     def get_by_email(self, email: str):
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .eq("email", email)
#                     .execute()
#             )
#
#             if not response.data:
#                 return None
#             return response.data[0]
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
#         
#         
#     def get_by_first_name(self, first_name: str):
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .eq("first_name", first_name)
#                     .execute()
#             )
#
#             if not response.data:
#                 return None
#             return response.data[0]
#         except Exception as e:
#             if "JSON object requested" in str(e):
#                 return None
#             raise HTTPException(status_code=400, detail=str(e))
#
#
#     def get_by_last_name(self, last_name: str):
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .eq("last_name", last_name)
#                     .execute()
#             )
#
#             if not response.data:
#                 return None
#             return response.data[0]
#         except Exception as e:
#             if "JSON object requested" in str(e):
#                 return None
#             raise HTTPException(status_code=400, detail=str(e))
#                
