/* Remove dark grey. */
var lightColors = ['#7cb5ec', '#90ed7d', '#f7a35c', '#8085e9', '#f15c80',
                   '#e4d354', '#2b908f', '#f45b5b', '#91e8e1'];

jQuery.fn.extend({
    chart_baseline: function() {
        $(this).each(function(i, item) {
            var chart = $(item);
            chart.highcharts({
                chart: {
                    type: "area"
                },
                title: {
                    text: chart.data("title") || ""
                },
                subtitle: {
                    text: chart.data("subtitle") || ""
                },
                xAxis: {
                    categories: chart.data("chart").categories || []
                },
                yAxis: {
                    title: {
                        text: chart.data("y-axis-title") || ""
                    }
                },
                legend: {
                    layout: 'vertical',
                    align: 'right',
                    verticalAlign: 'top',
                    floating: true,
                    backgroundColor: '#FFFFFF'
                },
                series: chart.data("chart").series || []
            });
        });
    },
    chart_numeric: function() {
        var dataType = $('#id_numeric').val();
        if (["sum", "average", "response-rate"].indexOf(dataType) != -1) {
            var label = $('#id_numeric :selected').text();
            $(this).each(function(i, item) {
                var chart = $(item);
                chart.closest('.poll-question').find('.data-type').text(label);
                var data = chart.data('chart');
                chart.highcharts({
                    chart: {
                        type: "area"
                    },
                    colors: lightColors,
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
            chart.jQCloud(chart.data('chart'), {
                height: 320
            });
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
                colors: lightColors,
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
                colors: lightColors,
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
    /* Update numeric data display on the client side. */
    $('.filter-form #id_numeric').on('change', function() {
        $('.chart-numeric').chart_numeric();
    });

    /* Initialize the charts. */
    $('.chart-open-ended').chart_open_ended();
    $('.chart-numeric').chart_numeric();
    $('.chart-multiple-choice').chart_multiple_choice();
    $('.chart-bar').chart_bar();
    $('.chart-baseline').chart_baseline();
});
