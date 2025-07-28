"""benchmark_id_ondelete_cascade_query_plans

Revision ID: e15e8b226491
Revises: 99895af5dae2
Create Date: 2025-07-28 19:38:09.273621

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e15e8b226491"
down_revision = "99895af5dae2"
branch_labels = None
depends_on = None


def upgrade():
    # Pipeline first
    op.create_table(
        "pipeline_plan",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("benchmark_id", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "pipeline_node",
        sa.Column("id", sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column("pipeline_plan_id", sa.String(length=50), nullable=False),
        sa.Column("pipeline_id", sa.Numeric(), nullable=False),
        sa.Column("incoming_tuples", sa.Numeric(), nullable=False),
        sa.Column(
            "predecessors",
            postgresql.ARRAY(sa.Numeric()),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "successors",
            postgresql.ARRAY(sa.Numeric()),
            nullable=True,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "operator_plan",
        sa.Column("id", sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column("pipeline_node_id", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "operator_node",
        sa.Column(
            "operator_node_id",
            sa.String(length=50),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("operator_plan_id", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Numeric(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column(
            "inputs", postgresql.ARRAY(sa.Numeric()), nullable=True, server_default="{}"
        ),
        sa.Column(
            "outputs",
            postgresql.ARRAY(sa.Numeric()),
            nullable=True,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("operator_node_id"),
    )

    # Logical next
    op.create_table(
        "logical_query_plan",
        sa.Column("id", sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column("benchmark_id", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "logical_query_plan_node",
        sa.Column(
            "logical_query_plan_id",
            sa.String(length=50),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.Numeric(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("node_type", sa.Text(), nullable=True),
        sa.Column(
            "inputs", postgresql.ARRAY(sa.Numeric()), nullable=True, server_default="{}"
        ),
        sa.Column(
            "outputs",
            postgresql.ARRAY(sa.Numeric()),
            nullable=True,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("logical_query_plan_id", "id"),  # Composite primary key
    )

    # Re-create them with ON DELETE CASCADE
    op.create_foreign_key(
        "pipeline_plan_benchmark_id_fkey",
        "pipeline_plan",
        "benchmark_result",
        ["benchmark_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "logical_query_plan_benchmark_id_fkey",
        "logical_query_plan",
        "benchmark_result",
        ["benchmark_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "logical_query_plan_node_logical_query_plan_id_fkey",
        "logical_query_plan_node",
        "logical_query_plan",
        ["logical_query_plan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "pipeline_node_pipeline_plan_id_fkey",
        "pipeline_node",
        "pipeline_plan",
        ["pipeline_plan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "operator_plan_pipeline_node_id_fkey",
        "operator_plan",
        "pipeline_node",
        ["pipeline_node_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "operator_node_operator_plan_id_fkey",
        "operator_node",
        "operator_plan",
        ["operator_plan_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint(
        "pipeline_plan_benchmark_id_fkey", "pipeline_plan", type_="foreignkey"
    )
    op.drop_constraint(
        "logical_query_plan_benchmark_id_fkey", "logical_query_plan", type_="foreignkey"
    )
    op.drop_constraint(
        "logical_query_plan_node_logical_query_plan_id_fkey",
        "logical_query_plan_node",
        type_="foreignkey",
    )
    op.drop_constraint(
        "pipeline_node_pipeline_plan_id_fkey", "pipeline_node", type_="foreignkey"
    )
    op.drop_constraint(
        "operator_plan_pipeline_node_id_fkey", "operator_plan", type_="foreignkey"
    )
    op.drop_constraint(
        "operator_node_operator_plan_id_fkey", "operator_node", type_="foreignkey"
    )

    op.drop_table("operator_node")
    op.drop_table("operator_plan")
    op.drop_table("pipeline_node")
    op.drop_table("pipeline_plan")

    op.drop_table("logical_query_plan_node")
    op.drop_table("logical_query_plan")

