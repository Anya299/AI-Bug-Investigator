from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Project
from schemas import ProjectCreate, ProjectResponse


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    new_project = Project(
        name=project.name,
        owner_id=1
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db)
):
    return db.query(Project).all()