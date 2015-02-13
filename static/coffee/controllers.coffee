controllers = angular.module('trac.controllers', ['trac.services']);

#============================================================================
# Latest poll issues controller
#============================================================================
controllers.controller 'LatestIssuesController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.issues = []

  $scope.init = ->
    $timeout($scope.refresh, 1)

  $scope.refresh = ->
    PollService.fetchLatestIssues (issues) ->
      $scope.issues = issues
      $scope.loading = false
      $timeout($scope.refresh, 5000)

]


#============================================================================
# Active regions controller
#============================================================================
controllers.controller 'ActiveRegionsController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.regions = []

  $scope.init = ->
    $timeout($scope.refresh, 1)

  $scope.refresh = ->
    PollService.fetchActiveRegions (regions) ->
      $scope.regions = regions
      $scope.loading = false
      $timeout($scope.refresh, 5000)

]


#============================================================================
# Active groups controller
#============================================================================
controllers.controller 'ActiveGroupsController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.groups = []

  $scope.init = ->
    $timeout($scope.refresh, 1)

  $scope.refresh = ->
    PollService.fetchActiveGroups (groups) ->
      $scope.groups = groups
      $scope.loading = false
      $timeout($scope.refresh, 5000)

]