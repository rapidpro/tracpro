import json

from dash.utils import datetime_to_ms

from tracpro.polls.charts import render_data

def baseline_chart(baseline_answers):

    chart_type = 'time-line'
    chart_data = []

    #render_data() example
    # [{u'data': [(datetime.datetime(2015, 8, 11, 12, 40, 11, 942000, tzinfo=<UTC>), 2)], u'name': u'Yes'}]
    #result: '[{"data": [[1439296811942, 2]], "name": "Yes"}]'

    #'[[1439389879040, "20.00000000"], [1439389693168, "35.00000000"], [1439389722678, "26.00000000"]]'


    #[(datetime.datetime(2015, 8, 12, 14, 31, 19, 40000, tzinfo=<UTC>), u'20.00000000', u'rebecca'),
    # (datetime.datetime(2015, 8, 12, 14, 28, 13, 168000, tzinfo=<UTC>), u'35.00000000', u'Erin Mullaney'),
    # (datetime.datetime(2015, 8, 12, 14, 28, 42, 678000, tzinfo=<UTC>), u'26.00000000', u'Erin Test Caktus')]


    for answer in baseline_answers:
        chart_data.append((datetime_to_ms(answer[0]), float(answer[1])))

    chart_data_json = json.dumps(chart_data)
    import ipdb; ipdb.set_trace();

    """
    chart_type = 'time-line'
    chart_data = []
    for pollrun in pollruns:
        average = pollrun.get_answer_numeric_average(question, region)
        chart_data.append((pollrun.conducted_on, average))
    """
    return chart_type, chart_data
