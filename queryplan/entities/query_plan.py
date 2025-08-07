from uuid import uuid4
from flask import g
from conbench.entities.benchmark_result import BenchmarkResult
from sqlalchemy.dialects import postgresql
import sqlalchemy as s
from typing import List
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy import event
from conbench.entities._entity import (
    Base,
    EntityMixin,
    EntitySerializer,
    NotNull,
    Nullable,
    genprimkey,
)

"""
This file holds all table definitions and create functions for the logical and pipeline query plans.
The last migration  "e15e8b226491_benchmark_id_ondelete_cascade_query_" fixed the ondelete cascade
issues, so deleting a benchmark result should delete all dependant query plans without issue.
The reason for creating the tables like this is to keep things separate,
splitting the logic and thus failure points as much as possible.

If the migration can't be applied or there are still issues that persist, updating the
sort_by_name[] list in get_tables_in_cleanup_order() in db.py should fix most issues.
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
Raw function for inserting query plans into the db.
Checked and called by create_queryplan_after_benchmark in queryplan/api/results.py.
"""
def _create_queryplan_in_db(userres,benchmark_id):
    try:
        # if present, creates the logical nodes and connects them to the logical plan -
        # which points to the current benchmark result
        if "serializedLogicalPlan" in userres:
            logical_query_plan = LogicalQueryPlan.create({"benchmark_id": benchmark_id})
            for node in userres["serializedLogicalPlan"]:
                LogicalQueryPlanNode.create({
                    "logical_query_plan_id": logical_query_plan.id,
                    "id": node["id"],
                    "label": node["label"],
                    "node_type": node["nodeType"],
                    "inputs": node["inputs"],
                    "outputs": node["outputs"],
                })

        # if present, creates the pipeline nodes and connects them to the pipeline plan -
        # which points to the current benchmark result
        if "serializedPipelinePlan" in userres:
            pipeline_plan = PipelinePlan.create({"benchmark_id": benchmark_id})
            for pipeline in userres["serializedPipelinePlan"]:
                pipeline_node = PipelineNode.create({
                    "pipeline_plan_id": pipeline_plan.id,
                    "incoming_tuples": pipeline["incomingTuples"],
                    "pipeline_id": pipeline["pipelineId"],
                    "predecessors": pipeline["predecessors"],
                    "successors": pipeline["successors"],
                })
                # each pipeline node holds an operator plan which in turn spans multiple operator nodes
                operator_plan = OperatorPlan.create({"pipeline_node_id": pipeline_node.id, })
                for operator in pipeline["operators"]:
                    OperatorNode.create({
                        "operator_plan_id": operator_plan.id,
                        "id": operator["id"],
                        "label": operator["label"],
                        "inputs": operator["inputs"],
                        "outputs": operator["outputs"],
                    })
    except Exception as e:
        log.warning(f"Query plan creation failed: {e}")

# ============================ Serializer ============================:
# Logical serializer
class _LogicalQueryPlanSerializer(EntitySerializer):
    def _dump(self, plan):
        result = []
        for node in plan.logical_query_plan_node:
            result.append({
                "id"        : int(node.id),
                "label"     : node.label,
                "node_type" : node.node_type,
                "inputs"    : [int(x) for x in node.inputs]  if node.inputs  else [],
                "outputs"   : [int(x) for x in node.outputs] if node.outputs else [],
            })
        return result

class LogicalQueryPlanSerializer:
    one = _LogicalQueryPlanSerializer()
    many = _LogicalQueryPlanSerializer(many=True)

# Pipeline serializer
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