import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable

log = logging.getLogger(__name__)

# composite key id + query_plan_id
class QueryPlanNode(Base, EntityMixin["QueryPlanNode"]):
    __tablename__ = "query_plan_node"
    query_plan_id: Mapped[str] = NotNull(s.String(50), s.ForeignKey("query_plan.id"), primary_key=True)
    id: Mapped[int] = NotNull(s.Numeric, primary_key=True) # TODO: test if 'primary_key=False' is needed
    label: Mapped[str] = Nullable(s.Text)
    node_type: Mapped[str] = Nullable(s.Text)
    inputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )
    outputs: Mapped[list] = Nullable(
        postgresql.ARRAY(s.Numeric), default=[]
    )

class _QueryPlanNodeSerializer(EntitySerializer):
    def _dump(self, query_plan_node):
        result = {
                "id": query_plan_node.id,
                "label": query_plan_node.label,
                "node_type": query_plan_node.node_type,
                "inputs": query_plan_node.inputs or [],
                "outputs": query_plan_node.outputs or [],
            }
        return result

class QueryPlanNodeSerializer:
    one = _QueryPlanNodeSerializer()
    many = _QueryPlanNodeSerializer(many=True)