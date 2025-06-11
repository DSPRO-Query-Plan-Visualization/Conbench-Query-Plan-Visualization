import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

from typing import List

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.query_plan_node import QueryPlanNode, QueryPlanNodeSerializer

log = logging.getLogger(__name__) #change to "test"

class QueryPlan(Base, EntityMixin["QueryPlan"]):
    __tablename__ = "query_plan"
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))

    # 'type' by itself seems to be a restricted name in postgresql
    # for now logical or physical, maybe more variations in the future
    query_plan_type: Mapped[str] = Nullable(s.Text)
    query_plan_node: Mapped[List[QueryPlanNode]] = relationship("QueryPlanNode", lazy="selectin", cascade="all, delete-orphan")



class _QueryPlanSerializer(EntitySerializer):
    def _dump(self, query_plan):
        result = [query_plan.query_plan_type, [ QueryPlanNodeSerializer().many._dump(query_plan_node) for query_plan_node in query_plan.query_plan_node ] ]
        return result


class QueryPlanSerializer:
    one = _QueryPlanSerializer()
    many = _QueryPlanSerializer(many=True)
