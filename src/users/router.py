# src/users/router.py

from database.client import get_async_session_factory 
from sqlalchemy.ext.asyncio import AsyncSession
# from users.dependencies import get_user_service
from users.schema import UserProfileResponse
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException
# from users.service import UserService
from sqlalchemy import select
from database.models import User
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def hello():
    return { "msg": "hello from users" }

# @router.get("/{user_id}/profile", response_model=UserResponse)
# async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
#     return await service.get_user(user_id)

# @router.get("/{user_id}/experiences", response_model=List[ExperienceResponse])
# async def get_user_experiences(user_id: int, service: UserService = Depends(get_user_service)):
#     return await service.get_user_experiences(user_id)
#
# @router.get("/{user_id}/education", response_model=List[EducationResponse])
# async def get_user_education(user_id: int, service: UserService = Depends(get_user_service)):
#     return await service.get_user_education(user_id)
#
# @router.get("/{user_id}/projects", response_model=List[ProjectResponse])
# async def get_user_projects(user_id: int, service: UserService = Depends(get_user_service)):
#     return await service.get_user_projects(user_id)
#
# @router.get("/{user_id}/skills", response_model=List[SkillResponse])
# async def get_user_skills(user_id: int, service: UserService = Depends(get_user_service)):
#     return await service.get_user_skills(user_id)

async def get_db():
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        yield session

@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
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
    
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    
    return user
