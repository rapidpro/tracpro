controllers = angular.module('trac.controllers', ['trac.services']);

#============================================================================
# Latest poll issues controller
#============================================================================
controllers.controller 'LatestIssuesController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.issues = []

  $scope.init = ->

    $scope.refreshIssues()

  $scope.refreshIssues = ->
    PollService.fetchLatestIssues (issues) ->
      $scope.issues = issues
      $timeout($scope.refreshIssues, 5000)

]