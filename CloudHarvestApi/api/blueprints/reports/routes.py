from api.blueprints.base import HarvestBlueprint
from flask import Response, jsonify, request
from json import loads

# Blueprint Configuration
report_blueprint = HarvestBlueprint(
    'reporting_bp', __name__,
    url_prefix='/reports'
)


@report_blueprint.route(rule='list', methods=['GET'])
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


@report_blueprint.route(rule='reload', methods=['GET'])
def reports_reload() -> Response:
    from configuration import HarvestConfiguration

    HarvestConfiguration.load_reports()

    return reports_list()


@report_blueprint.route(rule='run', methods=['GET'])
def reports_run() -> Response:
    """
    This endpoint is used to run a specific report and return its results.

    It expects a JSON payload in the request with the following structure:
    {
        "report_name": "<name_of_the_report>",
        "describe": <boolean>,
        "performance": <boolean>,
        "headers": ["<header1>", "<header2>", ...],
        "add_keys": ["<additional_key1>", "<additional_key2>", ...],
        "exclude_keys": ["<exclude_key1>", "<exclude_key2>", ...],
        "sort": ["<sort_key1>", "<sort_key2>", ...]
    }

    - "report_name" is the name of the report to run.
    - "describe" is an optional boolean parameter. If it's set to true, the function will return the configuration of the report instead of running it.
    - "performance" is an optional boolean parameter. If it's set to true, the function will return performance metrics for the report.
    - "headers" is a list of headers for the task.
    - "add_keys" is a list of additional keys to include in the headers.
    - "exclude_keys" is a list of keys to exclude from the headers.
    - "sort" is a list of keys to sort the results by.

    The function first checks if the report specified in "report_name" exists in the HarvestConfiguration.reports
    dictionary. If it doesn't, it returns an error.

    If the "describe" parameter is set to true, the function returns the configuration of the report.

    If the "describe" parameter is not set or is set to false, the function runs the report. It creates a task chain
    for each item in the report configuration and runs it. The results of the task chains are collected and
    returned as a JSON response.

    If the "performance" parameter is set to true, the function also returns performance metrics for the report as an
    extension to the report content. The performance metrics are defined in the BaseTaskChain.performance_metrics
    property.

    Returns:
        Response: A Flask Response object containing a JSON response with the results of the report or an error message.
    """

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

    results = []

    for chain_class, chain_configuration in report_configuration.items():
        chain = task_chain_from_dict(task_chain_name=chain_class,
                                     task_chain=chain_configuration,
                                     chain_class_name=chain_class,
                                     **request_json)
        chain.run()

        results.extend(chain.result)
        if request_json.get('performance'):
            chain.extend(chain.performance_metrics())

    return jsonify(results)

