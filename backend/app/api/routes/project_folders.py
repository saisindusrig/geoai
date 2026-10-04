from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.models import Project, ProjectFolder
from app.db.session import get_db

router = APIRouter(prefix="/api/project-folders", tags=["project-folders"])


def _normalise_name(name: str) -> str:
    value = " ".join(name.split())
    if not value:
        raise ValueError("Folder name cannot be empty")
    return value


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str = Field(default="sage", min_length=1, max_length=20)

    _clean_name = field_validator("name")(_normalise_name)


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, min_length=1, max_length=20)

    _clean_name = field_validator("name")(_normalise_name)


class FolderOut(BaseModel):
    id: int
    name: str
    color: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def _get_owned_folder(folder_id: int, db: Session, user_id: int) -> ProjectFolder:
    folder = db.get(ProjectFolder, folder_id)
    if folder is None or folder.user_id != user_id:
        raise HTTPException(404, "Folder not found")
    return folder


@router.get("", response_model=list[FolderOut])
def list_folders(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return (
        db.query(ProjectFolder)
        .filter(ProjectFolder.user_id == user_id)
        .order_by(ProjectFolder.name.asc())
        .all()
    )


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    folder = ProjectFolder(user_id=user_id, **payload.model_dump())
    db.add(folder)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You already have a folder with this name") from None
    db.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: int,
    payload: FolderUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    folder = _get_owned_folder(folder_id, db, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(folder, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You already have a folder with this name") from None
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    folder = _get_owned_folder(folder_id, db, user_id)
    # Keep work accessible: deleting a folder deliberately makes its projects Unfiled.
    (
        db.query(Project)
        .filter(Project.user_id == user_id, Project.folder_id == folder.id)
        .update({Project.folder_id: None}, synchronize_session=False)
    )
    db.delete(folder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
