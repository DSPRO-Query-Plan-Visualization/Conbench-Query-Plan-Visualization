import json

from conbench.entities.benchmark_result import BenchmarkResult
from queryplan.entities.query_plan import LogicalQueryPlan, LogicalQueryPlanSerializer, PipelinePlanSerializer, \
    _create_queryplan_in_db
from queryplan.entities.query_plan import PipelinePlan
import logging
from flask import request, jsonify, render_template, url_for
from conbench.api import api, rule
from conbench.api._endpoint import ApiEndpoint, maybe_login_required
import flask_login
import marshmallow
from conbench.entities._entity import NotFound

"""
Creation process of a new benchmark_result entry:
1.      POST route registered in conbench/api/results.py with protection
2.1.    BenchmarkListAPI defines:
            serializer = BenchmarkResultSerializer()
            schema = BenchmarkResultFacadeSchema()
2.2.    BenchmarkListAPI validates using schema.create, saves result into data
3.      creates entry using BenchmarkResult.create(data) and returns 201 if success
-------
4.      We can intercept the request after successful completion
        and create our own tables (also link them to the benchmark).
        Because of steps 1, 2 and 3 we know:
        - the request is already validated
        - the benchmark_result entry created
        - login requirements checked
-------
"""


log = logging.getLogger(__name__)

"""
Successful creation of a benchmark_result entry will trigger the
event listener which then creates the query plan tables.
"""
@api.after_request
def create_queryplan_after_benchmark(response):
    if (
        request.method == "POST"
        and request.path == url_for("api.benchmarks")
        and response.status_code == 201
    ):
        try:
            req_data = request.get_json()
            res_data = response.get_json()
            benchmark_id = res_data.get("id")
            if benchmark_id and BenchmarkResult.one(id=benchmark_id):
                _create_queryplan_in_db(req_data,benchmark_id)
        except Exception as e:
            log.warning(f"Query plan creation failed: {e}")
    return response
"""
This route is for fetching the query plans using a benchmark_result_id.
The response has this format:
{
    "serializedLogicalPlan"  : [...],
    "serializedPipelinePlan" : [...]
}

To use this, add a fetch request in the <script> tag and parse with 
your graph building function - or just include the queryplan.html like:

    {% include "queryplan.html" %}
    
where you want it to be in the html. See benchmark-result.html for an example.
This file copies the structure of conbench/api/results.py, so if you want
to add more functionality like PUT or DELETE check out conbenchs implementation.
"""
class QueryPlanEntityApi(ApiEndpoint):
    logical_serializer = LogicalQueryPlanSerializer()
    pipeline_serializer = PipelinePlanSerializer()

    def _get(self, benchmark_result_id):
        try:
            logical = LogicalQueryPlan.one(benchmark_id=benchmark_result_id)
            pipeline = PipelinePlan.one(benchmark_id=benchmark_result_id)
        except NotFound:
            self.abort_404_not_found()
        return logical, pipeline

    @maybe_login_required
    def get(self, benchmark_result_id):
        """
        ---
        description: |
            Get a benchmark specific query plan.
        responses:
            "200": "QueryPlanEntity"
            "401": "401"
            "404": "404"
        parameters:
          - name: benchmark_result_id
            in: path
            schema:
                type: string
        tags:
          - QueryPlan
        """
        serializedLogicalPlan, serializedPipelinePlan = self._get(benchmark_result_id)
        queryplan = {
            "serializedLogicalPlan": self.logical_serializer.one.dump(serializedLogicalPlan),
            "serializedPipelinePlan": self.pipeline_serializer.one.dump(serializedPipelinePlan)
        }
        return queryplan

# Though conbench wants to fade this out, for consistency reason we also do it like this:
query_plan_entity_view = QueryPlanEntityApi.as_view("queryplan")
rule(
    "/queryplan/<benchmark_result_id>",
    view_func=query_plan_entity_view,
    methods=["GET"],
)