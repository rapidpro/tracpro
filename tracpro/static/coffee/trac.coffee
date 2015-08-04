app = angular.module('trac', ['trac.services', 'trac.controllers', 'trac.filters']);

app.config [ '$interpolateProvider', '$httpProvider', ($interpolateProvider, $httpProvider) ->
  # Since Django uses {{ }}, we will have angular use [[ ]] instead.
  $interpolateProvider.startSymbol "[["
  $interpolateProvider.endSymbol "]]"

  # Use Django's CSRF functionality
  $httpProvider.defaults.xsrfCookieName = 'csrftoken'
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken'

  # Disabled since we reverted to Angular 1.2.x
  # $httpProvider.useApplyAsync(true);
]

#
# Page initialization
#
$ ->
  init_language_fields()
  init_audio_answers()
  init_charts()


init_language_fields = () ->
  $('.language-field').each ->
    # Django won't let us output a hidden input with a visible label - so we output a char control and switch it out
    # with a dynamic hidden input... which then select2.js converts to a swanky select box.
    text_ctrl = $(this)
    initial = text_ctrl.val()
    hidden_ctrl_id = text_ctrl.prop('id') + '_select2'
    text_ctrl.hide()
    text_ctrl.prop('name', '')
    text_ctrl.after('<input type="hidden" id="' + hidden_ctrl_id + '" name="language" style="width: 300px" value="' + initial + '" />')

    data_url = '/contact/create/'  # move to own languages view?

    data_callback = (term, page, context) -> return { search: term, page: page }
    results_callback = (response, page, context) -> return response
    init_sel_callback = (element, callback) ->
      codes = $(element).val()
      if codes != ""
        $.getJSON(data_url, {initial: codes}).done (data) ->
            callback(data.results[0])

    $('#' + hidden_ctrl_id).select2({
        selectOnBlur: false,
        multiple: false,
        quietMillis: 200,
        minimumInputLength: 0,
        ajax: {
            url: data_url,
            dataType: 'json',
            data: data_callback,
            results: results_callback
        },
        initSelection: init_sel_callback
    })


init_audio_answers = () ->
  $('a.answer-audio').each ->
    answer_link = $(this)
    answer_id = answer_link.data('answer-id')
    audio_url = answer_link.prop('href')

    # add icons inside
    answer_link.html('<span class="glyphicon glyphicon-play" />')

    # add audio element after
    audio_id = 'answer_audio_' + answer_id
    answer_link.after('<audio id="' + audio_id + '"><source src="' + audio_url + '" />Your browser does not support HTML5 audio</audio>')
    audio = answer_link.parent(null).find('#' + audio_id)

    on_playback_start = () ->
      answer_link.find('span').removeClass('glyphicon-play').addClass('glyphicon-pause')

    on_playback_stop = () ->
      answer_link.find('span').removeClass('glyphicon-pause').addClass('glyphicon-play')

    audio.on 'play', on_playback_start
    audio.on 'pause', on_playback_stop
    audio.on 'ended', on_playback_stop

    answer_link.addClass('btn btn-default')
    answer_link.prop('href', '#')
    answer_link.on 'click', () ->
      audio_elem = $('#' + audio_id).get(0)
      if audio_elem.paused
        audio_elem.play()
      else
        audio_elem.pause()


#
# Chart initialization
#
init_charts = () ->
  $('.chart').each ->
    container = $(this)
    question_id = container.data('question-id')
    chart_type = container.data('chart-type')
    window_min = container.data('window-min')
    window_max = container.data('window-max')
    unit_text = container.data('unit-text')
    data = eval('chart_' + question_id + '_data')

    if data && data.length > 0
      if chart_type == 'word'
        init_word_cloud(container, data)
      else if chart_type == 'pie'
        init_pie_chart(container, data, unit_text)
      else if chart_type == 'column'
        init_column_chart(container, data, unit_text)
      else if chart_type == 'time-area'
        init_time_area_chart(container, data, window_min, window_max, unit_text)
      else if chart_type == 'time-line'
        init_time_line_chart(container, data, window_min, window_max, unit_text)
    else
      init_no_data(container)


init_word_cloud = (container, data) ->
  container.jQCloud(data)


init_pie_chart = (container, data, unit_text) ->
  container.highcharts({
    title: null,
    tooltip: { enabled: false },
    plotOptions: {
      pie: {
        dataLabels: {
          enabled: true,
          format: '<b>' + unit_text + '</b><br/><b>{point.name}</b>: {point.percentage:.1f} %',
          style: {
            color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
          }
        }
      }
    },
    series: [{type: 'pie', data: data}],
    credits: { enabled: false }
  })


init_column_chart = (container, data, unit_text) ->
  container.highcharts({
    chart: { type: 'column' },
    title: null,
    xAxis: {
      title: null,
      categories: data[0]
    },
    yAxis: {
      title: null,
      allowDecimals: false
    },
    series: [{
      data: data[1]
    }],
    legend: { enabled: false },
    credits: { enabled: false },
    tooltip: {
                formatter: ->
                    '<b>' + unit_text + '</b> ' + @x +
                    '<br />' + @y
            },
  })

init_time_area_chart = (container, series, window_min, window_max, unit_text) ->
  container.highcharts({
    chart: { type: 'area' },
    title: null,
    xAxis: {
      type: 'datetime',
      title: { enabled: false },
      min: window_min,
      max: window_max
    },
    yAxis: {
      title: {
        text: 'Percent'
      }
    },
    tooltip: {
      xDateFormat: '<b>' + unit_text + '</b><br />%b %d, %Y',
      pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b> ({point.y:,.0f})<br/>',
      shared: true
    },
    plotOptions: {
      area: {
        stacking: 'percent',
        lineColor: '#ffffff',
        lineWidth: 1,
        marker: {
          lineWidth: 1,
          lineColor: '#ffffff'
        }
      }
    },
    series: series,
    credits: { enabled: false }
  })


init_time_line_chart = (container, data, window_min, window_max, unit_text) ->
  container.highcharts({
    chart: { type: 'spline' },
    title: null,
    xAxis: {
      type: 'datetime',
      title: { enabled: false },
      min: window_min,
      max: window_max
    },
    yAxis: { title: null },
    plotOptions: {
      spline: {
        marker: {
          enabled: true
        }
      }
    },
    series: [{ name: "Average", data: data }],
    legend: { enabled: false },
    credits: { enabled: false },
    tooltip: {
      valuePrefix: unit_text + ' '
    }
  })


init_no_data = (container) ->
  container.addClass('chart-no-data');
  container.text("No data")
