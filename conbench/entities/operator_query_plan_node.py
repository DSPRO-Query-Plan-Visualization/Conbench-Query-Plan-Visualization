import flask as f
import sqlalchemy as s
from docopt import Optional
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped

import logging
from ..entities._entity import Base, EntityMixin, EntitySerializer, NotNull, genprimkey, Nullable

log = logging.getLogger(__name__)

# composite key id + query_plan_id
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

class _OperatorNodeSerializer(EntitySerializer):
    def _dump(self, operator_node):
        result = {
                "id"        : operator_node.id,
                "label"     : operator_node.label,
                "inputs"    : operator_node.inputs  or [],
                "outputs"   : operator_node.outputs or [],
            }
        return result

class OperatorNodeSerializer:
    one     = _OperatorNodeSerializer()
    many    = _OperatorNodeSerializer(many=True)