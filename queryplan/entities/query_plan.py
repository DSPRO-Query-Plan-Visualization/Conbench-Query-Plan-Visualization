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

# =================================== Logical Plan ===================================:

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

# ================================== Pipeline Plan ===================================:

class OperatorNode(Base, EntityMixin["OperatorNode"]):
    __tablename__ = "operator_node"
    # foreign and primary key:
    operator_node_id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    operator_plan_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("operator_plan.id"))
    # content:
    id: Mapped[int] = NotNull(s.Numeric)
    label: Mapped[str] = Nullable(s.Text)
    inputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    outputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )

class OperatorPlan(Base, EntityMixin["OperatorPlan"]):
    __tablename__ = "operator_plan"
    # plan id and connections
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    pipeline_node_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("pipeline_node.id"))
    operator_nodes: Mapped[List[OperatorNode]] = relationship("OperatorNode", lazy="selectin", cascade="all, delete-orphan")
    # possible metadata:

class PipelineNode(Base, EntityMixin["PipelineNode"]):
    __tablename__ = "pipeline_node"
    # id and connection:
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    pipeline_plan_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("pipeline_plan.id"))

    # content:
    pipeline_id: Mapped[int] = NotNull(s.Numeric)
    incoming_tuples: Mapped[int] = NotNull(s.Numeric)
    predecessors: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    successors: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    operators: Mapped[OperatorPlan] = relationship("OperatorPlan", lazy="joined", cascade="all, delete-orphan")

class PipelinePlan(Base, EntityMixin["PipelinePlan"]):
    __tablename__ = "pipeline_plan"
    # plan id and connections
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))
    pipeline_node: Mapped[List[PipelineNode]] = relationship("PipelineNode", lazy="selectin", cascade="all, delete-orphan")
    # possible metadata:


"""
Event based creation of the benchmark_result dependant query plans.
'benchmark_request_json' is stored before hand by the
'stash_benchmark_data()' function in ..api/results, which gets 
triggered by a POST request to '/api/benchmarks/'.
"""

@event.listens_for(BenchmarkResult, "after_insert")
def create_logical_query_plan(mapper, connection, target):
    try:
        data = g.get("benchmark_request_json", {})
        benchmark_id = target.id

        # =================== Logical Plan ===================
        serialized_logical = data.get("serializedLogicalPlan")
        if serialized_logical:
            logical_plan_id = str(uuid4())
            connection.execute(
                LogicalQueryPlan.__table__.insert().values(
                    id=logical_plan_id,
                    benchmark_id=benchmark_id
                )
            )
            for node in serialized_logical:
                connection.execute(
                    LogicalQueryPlanNode.__table__.insert().values(
                        logical_query_plan_id=logical_plan_id,
                        id=node["id"],
                        label=node.get("label"),
                        node_type=node.get("nodeType"),
                        inputs=node.get("inputs", []),
                        outputs=node.get("outputs", [])
                    )
                )

        # ================== Pipeline Plan ===================
        serialized_pipeline = data.get("serializedPipelinePlan")
        if serialized_pipeline:
            pipeline_plan_id = str(uuid4())
            connection.execute(
                PipelinePlan.__table__.insert().values(
                    id=pipeline_plan_id,
                    benchmark_id=benchmark_id
                )
            )

            for pipeline in serialized_pipeline:
                pipeline_node_id = str(uuid4())
                connection.execute(
                    PipelineNode.__table__.insert().values(
                        id=pipeline_node_id,
                        pipeline_plan_id=pipeline_plan_id,
                        pipeline_id=pipeline["pipelineId"],
                        incoming_tuples=pipeline["incomingTuples"],
                        predecessors=pipeline.get("predecessors", []),
                        successors=pipeline.get("successors", [])
                    )
                )

                operator_plan_id = str(uuid4())
                connection.execute(
                    OperatorPlan.__table__.insert().values(
                        id=operator_plan_id,
                        pipeline_node_id=pipeline_node_id
                    )
                )

                for operator in pipeline.get("operators", []):
                    connection.execute(
                        OperatorNode.__table__.insert().values(
                            operator_node_id=str(uuid4()),
                            operator_plan_id=operator_plan_id,
                            id=operator["id"],
                            label=operator.get("label"),
                            inputs=operator.get("inputs", []),
                            outputs=operator.get("outputs", [])
                        )
                    )
    except Exception as e:
        logging.exception("Failed to create query plan: %s", e)


# ============================ Serializer ============================:
class _LogicalQueryPlanSerializer(EntitySerializer):
    def _dump(self, plan):
        result = []
        for node in plan.logical_query_plan_node:
            result.append({
                "id"        : node.id,
                "label"     : node.label,
                "node_type" : node.node_type,
                "inputs"    : [int(x) for x in node.inputs  or []],
                "outputs"   : [int(x) for x in node.outputs or []],
            })
        return result

class LogicalQueryPlanSerializer:
    one = _LogicalQueryPlanSerializer()
    many = _LogicalQueryPlanSerializer(many=True)

class _PipelinePlanSerializer(EntitySerializer):
    def _dump(self, plan):
        result = []
        for pnode in plan.pipeline_node:
            result.append({
            "pipeline_id"       : int(pnode.pipeline_id),
            "incoming_tuples"   : int(pnode.incoming_tuples),
            "predecessors"      : [int(x) for x in pnode.predecessors] if pnode.predecessors else [],
            "successors"        : [int(x) for x in pnode.successors]   if pnode.successors   else [],
            "operators"         : [{
                "id"        : int(onode.id),
                "label"     : onode.label,
                "inputs"    : [int(x) for x in onode.inputs]  if onode.inputs  else [],
                "outputs"   : [int(x) for x in onode.outputs] if onode.outputs else [],
            } for onode in pnode.operators.operator_nodes ]
        })
        return result

class PipelinePlanSerializer:
    one = _PipelinePlanSerializer()
    many = _PipelinePlanSerializer(many=True) # gets jsonnified