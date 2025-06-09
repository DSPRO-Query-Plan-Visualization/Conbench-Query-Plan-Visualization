import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable

log = logging.getLogger(__name__)

class QueryPlan(Base, EntityMixin["QueryPlan"]):
    __tablename__ = "query_plan"
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey) # actually has to be generated no ?
    benchmark_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("benchmark_result.id"))
    label: Mapped[str] = Nullable(s.Text)
    bla: Mapped[str] = Nullable(s.Text)
    inputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    outputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )


class _QueryPlanSerializer(EntitySerializer):
    def _dump(self, query_plan):
        log.info("sQQQQQQQQQQQQQQQQQQQQQQerializing query_plan \n\n")
        result = {
            "id": query_plan.id,
            "label": query_plan.label,
        }
        return result


class QueryPlanSerializer:
    one = _QueryPlanSerializer()
    many = _QueryPlanSerializer(many=True)
