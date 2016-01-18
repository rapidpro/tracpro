jQuery.fn.extend({
    chart_numeric: function() {
        var dataType = $('#id_numeric').val();
        if (["sum", "average", "response-rate"].indexOf(dataType) != -1) {
            var label = $('#id_numeric :selected').text();
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
            var data = chart.data('chart');
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
    },
    chart_bar: function() {
        $(this).each(function(i, item) {
            var chart = $(item);
            var data = chart.data('chart');
            chart.highcharts({
                chart: {
                    type: 'bar'
                },
                title: {
                    text: ''
                },
                xAxis: {
                    categories: data.categories,
                    tickmarkPlacement: 'on'
                },
                yAxis: {
                    tickInterval: 1
                },
                tooltip: {
                    pointFormat: '<span style="color:{series.color}">{series.name}</span>: {point.y:,.0f}',
                    shared: true
                },
                series: [{
                    name: 'Response Counts',
                    data: data.data,
                    colorByPoint: true
                }]
            });
        });
    },
});

$(function() {
    /* Initialize Highcharts Colors, remove the dark grey */
    Highcharts.setOptions({
        colors: ['#7cb5ec', '#90ed7d', '#f7a35c', '#8085e9', '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1']
    });

    /* Initialize date fields. */
    if ($("input[class^='datepicker']").length) {
        $("input[class^='datepicker']").datepicker({
            changeMonth: true,
            changeYear: true,
            selectOtherMonths: true,
            showOtherMonths: true,
            yearRange: "2013:" + new Date().getFullYear()
        });
    }

    /* Update button text when filter form display is toggled. */
    $('#filters').on('show.bs.collapse', function() {
        $('#toggle-filters').text('Hide filters...');
    });
    $('#filters').on('hide.bs.collapse', function() {
        $('#toggle-filters').text('Show filters...');
    });

    /* Don't submit custom date fields if they are not used. */
    $('.filter-form #id_date_range').on('change', function() {
        var showDates = $(this).val() === 'custom';
        $('#filter-dates').toggleClass('hidden', !showDates);
        $('#filter-dates').find('input').prop('disabled', !showDates)
    }).change();

    /* Don't submit empty form fields. */
    $('.filter-form').on('submit', function() {
        $(this).find('input,select').each(function(i, item) {
          var self = $(this);
          if (!self.val()) {
            self.prop('disabled', true);
          }
        });
        return true;
    });

    /* Update numeric data display on the client side. */
    $('#id_numeric').on('change', function() {
        $('.chart-numeric').chart_numeric();
    });

    /* Initialize the charts. */
    $('.chart-open-ended').chart_open_ended();
    $('.chart-numeric').chart_numeric();
    $('.chart-multiple-choice').chart_multiple_choice();

    $('.chart-bar').chart_bar();
});
