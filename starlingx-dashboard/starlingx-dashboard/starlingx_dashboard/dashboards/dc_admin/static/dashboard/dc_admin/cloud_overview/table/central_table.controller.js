/**
 * Copyright (c) 2017-2019, 2025 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */


(function() {
  'use strict';

  /**
   * @ngdoc dcOverviewCentralTableController
   * @ngController
   *
   * @description
   * Controller for the dc_admin cloud overview system controller table.
   * Serve as the focal point for table actions.
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview')
    .controller('dcOverviewCentralTableController', dcOverviewCentralTableController);

  dcOverviewCentralTableController.$inject = [
    '$q',
    '$scope',
    '$timeout',
    '$interval',
    '$window',
    '$cookies',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.app.core.openstack-service-api.sysinv',
    'horizon.app.core.openstack-service-api.fm',
  ];

  function dcOverviewCentralTableController(
    $q,
    $scope,
    $timeout,
    $interval,
    $window,
    $cookies,
    toast,
    gettext,
    sysinv,
    fm
  ){

    var ctrl = this;
    ctrl.centralClouds = [];
    ctrl.icentralClouds = [];

    ctrl.goToCentralAlarmDetails = goToCentralAlarmDetails;
    ctrl.goToCentralHostDetails = goToCentralHostDetails;

    // Auto-refresh
    ctrl.$interval = $interval;
    ctrl.refreshInterval;
    ctrl.refreshWaitTime = 5000;

    getData();
    startRefresh();

    ////////////////////////////////

    function getData() {
      // Fetch central cloud data to populate the table
      $q.all([
        sysinv.getSystem().success(getSystemSuccess),
        fm.getAlarmSummary().success(getAlarmSummarySuccess)
      ]).then(function(){
        angular.extend(ctrl.centralClouds[0], ctrl.alarmSummary);
      })
    }

    function getSystemSuccess(response) {
      ctrl.centralClouds = [response];
    }

    function getAlarmSummarySuccess(response) {
      ctrl.alarmSummary = response;  //Only one summary exists
    }

    ///////////////////////////
    // REFRESH FUNCTIONALITY //
    ///////////////////////////

    function startRefresh() {
      if (angular.isDefined(ctrl.refreshInterval)) return;
      ctrl.refreshInterval = ctrl.$interval(getData, ctrl.refreshWaitTime);
    }

    $scope.$on('$destroy',function(){
      ctrl.stopRefresh();
    });

    function stopRefresh() {
      if (angular.isDefined(ctrl.refreshInterval)) {
        ctrl.$interval.cancel(ctrl.refreshInterval);
        ctrl.refreshInterval = undefined;
      }
    }

    /////////////
    // Details //
    /////////////

    function goToCentralAlarmDetails(cloud) {
      var regionName = $cookies.get('region_one_name') || "RegionOne";
      $window.location.href = "/auth/switch_services_region/" + regionName + "/?next=/admin/active_alarms/";
    }

    function goToCentralHostDetails(cloud) {
      var regionName = $cookies.get('region_one_name') || "RegionOne";
      $window.location.href = "/auth/switch_services_region/" + regionName + "/?next=/admin/";
    }

  }
})();
