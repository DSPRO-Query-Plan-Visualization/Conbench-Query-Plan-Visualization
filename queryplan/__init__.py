from flask import Blueprint

# this makes queryplan/templates visible to conbench/templates
# alternatively add the queryplan.html directly to conbench/templates
queryplan_bp = Blueprint(
    "queryplan",
    __name__,
    template_folder="templates"
)
