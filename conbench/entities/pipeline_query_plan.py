import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

from typing import List

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.pipeline_query_plan_node import PipelineNode, PipelineNodeSerializer

log = logging.getLogger(__name__) #change to "test"

class PipelinePlan(Base, EntityMixin["PipelinePlan"]):
    __tablename__ = "pipeline_plan"
    # plan id and connections
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))
    pipeline_node: Mapped[List[PipelineNode]] = relationship("PipelineNode", lazy="selectin", cascade="all, delete-orphan")
    # possible metadata:


class _PipelinePlanSerializer(EntitySerializer):
    def _dump(self, pipeline_plan):
        result = [ PipelineNodeSerializer().many._dump(pipeline_node) for pipeline_node in pipeline_plan.pipeline_node ]
        return result


class PipelinePlanSerializer:
    one = _PipelinePlanSerializer()
    many = _PipelinePlanSerializer(many=True)
