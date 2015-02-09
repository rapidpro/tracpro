controllers = angular.module('trac.controllers', ['trac.services']);

#============================================================================
# Latest poll issues controller
#============================================================================
controllers.controller 'LatestIssuesController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.issues = []

  $scope.init = ->

    $scope.refreshIssues()

  $scope.refreshIssues = ->
    PollService.fetchLatestIssues (issues) ->
      $scope.issues = issues
      $scope.loading = false
      $timeout($scope.refreshIssues, 5000)

]