from flask import Blueprint, Response, jsonify, request
from json import loads

# Blueprint Configuration
blueprint = Blueprint(
    'reporting_bp', __name__,
    url_prefix='/reports'
)


@blueprint.route(rule='list', methods=['GET'])
def reports_list() -> Response:
    from configuration import HarvestConfiguration

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
    from configuration import HarvestConfiguration

    HarvestConfiguration.load_reports()

    return reports_list()


@blueprint.route(rule='run', methods=['GET'])
def reports_run() -> Response:
    from configuration import HarvestConfiguration

    request_json = loads(request.get_json())

    report_name = request_json.get('report_name')
    reports = HarvestConfiguration.reports

    if report_name not in reports.keys():
        return jsonify([{'error': f'report `{request_json.get("report_name")}` not found'}])

    report_configuration = reports.get(report_name)

    from CloudHarvestCoreTasks.factories import task_chain_from_dict

    if request_json.get('describe'):
        return jsonify({'data': report_configuration})

    chains = []

    for chain_class, chain_configuration in report_configuration.items():
        chain = task_chain_from_dict(task_chain_name=chain_class,
                                     task_chain=chain_configuration,
                                     chain_class_name=chain_class,
                                     **request_json)
        chains.append(chain)

        chain.run()

    return jsonify(chains[-1].result)

