/**
 * Copyright (c) 2017-2020 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */


(function() {
  'use strict';

  /**
   * @ngdoc dcOverviewCloudTableController
   * @ngController
   *
   * @description
   * Controller for the dc_admin overview table.
   * Serve as the focal point for table actions.
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview')
    .controller('dcOverviewCloudTableController', dcOverviewCloudTableController);

  dcOverviewCloudTableController.$inject = [
    '$q',
    '$scope',
    '$timeout',
    '$interval',
    '$window',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.util.i18n.gettext',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.modal.deleteModalService',
    'horizon.app.core.openstack-service-api.dc_manager',
    'horizon.app.core.openstack-service-api.keystone',
  ];

  function dcOverviewCloudTableController(
    $q,
    $scope,
    $timeout,
    $interval,
    $window,
    toast,
    gettext,
    modalFormService,
    simpleModalService,
    deleteModal,
    dc_manager,
    keystone
  ){

    var ctrl = this;
    ctrl.subClouds = [];
    ctrl.isubClouds = [];
    ctrl.subCloudSummaries = [];

    //ctrl.globalActions = globalActions;

    ctrl.manage = manage;
    ctrl.unmanageSubcloud = unmanageSubcloud;
    ctrl.deleteSubcloud = deleteSubcloud;
    ctrl.addSubcloud = addSubcloud;
    ctrl.editSubcloud = editSubcloud;
    ctrl.addSubcloudAction = addSubcloudAction;
    ctrl.goToAlarmDetails = goToAlarmDetails;
    ctrl.goToHostDetails = goToHostDetails;

    // Auto-refresh
    ctrl.$interval = $interval;
    ctrl.refreshInterval;
    ctrl.refreshWaitTime = 5000;

    // Messages
    ctrl.endpointErrorMsg = gettext("This subcloud's endpoints are not yet accessible by horizon.  Please log out and log back in to access this subcloud.");

    ctrl.filterFacets = [
      {
        label: gettext('Name'),
        name: 'name',
        singleton: true
      },
      {
        label: gettext('Management State'),
        name: 'is_managed',
        singleton: true,
        options: [
          { label: gettext('unmanaged'), key: 'false' },
          { label: gettext('managed'), key: 'true' }
        ]
      },
      {
        label: gettext('Availability Status'),
        name: 'availability_status',
        singleton: true,
        options: [
          { label: gettext('online'), key: 'online' },
          { label: gettext('offline'), key: 'offline' }
        ]
      },
      {
        label: gettext('Deploy Status'),
        name: 'deploy_status',
        singleton: true,
        options: [
          { label: gettext('not-deployed'), key: 'not-deployed' },
          { label: gettext('pre-install'), key: 'pre-install' },
          { label: gettext('pre-install-failed'), key: 'pre-install-failed' },
          { label: gettext('installing'), key: 'installing' },
          { label: gettext('install-failed'), key: 'install-failed' },
          { label: gettext('bootstrapping'), key: 'bootstrapping' },
          { label: gettext('bootstrap-failed'), key: 'bootstrap-failed' },
          { label: gettext('deploying'), key: 'deploying' },
          { label: gettext('deploy-failed'), key: 'deploy-failed' },
          { label: gettext('complete'), key: 'complete' }
        ]
      },
      {
        label: gettext('Sync Status'),
        name: 'sync_status',
        singleton: true,
        options: [
          { label: gettext('unknown'), key: 'unknown' },
          { label: gettext('in-sync'), key: 'in-sync' },
          { label: gettext('out-of-sync'), key: 'out-of-sync' },
        ]
      },
      {
        label: gettext('Alarm Status'),
        name: 'status',
        singleton: true,
        options: [
          { label: gettext('critical'), key: 'critical' },
          { label: gettext('degraded'), key: 'degraded' },
          { label: gettext('disabled'), key: 'disabled' },
          { label: gettext('OK'), key: 'OK' },
        ]
      },
      {
        label: gettext('Subcloud ID'),
        name: 'subcloud_id',
        singleton: true
      }
    ];

    ctrl.getManagementState = {
      false: gettext('unmanaged'),
      true: gettext('managed')
    };

    getData();
    startRefresh();

    ////////////////////////////////

    function getData() {
      // Fetch subcloud data to populate the table
      $q.all([
        dc_manager.getSubClouds().success(getSubCloudsSuccess),
        dc_manager.getSummaries().success(getSummariesSuccess)
      ]).then(function(){
        map_subclouds();
      })
    }

    function getSubCloudsSuccess(response) {
      response.items.map(modifyItem);
      ctrl.subClouds = response.items;

      // Because "managed" is a substring of "unmanaged", a search for the
      // word "managed" will return both managed and unmanaged items. To
      // go around this issue we map management_state to new boolean
      // attribute is_managed.
      function modifyItem(item) {
         if (item.management_state == 'managed') {
            item.is_managed = true;
          }
          else {
            item.is_managed = false;
          }
       }
    }

    function getSummariesSuccess(response) {
      ctrl.subCloudSummaries = response.items;
    }

    function map_subclouds() {
      ctrl.subClouds = $.map(ctrl.subClouds, function (subCloud){
        var match = ctrl.subCloudSummaries.filter(function(summary){return summary.name == subCloud.name;});
        if (match.length == 0){
          // No matching summary to this subcloud
          return subCloud;
        }
        return angular.extend(subCloud, match[0]);
      });
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


    /////////////////
    // UNMANAGE/MANAGE //
    /////////////////

    function manage(cloud) {
      var response = dc_manager.editSubcloud(cloud.subcloud_id, {'management-state': 'managed'});
    }

    function unmanageSubcloud(cloud) {
      var options = {
        title: 'Confirm Subcloud Unmanage',
        body: 'Are you sure you want to unmanage subcloud '+cloud.name+'?',
        submit: 'Unmanage',
        cancel: 'Cancel'
      };

      simpleModalService.modal(options).result.then(function() {
        dc_manager.editSubcloud(cloud.subcloud_id, {'management-state': 'unmanaged'});
      });
    }


    ////////////
    // DELETE //
    ////////////

    function deleteSubcloud(cloud) {
      var scope = { $emit: deleteActionComplete };
      var context = {
        labels: {
          title: gettext('Confirm Subcloud Delete'),
          message: gettext('This will delete subcloud %s, are you sure you want to continue?'),
          submit: gettext('Delete'),
          success: gettext('Subcloud delete successful.')
          },
        deleteEntity: doDelete,
        successEvent: 'success',
      };
      cloud.id = cloud.subcloud_id;
      deleteModal.open(scope, [cloud], context);

    }
    function doDelete(id) {
      var response = dc_manager.deleteSubcloud(id);
      return response;
    }

    function deleteActionComplete(eventType) {
      return;
    }


    /////////////////
    // CREATE/EDIT //
    /////////////////

    var subcloudSchema = {
      type: "object",
      properties: {
        "name": {
          type: "string",
          title: "Name"},
        "description": {
          type: "string",
          title: "Description"},
        "location": {
          type: "string",
          title: "Location"},
        "management-subnet": {
          type: "string",
          title: "Management Subnet"},
        "management-start-ip": {
          type: "string",
          title: "Management Start IP"},
        "management-end-ip": {
          type: "string",
          title: "Management End IP"},
        "management-gateway-ip": {
          type: "string",
          title: "Management Gateway IP"},
        "systemcontroller-gateway-ip": {
          type: "string",
          title: "System Controller Gateway IP"},
      },
      required: ["name", "management-subnet", "management-start-ip", "management-end-ip", "management-gateway-ip", "systemcontroller-gateway-ip"],
    };

    function addSubcloud() {
      var model = {
        "name": "",
        "description": "",
        "location": "",
        "management-subnet": "",
        "management-start-ip": "",
        "management-end-ip": "",
        "management-gateway-ip": "",
        "systemcontroller-gateway-ip": ""};
      var config = {
        title: gettext('Add Subcloud'),
        schema: subcloudSchema,
        form: ["*"],
        model: model
      };
      return modalFormService.open(config).then(function then() {
        return ctrl.addSubcloudAction(model);
      });
    }

    function addSubcloudAction(model) {
      return dc_manager.createSubcloud(model);
    }

    var editsubcloudSchema  = {
      type: "object",
      properties: {
        "name": {
          type: "string",
          title: "Name",
          readonly: true},
        "description": {
          type: "string",
          title: "Description"},
        "location": {
          type: "string",
          title: "Location"},
      }
    };

    function editSubcloud(cloud) {
      var model = {
        "name": cloud.name,
        "description": cloud.description,
        "location": cloud.location,
        };

      var config = {
        title: gettext('Edit Subcloud'),
        schema: editsubcloudSchema,
        form: ["*"],
        model: model
      };
      return modalFormService.open(config).then(function(){
        return dc_manager.editSubcloud(cloud.subcloud_id, model);
      });
    }

    /////////////
    // Details //
    /////////////

    function goToAlarmDetails(cloud) {
      // TODO handle tabs?

      // Check to see that the subcloud is managed
      if (cloud.management_state != 'managed') {
        toast.add('error',
            gettext('The subcloud must be in the managed state before you can access detailed views.'));
        return;
      }

      keystone.getCurrentUserSession().success(function(session){
        session.available_services_regions.indexOf(cloud.name)
        if (session.available_services_regions.indexOf(cloud.name) > -1) {
          $window.location.href = "/auth/switch_services_region/"+ cloud.name + "/?next=/admin/active_alarms/";
        } else {
          toast.add('error', ctrl.endpointErrorMsg);
          // TODO(tsmith) should we force a logout here with an reason message?
        }
      }).error(function(error) {
        toast.add('error',
            gettext("Could not retrieve current user's session."));
      });
    }

    function goToHostDetails(cloud) {
      // Check to see that the subcloud is managed
      if (cloud.management_state != 'managed') {
        toast.add('error',
            gettext('The subcloud must be in the managed management state before you can access detailed views.'));
        return;
      }

      keystone.getCurrentUserSession().success(function(session){
        if (session.available_services_regions.indexOf(cloud.name) > -1) {
          $window.location.href = "/auth/switch_services_region/"+ cloud.name + "/?next=/admin/";
        } else {
          toast.add('error', ctrl.endpointErrorMsg);
        }
      }).error(function(error) {
        toast.add('error',
            gettext("Could not retrieve current user's session."));
      });
    }

  }
})();
