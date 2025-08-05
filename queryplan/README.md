# Conbench Query Plan Visualization

This folder contains all functionality related to query plans. 
To maintain modularity and a clear overview, 
all related code is centralized here, 
with only a few minimal and necessary exceptions.

## Folder Purpose

The queryplan directory includes:

- API endpoints for handling query plan data

- Database models and schema definitions

- Marshmallow validation logic

- Frontend template and JavaScript for rendering query plan graphs

It mirrors Conbench's internal structure to stay consistent, but operates independently.

## Minimal Conbench Modifications

A few targeted changes were made outside this folder:

- Dockerfile includes the queryplan module so it’s available at runtime.

- conbench/__init __.py registers the queryplan/templates/queryplan.html template.

- conbench/api/__init __.py imports queryplan/api/results.py for query plan API functionality and queryplan/entities/validation.py.
as a marshmallow schema extension

- /migration/versions/e15e8b226491_benchmark_id_ondelete_cascade_query_.py
 adds cascade behavior on benchmark_id for query plan records.

- benchmark-result.html includes the query plan UI via the shared template.

## Frontend Behavior

The UI code in queryplan/templates/queryplan.html handles rendering of the graph. To include the visualization in a page, use:

{% include "queryplan.html" %}

Make sure a benchmark.id is available in the page context. Without it, no query plan will load.

The graph fetches its data via:

GET /api/queryplan/<benchmark_id>

This API endpoint returns both the logical and pipeline plan structures for the given benchmark.

## API & Backend Logic

- queryplan/api/results.py handles API requests (GET, POST).

- queryplan/entities/query_plan.py defines and creates the relevant tables and relationships.

- queryplan/entities/validation.py handles request schema validation using Marshmallow.