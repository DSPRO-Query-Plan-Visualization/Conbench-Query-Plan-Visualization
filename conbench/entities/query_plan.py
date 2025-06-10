import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.query_plan_node import QueryPlanNode

log = logging.getLogger(__name__) #change to "test"

class QueryPlan(Base, EntityMixin["QueryPlan"]):
    __tablename__ = "query_plan"
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))

    # 'type' by itself seems to be a restricted name in postgresql
    # for now logical or physical, maybe more variations in the future
    query_plan_type: Mapped[str] = Nullable(s.Text)
    query_plan_node: Mapped[QueryPlanNode] = relationship("QueryPlanNode", lazy="selectin", cascade="all, delete-orphan")



class _QueryPlanSerializer(EntitySerializer):
    def _dump(self, query_plan):
        log.info("sQQQQQQQQQQQQQQQQQQQQQQerializing query_plan \n\n")
        result = {
            "id": query_plan.id,
            "query_plan_type": query_plan.query_plan_type,
        }
        return result


class QueryPlanSerializer:
    one = _QueryPlanSerializer()
    many = _QueryPlanSerializer(many=True)
