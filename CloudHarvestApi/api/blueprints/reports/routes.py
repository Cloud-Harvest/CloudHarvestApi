from flask import Blueprint, Response, jsonify, request
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'reporting_bp', __name__,
    url_prefix='/reports'
)


@blueprint.route(rule='list', methods=['GET'])
def reports_list() -> Response:
    from startup import HarvestConfiguration

    # local api reports
    result = {
        'data': [
            {
                'Name': k,
                'Description': v.get('report', {}).get('description', 'no description'),
                'Headers': v.get('report', {}).get('headers', [])
            }
            for k, v in HarvestConfiguration.reports.items()
        ],
        'meta': {
            'headers': ['Name', 'Description']
        }
    }

    return jsonify(result)


@blueprint.route(rule='reload', methods=['GET'])
def reports_reload() -> Response:
    from startup import HarvestConfiguration

    HarvestConfiguration.load_reports()

    return reports_list()


@blueprint.route(rule='run', methods=['GET'])
def reports_run() -> Response:
    from startup import HarvestConfiguration

    request_json = loads(request.get_json())

    report_name = request_json.get('report_name')
    reports = HarvestConfiguration.reports

    if report_name not in reports.keys():
        return jsonify([{'error': f'report `{request_json.get("report_name")}` not found'}])

    report_configuration = reports.get(report_name)

    from CloudHarvestCoreTasks.factories import task_chain_from_dict

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
