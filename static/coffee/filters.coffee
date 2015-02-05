filters = angular.module('trac.filters', []);

filters.filter 'autodate', (dateFilter) ->
  (date) ->
    dateFilter(date, 'MMM dd, yyyy HH:mm')
