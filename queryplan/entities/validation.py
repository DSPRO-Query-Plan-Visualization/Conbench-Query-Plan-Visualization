import marshmallow
import conbench.util
from conbench.entities.benchmark_result import _BenchmarkResultCreateSchema, BenchmarkResultFacadeSchema

"""
This file is used to update the marshmallow schema, so query plans sent to the server get properly validated.
As a reference this is the current structure of the logical query plan
and pipeline query plan JSON (as sent to the server):

"serializedLogicalPlan": [
            {
                "id": INT,
                "inputs": [ INT ],
                "label": STR,
                "nodeType": STR,
                "outputs": [ INT ]
            },
            {
                ...
            },
            ],

"serializedPipelinePlan": [
            {
                "incomingTuples": INT,
                "operators": [
                    {
                        "id": INT,
                        "inputs": [ INT ],
                        "label": STR,
                        "outputs": [ INT ]
                    },
                    {
                        ...
                    },
                ],
                "pipelineId": INT,
                "predecessors": [ INT ],
                "successors": [ INT ]
            },
            {
                ...
            },
            ],

While the operators (in the pipeline query plan) have an array for input and output,
they are expected to have at most one input and output element.
The logical plan, same as the pipeline plan, can have multiple input and output elements
(predecessor and successor for the pipeline plan).
"""

# marshmallow schema for the logical query plan
class LogicalQueryPlanNodeSchema(marshmallow.Schema):
    id          = marshmallow.fields.Integer()
    label       = marshmallow.fields.String()
    nodeType    = marshmallow.fields.String()
    inputs      = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                           required=False)
    outputs     = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                           required=False)

# marshmallow schema for the operator nodes which are nested in the pipeline nodes
class OperatorQueryPlanNodeSchema(marshmallow.Schema):
    id          = marshmallow.fields.Integer()
    label       = marshmallow.fields.String()
    inputs      = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                           required=False)
    outputs     = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                           required=False)

# marshmallow schema for the pipeline nodes, contains the operator nodes
class PipelineQueryPlanSchema(marshmallow.Schema):
    pipelineId      = marshmallow.fields.Integer()
    incomingTuples  = marshmallow.fields.Integer()
    predecessors    = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                               required=False)
    successors      = marshmallow.fields.List( marshmallow.fields.Integer(allow_none=True),
                                               required=False)
    operators       = marshmallow.fields.List(
                                    marshmallow.fields.Nested(OperatorQueryPlanNodeSchema),
                                    required=False)

class ExtendedSchema(_BenchmarkResultCreateSchema):
    serializedLogicalPlan = marshmallow.fields.List(
        marshmallow.fields.Nested(
            LogicalQueryPlanNodeSchema,
            required=False,
            metadata={
                "description": conbench.util.dedent_rejoin(
                    """
                    The logical plan sent as 'serializedLogicalPlan' by benchmark.py. 
                    The plan is optional and saved into separate tables, following this schema:

                        benchmark_result <--- logical_query_plan <--- [ logical_query_plan_node ]

                    The logical plan shows up under /benchmark-results/<id>.
                    """
                )
            }
        ),
        required=False,
    )

    serializedPipelinePlan = marshmallow.fields.List(
        marshmallow.fields.Nested(
            PipelineQueryPlanSchema,
            required=False,
            metadata={
                "description": conbench.util.dedent_rejoin(
                    """
                    The pipeline plan sent as 'serializedPipelinePlan' by benchmark.py. 
                    The plan is optional and saved into separate tables, following this schema:

                        benchmark_result <--- pipeline_plan <--- [ pipeline_node ] <--- operator_plan <--- [ operator_nodes ]

                    The pipeline plan shows up under /benchmark-results/<id>.
                    """
                )
            }
        ),
        required=False,
    )

# Overwrites the current create schema which is used for validation with our own extension
BenchmarkResultFacadeSchema.create = ExtendedSchema()