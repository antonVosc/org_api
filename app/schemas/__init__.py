from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator



class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: date | None = None

    @field_validator("full_name", "position", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str):
        if isinstance(v, str):
            v = v.strip()
        
        return v


class EmployeeRead(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str):
        if isinstance(v, str):
            v = v.strip()
        
        return v


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            v = v.strip()
        
        return v


class DepartmentRead(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentDetail(DepartmentRead):
    employees: list[EmployeeRead] = []
    children: list[DepartmentDetail] = []

    model_config = {"from_attributes": True}


DepartmentDetail.model_rebuild()


class DeleteStatus(BaseModel):
    detail: str