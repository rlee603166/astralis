# src/users/repos/base.py

# from typing import Generic, TypeVar, List, Optional
# from fastapi import HTTPException
# from database.client import Client 
#
#
# ModelType           = TypeVar("ModelType", bound=dict)
# CreateSchemaType    = TypeVar("CreateSchemaType")
# UpdateSchemaType    = TypeVar("UpdateSchemaType")
#
# class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
#     """
#     Generic Class for CRUD ops
#     """
#     def __init__(self, client: Client, table_name: str, pk: str="id"):
#         self.db = client
#         self.table_name = table_name
#         self.pk = pk
#
#     def create(self, data: CreateSchemaType) -> ModelType:
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .insert(data.model_dump())
#                     .execute()
#             )
#             return response.data[0]
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
#
#     def get(self, id: int) -> Optional[ModelType]:
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .eq(self.pk, id)
#                     .execute()
#             )
#             return response.data[0]
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
#
#     def get_all(self) -> List[ModelType]:
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .select("*")
#                     .execute()
#             )
#             return response.data
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
#
#     def update(self, id: int, schema: UpdateSchemaType) -> ModelType:
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .update(schema.model_dump(exclude_unset=True))
#                     .eq(self.pk, id)
#                     .execute()
#             )
#             if not response.data:
#                 raise HTTPException(status_code=404, detail="Record not found")
#             return response.data[0]
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Database update failed: {str(e)}"
#             ) from e       
#
#     def delete(self, id: int) -> bool:
#         try:
#             response = (
#                 self.db.table(self.table_name)
#                     .delete()
#                     .eq(self.pk, id)
#                     .execute()
#             )
#             return bool(response.data)
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=str(e))
