from typing import Literal
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.schemas import DepartmentCreate, DepartmentDetail, DepartmentRead, DepartmentUpdate, EmployeeCreate, EmployeeRead
from app.services import create_department, create_employee, delete_department, get_department_detail, update_department

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentRead, status_code=201)
async def api_create_department(body: DepartmentCreate, session: AsyncSession = Depends(get_session)) -> DepartmentRead:
    dept = await create_department(session, body)

    return DepartmentRead.model_validate(dept)

@router.post("/{dept_id}/employees/", response_model=EmployeeRead, status_code=201)
async def api_create_employee(dept_id: int, body: EmployeeCreate, session: AsyncSession = Depends(get_session)) -> EmployeeRead:
    emp = await create_employee(session, dept_id, body)

    return EmployeeRead.model_validate(emp)

@router.get("/{dept_id}", response_model=DepartmentDetail)
async def api_get_department(dept_id: int, depth: int = Query(default=1, ge=1, le=5), include_employees: bool = Query(default=True), session: AsyncSession = Depends(get_session)) -> DepartmentDetail:
    return await get_department_detail(session, dept_id, depth, include_employees)

@router.patch("/{dept_id}", response_model=DepartmentRead)
async def api_update_department(dept_id: int, body: DepartmentUpdate,session: AsyncSession = Depends(get_session)) -> DepartmentRead:
    dept = await update_department(session, dept_id, body)

    return DepartmentRead.model_validate(dept)

@router.delete("/{dept_id}", status_code=204)
async def api_delete_department(dept_id: int, mode: Literal["cascade", "reassign"] = Query(...), reassign_to_department_id: int | None = Query(default=None), session: AsyncSession = Depends(get_session)) -> Response:
    await delete_department(session, dept_id, mode, reassign_to_department_id)

    return Response(status_code=204)