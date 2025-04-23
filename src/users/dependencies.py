# src/users/dependencies.py

# from fastapi import Depends
# from users.repos import UserRepository, ExperienceRepository, EducationRepository, ProjectRepository, SkillRepository
# from users.service import UserService
#
#
# """
# User Module Dependencies
# """
#
#
# """Repositories"""
# def get_user_repo():
#     return UserRepository()
#
# def get_exp_repo():
#     return ExperienceRepository()
#
# def get_edu_repo():
#     return EducationRepository()
#
# def get_project_repo():
#     return ProjectRepository()
#
# def get_skill_repo():
#     return SkillRepository()
#
# """Services"""
# def get_user_service(
#     user_repo: UserRepository = Depends(get_user_repo),
#     exp_repo: ExperienceRepository = Depends(get_exp_repo),
#     edu_repo: EducationRepository = Depends(get_edu_repo),
#     project_repo: ProjectRepository = Depends(get_project_repo),
#     skill_repo: SkillRepository = Depends(get_skill_repo)
# ):
#     return UserService(
#         user_repo,
#         exp_repo,
#         edu_repo,
#         project_repo,
#         skill_repo
#     )
#
