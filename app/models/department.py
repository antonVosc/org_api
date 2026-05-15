from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base



class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_department_parent_name"), {})

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent: Mapped["Department | None"] = relationship("Department", back_populates="children", remote_side="Department.id", foreign_keys="[Department.parent_id]")
    children: Mapped[list["Department"]] = relationship("Department", back_populates="parent", foreign_keys="[Department.parent_id]", cascade="all, delete-orphan", passive_deletes=True)
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="department", cascade="all, delete-orphan", passive_deletes=True)