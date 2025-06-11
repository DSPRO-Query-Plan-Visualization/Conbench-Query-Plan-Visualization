# Systest Mimic

Following the footsteps of `nebula/scripts/benchmarking/benchmark.py`,  
the `systest_mimic/` directory contains all files necessary to send benchmarks (and soon, query plans) to the Conbench server.

To avoid clutter, all data and scripts **not natively belonging to Conbench** should be stored here.

## Contents

- `benchmark.py` - Script to send benchmark data to the server  
- `debug_results.json` - Example benchmark file, for debugging purposes
- `.env` - Args for testing, important: CONBENCH_URL, CONBENCH_EMAIL, CONBENCH_PASSWORD, CONBENCH_RUN_REASON

## Additional Requirements

- `pip install -e benchadapt/python/` - local install
- `pip install python-dotenv` - for easy .env loading