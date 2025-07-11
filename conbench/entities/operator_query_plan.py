import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

from typing import List

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable
from ..entities.operator_query_plan_node import OperatorNode, OperatorNodeSerializer

log = logging.getLogger(__name__) #change to "test"

class OperatorPlan(Base, EntityMixin["OperatorPlan"]):
    __tablename__ = "operator_plan"
    # plan id and connections
    id: Mapped[str] = NotNull(s.String(50), primary_key=True, default=genprimkey)
    pipeline_node_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("pipeline_node.id"))
    operator_nodes: Mapped[List[OperatorNode]] = relationship("OperatorNode", lazy="selectin", cascade="all, delete-orphan")
    # possible metadata:


class _OperatorPlanSerializer(EntitySerializer):
    def _dump(self, operator_plan):
        log.info("\n\n[3]")
        result = [OperatorNodeSerializer().many._dump(operator_query_plan_node) for operator_query_plan_node in operator_plan.operator_nodes]
        return result


class OperatorPlanSerializer:
    one = _OperatorPlanSerializer()
    many = _OperatorPlanSerializer(many=True)
