import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

from typing import List

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.logical_query_plan_node import LogicalQueryPlanNode, LogicalQueryPlanNodeSerializer

log = logging.getLogger(__name__) #change to "test"

class LogicalQueryPlan(Base, EntityMixin["LogicalQueryPlan"]):
    __tablename__ = "logical_query_plan"
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))
    logical_query_plan_node: Mapped[List[LogicalQueryPlanNode]] = relationship("LogicalQueryPlanNode", lazy="selectin", cascade="all, delete-orphan")

class _LogicalQueryPlanSerializer(EntitySerializer):
    def _dump(self, logical_query_plan):
        result = [ LogicalQueryPlanNodeSerializer().many._dump(logical_query_plan_node) for logical_query_plan_node in logical_query_plan.logical_query_plan_node ]
        return result

class LogicalQueryPlanSerializer:
    one = _LogicalQueryPlanSerializer()
    many = _LogicalQueryPlanSerializer(many=True)
