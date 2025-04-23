# src/database/models.py

from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    pfp_url = Column(String)
    hashed_password = Column(String)
    
    # Relationships
    projects = relationship("Project", back_populates="user")
    educations = relationship("Education", back_populates="user")
    experiences = relationship("Experience", back_populates="user")
    skills = relationship("Skill", back_populates="user")

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'pfp_url': self.pfp_url,
            'projects': [project.to_dict() for project in self.projects],
            'educations': [education.to_dict() for education in self.educations],
            'experiences': [experience.to_dict() for experience in self.experiences],
            'skills': [skill.to_dict() for skill in self.skills]
        }

    def for_llm(self):
        return {
            'user_id': self.user_id,
            'name': f'{self.first_name} {self.last_name}',
            'contact': self.email,
            'projects': [
                {
                    'project_id': proj.project_id,
                    'project_name': proj.project_name,
                    'project_description': proj.project_description
                } for proj in self.projects
            ] if self.projects else [],
            'experiences': [
                exp.job_description() for exp in self.experiences
            ] if self.experiences else [],
            'educations': [edu.education_description() for edu in self.educations],
            'skills': [skill.skill_name for skill in self.skills]
        }

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    project_name = Column(String)
    project_description = Column(String)
    github_url = Column(String)
    project_url = Column(String)
    project_start_date = Column(Date)
    project_end_date = Column(Date)
    
    # Relationship
    user = relationship("User", back_populates="projects")

    def to_dict(self):
        return {
            'project_id': self.project_id,
            'user_id': self.user_id,
            'project_name': self.project_name,
            'project_description': self.project_description,
            'github_url': self.github_url,
            'project_url': self.project_url,
            'project_start_date': self.project_start_date.isoformat() if self.project_start_date else None,
            'project_end_date': self.project_end_date.isoformat() if self.project_end_date else None
        }

class Education(Base):
    __tablename__ = "educations"
    
    education_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    institution_name = Column(String)
    degree_type = Column(String)
    degree_name = Column(String)
    enrollment_date = Column(Date)
    graduation_date = Column(Date)
    
    # Relationship
    user = relationship("User", back_populates="educations")

    def to_dict(self):
        return {
            'education_id': self.education_id,
            'user_id': self.user_id,
            'institution_name': self.institution_name,
            'degree_type': self.degree_type,
            'degree_name': self.degree_name,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'graduation_date': self.graduation_date.isoformat() if self.graduation_date else None
        }

    def format_edu_period(self):
        if not self.enrollment_date:
            return ""
        
        end = True if self.graduation_date else False
        if not end:
            return f""
        return f"From {self.enrollment_date} to {self.graduation_date}"

    def education_description(self):
        return f"{self.degree_type} in {self.degree_name} at {self.institution_name}. {self.format_edu_period()}"

class Experience(Base):
    __tablename__ = "experiences"
    
    experience_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    company_name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    experience_description = Column(String)
    job_title = Column(String)
    location = Column(String)
    
    # Relationship
    user = relationship("User", back_populates="experiences")

    def to_dict(self):
        return {
            'experience_id': self.experience_id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'experience_description': self.experience_description,
            'job_title': self.job_title,
            'location': self.location
        }    

    def format_job_period(self):
        if not self.start_date:
            return ""
        
        end = self.end_date if self.end_date else "Present"
        return f"From {self.start_date} to {end}"

    def job_description(self):
        period = self.format_job_period()
        base = f"{self.job_title} at {self.company_name}"
        return f"{base}. {period}. Description: {self.experience_description}" if period else base

class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    skill_name = Column(String)
    
    # Relationship
    user = relationship("User", back_populates="skills")

    def to_dict(self):
        return {
            'skill_id': self.skill_id,
            'user_id': self.user_id,
            'skill_name': self.skill_name
        }
