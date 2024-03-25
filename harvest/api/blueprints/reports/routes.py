from flask import Blueprint, Response, jsonify, request
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'reporting_bp', __name__
)


@blueprint.route('/reports/run', methods=['GET'])
def reports_run() -> Response:
    request_json = loads(request.get_json())

    from configuration import HarvestConfiguration

    if request_json.get('report_name_or_file') not in HarvestConfiguration.reports.keys():
        return jsonify({'error': f'report `{request_json.get("report_name_or_file")}` not found'})

    from .resources import Report
    with Report(**request_json) as report:
        report.build()

    return jsonify({})


@blueprint.route('/reports/list', methods=['GET'])
def reports_list() -> Response:
    from configuration import HarvestConfiguration
    # local api reports
    result = [
        {
            'name': k,
            'description': v.get('description', 'no description')
         }
        for k, v in HarvestConfiguration.reports.items()
    ]

    return jsonify(result)
