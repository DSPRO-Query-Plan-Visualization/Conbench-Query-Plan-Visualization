import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.operator_query_plan import OperatorPlan, OperatorPlanSerializer


log = logging.getLogger(__name__)

# composite key id + query_plan_id
class PipelineNode(Base, EntityMixin["PipelineNode"]):
    __tablename__ = "pipeline_node"
    # id and connection:
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    pipeline_plan_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("pipeline_plan.id"))

    # content:
    pipeline_id: Mapped[int] = NotNull(s.Numeric)
    predecessors: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    successors: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    # TODO: relationship, default [] ? optional ?
    operators: Mapped[OperatorPlan] = relationship("OperatorPlan", lazy="joined") # TODO: cascading needed on delete ?

class _PipelineNodeSerializer(EntitySerializer):
    def _dump(self, pipeline_node):
        log.info("\n\n[1]")
        log.info(pipeline_node.operators)
        result = {
                "pipeline_id": pipeline_node.pipeline_id,
                "predecessors": pipeline_node.predecessors or [],
                "successors": pipeline_node.successors or [],
                "operators": OperatorPlanSerializer().many._dump(pipeline_node.operators),
            }
        return result

class PipelineNodeSerializer:
    one = _PipelineNodeSerializer()
    many = _PipelineNodeSerializer(many=True)