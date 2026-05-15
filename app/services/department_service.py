from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.department import Department
from app.models.employee import Employee
from app.schemas import DepartmentCreate, DepartmentDetail, DepartmentUpdate
from fastapi import HTTPException

async def _get_or_404(session: AsyncSession, dept_id: int) -> Department:
    obj = await session.get(Department, dept_id)

    if obj is None:        
        raise HTTPException(status_code=404, detail=f"Департамент {dept_id} не найден")
    
    return obj


async def _collect_subtree_ids(session: AsyncSession, root_id: int) -> set[int]:
    """BFS по детям для сбора всех ID потомков (включая корневой)."""
    visited: set[int] = set()
    queue = [root_id]

    while queue:
        current = queue.pop()

        if current in visited:
            continue

        visited.add(current)
        result = await session.execute(select(Department.id).where(Department.parent_id == current))
        queue.extend(result.scalars().all())
    
    return visited


async def _would_create_cycle(session: AsyncSession, dept_id: int, new_parent_id: int | None) -> bool:
    """ Возвращает True, если установка dept.parent_id = new_parent_id создаёт цикл."""
    if new_parent_id is None:
        return False
    
    if new_parent_id == dept_id:
        return True
    
    subtree = await _collect_subtree_ids(session, dept_id)
    
    return new_parent_id in subtree


async def _build_detail(session: AsyncSession, dept: Department, depth: int, include_employees: bool, current_depth: int = 0) -> DepartmentDetail:
    """Рекурсивно строит ответ DepartmentDetail."""
    employees = []

    if include_employees:
        result = await session.execute(select(Employee).where(Employee.department_id == dept.id).order_by(Employee.created_at))
        employees = result.scalars().all()
    
    children_detail: list[DepartmentDetail] = []
    
    if current_depth < depth:
        result = await session.execute(select(Department).where(Department.parent_id == dept.id))
        child_depts = result.scalars().all()

        for child in child_depts:
            children_detail.append(await _build_detail(session, child, depth, include_employees, current_depth + 1))
    
    return DepartmentDetail(id=dept.id, name=dept.name, parent_id=dept.parent_id, created_at=dept.created_at, employees=[e for e in employees], children=children_detail)


async def create_department(session: AsyncSession, data: DepartmentCreate) -> Department:
    if data.parent_id is not None:
        await _get_or_404(session, data.parent_id)

    dept = Department(name=data.name, parent_id=data.parent_id)
    session.add(dept)

    try:
        await session.commit()
        await session.refresh(dept)
    except IntegrityError:
        await session.rollback()

        raise HTTPException(status_code=409, detail="Департамент с таким названием уже существует в рамках одного родителя.")
    
    logger.info("Создан департамент id=%d name=%r", dept.id, dept.name)
    
    return dept


async def get_department_detail(session: AsyncSession, dept_id: int, depth: int, include_employees: bool) -> DepartmentDetail:
    dept = await _get_or_404(session, dept_id)

    return await _build_detail(session, dept, depth, include_employees)


async def update_department(session: AsyncSession, dept_id: int, data: DepartmentUpdate) -> Department:
    dept = await _get_or_404(session, dept_id)
    update_data = data.model_dump(exclude_unset=True)

    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if await _would_create_cycle(session, dept_id, new_parent_id):
            raise HTTPException(status_code=409, detail="Невозможно установить parent_id, так как это создаст цикл в иерархии.")
        
        if new_parent_id is not None:
            await _get_or_404(session, new_parent_id)
        
        dept.parent_id = new_parent_id

    if "name" in update_data:
        dept.name = update_data["name"]

    try:
        await session.commit()
        await session.refresh(dept)
    except IntegrityError:
        await session.rollback()

        raise HTTPException(status_code=409, detail="Департамент с таким названием уже существует в рамках одного родителя.")
    
    logger.info("Updated department id=%d", dept.id)
    
    return dept


async def delete_department(session: AsyncSession, dept_id: int, mode: str, reassign_to_department_id: int | None) -> None:
    dept = await _get_or_404(session, dept_id)

    if mode == "cascade":
        await session.delete(dept)
        await session.commit()
        
        logger.info("Cascade-deleted department id=%d", dept_id)
    elif mode == "reassign":
        if reassign_to_department_id is None:
            raise HTTPException(status_code=422, detail="reassign_to_department_id нужен если mode=reassign")
        
        target = await _get_or_404(session, reassign_to_department_id)
        subtree_ids = await _collect_subtree_ids(session, dept_id)

        if reassign_to_department_id in subtree_ids:
            raise HTTPException(status_code=409, detail="Невозможно переназначить сотрудников в департамент, который является частью удаляемого поддерева.")
        
        result = await session.execute(select(Employee).where(Employee.department_id.in_(subtree_ids)))
        employees = result.scalars().all()

        for emp in employees:
            emp.department_id = target.id

        result = await session.execute(select(Department).where(Department.parent_id == dept_id))
        children = result.scalars().all()

        for child in children:
            child.parent_id = dept.parent_id

        await session.flush()
        await session.delete(dept)
        await session.commit()
        
        logger.info("Reassign-deleted department id=%d; %d employees moved to dept id=%d", dept_id, len(employees), reassign_to_department_id)

    else:
        raise HTTPException(status_code=422, detail="mode must be 'cascade' or 'reassign'")