/**
 * Initializes a language selection widget
 * @param id the existing text input id
 * @param data_url the URL for AJAX data fetching
 */
function init_language_select(id, data_url) {
    // Django won't let us output a hidden input with a visible label - so we output a char control and switch it out
    // with a dynamic hidden input... which then select2.js converts to a swanky select box.
    var text_ctrl = $('#' + id);
    var initial = text_ctrl.val();
    var hidden_ctrl_id = id + '_select2';
    text_ctrl.hide();
    text_ctrl.prop('name', '');
    text_ctrl.after('<input type="hidden" id="' + hidden_ctrl_id + '" name="language" style="width: 300px" value="' + initial + '" />');

    $('#' + hidden_ctrl_id).select2({
        selectOnBlur: false,
        multiple: false,
        quietMillis: 200,
        minimumInputLength: 0,
        ajax: {
            url: data_url,
            dataType: 'json',
            data: function (term, page, context) {
                return {
                    search: term,
                    page: page
                };
            },
            results: function (response, page, context) {
                return response;
            }
        },
        initSelection: function(element, callback) {
            var codes = $(element).val();
            if (codes !== "") {
                $.getJSON(data_url, {initial: codes}).done(function(data) {
                    callback(data.results[0]);
                });
            }
        }
    });
}
