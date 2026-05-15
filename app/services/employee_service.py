from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.employee import Employee
from app.models.department import Department
from app.schemas import EmployeeCreate
from fastapi import HTTPException


async def create_employee(session: AsyncSession, department_id: int, data: EmployeeCreate) -> Employee:
    dept = await session.get(Department, department_id)

    if dept is None:
        raise HTTPException(status_code=404, detail=f"Департамент {department_id} не найден")

    emp = Employee(department_id=department_id, full_name=data.full_name, position=data.position, hired_at=data.hired_at)
    session.add(emp)

    await session.commit()
    await session.refresh(emp)

    logger.info("Создан employee id=%d в department id=%d", emp.id, department_id)

    return emp