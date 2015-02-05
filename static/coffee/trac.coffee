app = angular.module('trac', ['trac.services', 'trac.controllers']);

app.config [ '$httpProvider', ($httpProvider) ->
  $httpProvider.defaults.xsrfCookieName = 'csrftoken'
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken'
]

#============================================================================
# Since Django uses {{ }}, we will have angular use [[ ]] instead.
#============================================================================
app.config ($interpolateProvider) ->
  $interpolateProvider.startSymbol "[["
  $interpolateProvider.endSymbol "]]"
