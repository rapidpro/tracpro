controllers = angular.module('trac.controllers', ['trac.services']);

#============================================================================
# Latest poll runs controller
#============================================================================
controllers.controller 'LatestPollRunsController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.pollruns = []

  $scope.refresh = ->
    PollService.fetchLatestPollRuns (pollruns) ->
      $scope.pollruns = pollruns
      $scope.loading = false
      $timeout($scope.refresh, 5000)

  $scope.refresh()
]


#============================================================================
# Active regions controller
#============================================================================
controllers.controller 'ActiveRegionsController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.regions = []

  $scope.refresh = ->
    PollService.fetchActiveRegions (regions) ->
      $scope.regions = regions
      $scope.loading = false
      $timeout($scope.refresh, 5000)

  $scope.refresh()
]


#============================================================================
# Active groups controller
#============================================================================
controllers.controller 'ActiveGroupsController', [ '$scope', '$timeout', 'PollService', ($scope, $timeout, PollService) ->

  $scope.loading = true
  $scope.groups = []

  $scope.refresh = ->
    PollService.fetchActiveGroups (groups) ->
      $scope.groups = groups
      $scope.loading = false
      $timeout($scope.refresh, 5000)

  $scope.refresh()
]