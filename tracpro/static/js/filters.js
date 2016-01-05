var chart_numeric = function() {
    var dataType = $('#id_data_type').val();
    if (dataType) {
        var label = $('#id_data_type :selected').text();
        $('.chart-numeric').each(function(i, item) {
            var chart = $(item);
            chart.closest('.poll-question').find('.data-type').text(label);
            chart.highcharts({
                title: {
                    text: ""
                },
                categories: chart.data('categories'),
                plotOptions: {
                    series: {
                        cursor: "pointer",
                        point: {
                            events: {
                                click: function() {
                                    // Take user to pollrun detail page
                                    // when they click on a specific date.
                                    location.href = this.options.url;
                                }
                            }
                        }
                    }
                },
                series: [
                    {
                        type: "area",
                        name: chart.data('name'),
                        data: chart.data(dataType)
                    }
                ]
            });
        });
    }
}

$(function() {
    /* Initialize date fields. */
    $("input[class^='datepicker']").datepicker();

    /* Update button text when filter form display is toggled. */
    $('#filters').on('show.bs.collapse', function() {
        $('#toggle-filters').text('Hide filters...');
    });
    $('#filters').on('hide.bs.collapse', function() {
        $('#toggle-filters').text('Show filters...');
    });

    /* Don't submit unused fields. */
    $('.filter-form #id_date_range').on('change', function() {
        var showDates = $(this).val() === 'other';
        $('#filter-dates').toggleClass('hidden', !showDates);
        $('#filter-dates').find('input').prop('disabled', !showDates)
    }).change();

    /* Update numeric data display on the client side. */
    $('#id_data_type').on('change', chart_numeric)

    /* Initialize the charts. */
    chart_numeric();
});
