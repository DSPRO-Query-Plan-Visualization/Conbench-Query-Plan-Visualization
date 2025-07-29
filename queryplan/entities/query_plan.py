from uuid import uuid4
from flask import g
from conbench.entities.benchmark_result import BenchmarkResult
from sqlalchemy.dialects import postgresql
import sqlalchemy as s
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import event
from conbench.entities._entity import (
    Base,
    EntityMixin,
    EntitySerializer,
    NotNull,
    Nullable,
    genprimkey,
    to_float,
)

"""
This file holds all table definitions and create functions for the logical and pipeline query plans.
The last migration  "e15e8b226491_benchmark_id_ondelete_cascade_query_" fixed the ondelete cascade
issues, so deleting a benchmark result should delete all dependant query plans without issue.
The reason for creating the tables like this is to keep things separate,
splitting the logic and thus failure points as much as possible.
"""

import logging
log = logging.getLogger(__name__)
log.info("Query Plan start")

class LogicalQueryPlanNode(Base, EntityMixin["LogicalQueryPlanNode"]):
    __tablename__ = "logical_query_plan_node"
    logical_query_plan_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("logical_query_plan.id"), primary_key=True)
    id: Mapped[int] = NotNull(s.Numeric, primary_key=True)
    label: Mapped[str] = Nullable(s.Text)
    node_type: Mapped[str] = Nullable(s.Text)
    inputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    outputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )

class LogicalQueryPlan(Base, EntityMixin["LogicalQueryPlan"]):
    __tablename__ = "logical_query_plan"
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))
    logical_query_plan_node: Mapped[List[LogicalQueryPlanNode]] = relationship("LogicalQueryPlanNode", lazy="selectin", cascade="all, delete-orphan")

"""
Event based creation of the benchmark_result dependant logical plans.
'benchmark_request_json' is stored before hand by the
'stash_benchmark_data()' function in ..api/results, which gets 
triggered by a POST request to '/api/benchmarks/'.
"""
@event.listens_for(BenchmarkResult, "after_insert")
def create_logical_query_plan(mapper, connection, target):
    try:
        data = g.get("benchmark_request_json", {})
        serialized_plan = data.get("serializedLogicalPlan")
        if not serialized_plan:
            return

        logical_plan_id = str(uuid4())
        # Insert the LogicalQueryPlan
        connection.execute(
            LogicalQueryPlan.__table__.insert().values( id = logical_plan_id,
                                                        benchmark_id = target.id )
        )
        # Insert each LogicalQueryPlanNode
        for node in serialized_plan:
            connection.execute(
                LogicalQueryPlanNode.__table__.insert().values(
                    logical_query_plan_id = logical_plan_id,
                    id          =node["id"],
                    label       =node.get("label"),
                    node_type   =node.get("nodeType"),
                    inputs      =node.get("inputs", []),
                    outputs     =node.get("outputs", [])
                )
            )
    except Exception as e:
        logging.exception("Failed to create logical query plan: %s", e)