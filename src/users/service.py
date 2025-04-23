# src/users/service.py

# from typing import List
# from fastapi.concurrency import run_in_threadpool
#
# from users.schema import ExperienceResponse, UserResponse, EducationResponse, ProjectResponse, SkillResponse
# from users.repos import UserRepository, ExperienceRepository, EducationRepository, ProjectRepository, SkillRepository
#
#
# class UserService:
#     def __init__(
#         self,
#         user_repo: UserRepository, 
#         exp_repo: ExperienceRepository,
#         edu_repo: EducationRepository,
#         project_repo: ProjectRepository,
#         skill_repo: SkillRepository
#     ) -> None:
#         self.user_repo = user_repo
#         self.exp_repo = exp_repo
#         self.edu_repo = edu_repo
#         self.project_repo = project_repo
#         self.skill_repo = skill_repo
#
#     async def get_user(self, user_id: int) -> List[UserResponse]:
#         return await run_in_threadpool(self.user_repo.get, user_id)
#
#     async def get_user_experiences(self, user_id: int) -> List[ExperienceResponse]:
#         return await run_in_threadpool(self.exp_repo.get_by_user, user_id)
#
#     async def get_user_education(self, user_id: int) -> List[EducationResponse]:
#         return await run_in_threadpool(self.edu_repo.get_by_user, user_id)
#
#     async def get_user_projects(self, user_id: int) -> List[ProjectResponse]:
#         return await run_in_threadpool(self.project_repo.get_by_user, user_id)
#
#     async def get_user_skills(self, user_id: int) -> List[SkillResponse]:
#         return await run_in_threadpool(self.skill_repo.get_by_user, user_id)
