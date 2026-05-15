from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_id", "name", name="uq_department_parent_name"),
    )

    op.create_index("ix_departments_id", "departments", ["id"], unique=False)
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"], unique=False)

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("position", sa.String(length=200), nullable=False),
        sa.Column("hired_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_employees_id", "employees", ["id"], unique=False)
    op.create_index("ix_employees_department_id", "employees", ["department_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_index("ix_employees_id", table_name="employees")
    op.drop_table("employees")

    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_index("ix_departments_id", table_name="departments")
    op.drop_table("departments")