jQuery.fn.extend({
    chart_numeric: function() {
        var dataType = $('#id_num_display').val();
        if (["sum", "average", "response-rate"].indexOf(dataType) != -1) {
            var label = $('#id_num_display :selected').text();
            $(this).each(function(i, item) {
                var chart = $(item);
                chart.closest('.poll-question').find('.data-type').text(label);
                var data = chart.data('chart');
                chart.highcharts({
                    title: {
                        text: ""
                    },
                    xAxis: {
                        categories: data.dates
                    },
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
                            data: data[dataType]
                        }
                    ]
                });
            });
        }
    },
    chart_open_ended: function() {
        $(this).each(function(i, item) {
            var chart = $(item);
            chart.jQCloud(chart.data('chart'));
        });
    },
    chart_multiple_choice: function() {
        $(this).each(function(i, item) {
            var chart = $(item);
            var data = chart.data('chart')
            chart.highcharts({
                chart: {
                    type: 'area'
                },
                title: {
                    text: ''
                },
                xAxis: {
                    categories: data.dates,
                    tickmarkPlacement: 'on',
                    title: {
                        enabled: false
                    }
                },
                yAxis: {
                    title: {
                        text: 'Percent'
                    }
                },
                tooltip: {
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
                    },
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
                series: data.series
            });
        });
    }
});

$(function() {
    /* Initialize date fields. */
    $("input[class^='datepicker']").datepicker({
        changeMonth: true,
        changeYear: true,
        selectOtherMonths: true,
        showOtherMonths: true,
        yearRange: "2013:" + new Date().getFullYear()
    });

    /* Update button text when filter form display is toggled. */
    $('#filters').on('show.bs.collapse', function() {
        $('#toggle-filters').text('Hide filters...');
    });
    $('#filters').on('hide.bs.collapse', function() {
        $('#toggle-filters').text('Show filters...');
    });

    /* Don't submit unused fields. */
    $('.filter-form #id_date_range').on('change', function() {
        var showDates = $(this).val() === 'custom';
        $('#filter-dates').toggleClass('hidden', !showDates);
        $('#filter-dates').find('input').prop('disabled', !showDates)
    }).change();

    /* Update numeric data display on the client side. */
    $('#id_num_display').on('change', function() {
        $('.chart-numeric').chart_numeric();
    });

    /* Initialize the charts. */
    $('.chart-open-ended').chart_open_ended();
    $('.chart-numeric').chart_numeric();
    $('.chart-multiple-choice').chart_multiple_choice();
});
