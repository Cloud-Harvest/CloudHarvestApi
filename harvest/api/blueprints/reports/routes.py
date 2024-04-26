from flask import Blueprint, Response, jsonify, request
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'reporting_bp', __name__
)


@blueprint.route('/reports/run', methods=['GET'])
def reports_run() -> Response:
    request_json = loads(request.get_json())

    report_name = request_json.get('report_name')
    from configuration import HarvestConfiguration

    if report_name not in HarvestConfiguration.reports.keys():
        return jsonify([{'error': f'report `{request_json.get("report_name")}` not found'}])

    report_configuration = HarvestConfiguration.reports.get(report_name)

    from core.tasks.tasks.factories import task_chain_from_dict

    if request_json.get('describe'):
        return jsonify({'data': report_configuration})

    report = task_chain_from_dict(task_chain_name=report_name,
                                  task_chain=report_configuration,
                                  chain_class_name='report',
                                  **request_json)

    report.run()

    if not hasattr(report, 'result'):
        return jsonify([{'error': 'no result'}])

    result = report.result

    return jsonify(result)


@blueprint.route('/reports/list', methods=['GET'])
def reports_list() -> Response:
    from configuration import HarvestConfiguration
    # local api reports
    result = {
        'data': [
            {
                'Name': k,
                'Description': v.get('description', 'no description')
            }
            for k, v in HarvestConfiguration.reports.items()
        ],
        'meta': {
            'headers': ['Name', 'Description']
        }
    }

    return jsonify(result)
