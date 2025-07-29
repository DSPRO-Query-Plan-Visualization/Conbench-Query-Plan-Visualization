"""
Creation process of a new benchmark_result entry:
1.      POST route registered in /api/results.py with protection
2.1.    BenchmarkListAPI defines:
            serializer = BenchmarkResultSerializer()
            schema = BenchmarkResultFacadeSchema()
2.2.    BenchmarkListAPI validates using schema.create, saves result into data
3.      creates entry using BenchmarkResult.create(data) and returns 201 if success

4.      We can intercept the request after successful completion
        and create our own tables (also link them to the benchmark).
        Because of steps 1, 2 and 3 we know:
        - the request is already validated
        - the benchmark_result entry created
        - login requirements checked

TODO: change description to include newer stash and wait for creation event variant
--> goal is to keep atomicity by using event listener
"""

from conbench.entities.benchmark_result import BenchmarkResult
from queryplan.entities.query_plan import LogicalQueryPlan
import logging
from flask import request, jsonify, render_template, g
from conbench.api import api
from conbench.api._endpoint import ApiEndpoint, maybe_login_required
import flask_login
import marshmallow

log = logging.getLogger(__name__)

@api.before_request
def stash_benchmark_data():
    if request.method == "POST" and request.path == "/api/benchmarks/":
        g.benchmark_request_json = request.get_json()


# TODO: no use anymore
@api.after_request
def after_benchmark_created(response):
    if request.method == "POST--------" and request.path == "/api/benchmarks/" and response.status_code == 201:
        id = response.get_json()["id"]
        l_plan = LogicalQueryPlan.create({"benchmark_id": id})
    return response


#TODO: change to proper route
@api.route('/bla', methods=['GET'])
# adding maybe_login or flask_login.login_required doesn't do anything in app
def my_custom_benchmark_handler():
    # Example logic – replace with your own
    return jsonify({"bla": "BLA"})

#TODO: change to proper route
@api.route('/bla/<id>', methods=['GET'])
def id_automat(id):
    # Example logic – replace with your own
    return jsonify({"bla": str(id) + "test" })