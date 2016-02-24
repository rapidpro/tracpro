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
