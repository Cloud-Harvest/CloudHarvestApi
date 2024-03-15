from flask import Blueprint, Response, jsonify

# Blueprint Configuration
blueprint = Blueprint(
    'reporting_bp', __name__
)


@blueprint.route('/reports/run', methods=['GET'])
def reports_run(name: str, match: list = None, add: list = None, limit: int = None, order: list = None,
                **kwargs) -> Response:
    """
    execute a defined report and return the results
    :param name: the report to be executed
    :param match: matching logic
    :param add: appends extra fields to a report output
    :param limit: only return this many records
    :param order: sort results by these fields
    :return:
    """
    from .resources import Report
    with Report(**kwargs) as report:
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
