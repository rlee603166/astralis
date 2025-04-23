# src/users/schema.py

from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List


# class User(BaseModel):
#     first_name: str
#     last_name: str
#     email: EmailStr
#
# class UserCreate(User):
#     hashed_password: str
#
# class UserUpdate(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None
#     email: Optional[EmailStr] = None
#     hashed_password: Optional[str] = None 
#
# class UserResponse(User):
#     user_id: int
#     created_at: datetime
#
# class Experience(BaseModel):
#     user_id: int
#     start_date: date
#     end_date: date
#     company_name: str
#     experience_description: str
#     job_title: str
#     location: str
#  
# class ExperienceCreate(Experience):
#     pass
#
# class ExperienceUpdate(BaseModel):
#     user_id: Optional[int]
#     start_date: Optional[date]
#     end_date: Optional[date]
#     company_name: Optional[str]
#     experience_description: Optional[str]
#     job_title: Optional[str]
#     location: Optional[str]
#  
#
# class ExperienceResponse(Experience):
#     experience_id: int
#     
#
# # Update the Education and EducationResponse models in schema.py
# class Education(BaseModel):
#     user_id: int
#     institution_name: str  # Changed from school_name to match your DB
#     degree_type: str
#     degree_name: str
#     enrollment_date: str | None = None   
#     graduation_date: str | None = None
#
# class EducationResponse(Education):
#     education_id: int
#
# class EducationCreate(Education):
#     pass
#
# class EducationUpdate(BaseModel):
#     user_id: Optional[int]
#     institution_name: Optional[str]  # Changed from school_name
#     degree_type: Optional[str]
#     degree_name: Optional[str]
#     enrollment_date: Optional[str]
#     graduation_date: Optional[str]  # Fixed typo from graduion_date
#
# class Project(BaseModel):
#     user_id: int
#     project_name: str
#
#
# class ProjectCreate(Project):
#     description: str | None = None
#     github_url: str | None = None
#     project_url: str | None = None
#     project_start_date: date | None = None
#     project_end_date: date | None = None
#
# class ProjectUpdate(BaseModel):
#     user_id: Optional[int]
#     project_name: Optional[str]
#     description: Optional[str]
#     github_url: Optional[str]
#     project_url: Optional[str]
#     project_start_date: Optional[date]
#     project_end_date: Optional[date]
#
# class ProjectResponse(Project):
#     project_id: int
#     description: str | None = None
#     github_url: str | None = None
#     project_url: str | None = None
#     project_start_date: date | None = None
#     project_end_date: date | None = None
#
#
# class Skill(BaseModel):
#     user_id: int
#     skill_name: str
#     proficiency_level: str
#
# class SkillCreate(Skill):
#     pass
#
# class SkillUpdate(BaseModel):
#     user_id: Optional[int]
#     skill_name: Optional[str]
#     proficiency_level: Optional[str]
#
# class SkillResponse(Skill):
#     skill_id: int
#    
# """
# Relational
# """
#
# class ProjectSkill(BaseModel):
#     project_skill_id: int
#     project_id: int
#     skill_id: int
#
# class ExperienceSkill(BaseModel):
#     experience_skill_id: int
#     experience_id: int
#     skill_id: int

class SkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    
    class Config:
        orm_mode = True

class ProjectResponse(BaseModel):
    project_id: str
    project_name: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    project_url: Optional[str] = None
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None
    
    class Config:
        orm_mode = True

class EducationResponse(BaseModel):
    education_id: str
    institution_name: str
    degree_type: Optional[str] = None
    degree_name: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    
    class Config:
        orm_mode = True

class ExperienceResponse(BaseModel):
    experience_id: str
    company_name: str
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    experience_description: Optional[str] = None
    
    class Config:
        orm_mode = True

class UserProfileResponse(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    projects: List[ProjectResponse] = []
    educations: List[EducationResponse] = []
    experiences: List[ExperienceResponse] = []
    skills: List[SkillResponse] = []
    
    class Config:
        orm_mode = True

