import json
import subprocess
import time
import os
import logging
from typing import List, Any

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

log = logging.getLogger(__name__)

from benchadapt import BenchmarkResult
from benchadapt.adapters import BenchmarkAdapter

import argparse


class SystestAdapter(BenchmarkAdapter):
    """
    An adapter to read in Systest benchmark results, transform them to the correct schema and upload them to conbench
    """
    systest_working_dir: str
    result_fields_override: dict[str, Any] = None,
    result_fields_append: dict[str, Any] = None,

    def __init__(
            self,
            systest_working_dir: str,
            result_fields_override: dict[str, Any] = None,
            result_fields_append: dict[str, Any] = None,
    ) -> None:
        super().__init__(
            command=[],
            result_fields_append=result_fields_append,
            result_fields_override=result_fields_override)
        self.systest_working_dir = systest_working_dir
        self.results = self.transform_results()

    def _transform_results(self) -> List[BenchmarkResult]:
        with open(self.systest_working_dir + "/BenchmarkResults.json", "r") as f:
            raw_results = json.load(f)

        benchmarkResults = []

        for result in raw_results:
            benchmarkResults.append(BenchmarkResult(
                stats={
                    "data": [result["time"]],
                    "unit": "ns"
                },
                context={"benchmark_language": "systest"},
                tags={"name": result["query name"]},
                github={"repository": "https://github.com/fake/fake"}, #TODO: might not be needed
                query_plan="SECOND_TEST", # TODO: add attribute to conbench
            ))

        return benchmarkResults


systest_adapter = SystestAdapter(
    systest_working_dir=os.path.join(os.path.dirname(__file__)),
    result_fields_override={"run_reason": os.getenv("CONBENCH_RUN_REASON")},
)

# reads the message send to the server
message = systest_adapter.post_results()
if message:
    print(message) #prints the message send to the server for debugging purposes