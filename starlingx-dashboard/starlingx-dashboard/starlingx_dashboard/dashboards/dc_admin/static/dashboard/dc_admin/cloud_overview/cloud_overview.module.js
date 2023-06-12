/**
 * Copyright (c) 2017-2023 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */

(function() {
  'use strict';

  /**
   * @ngdoc horizon.dashboard.dc_admin.cloud_overview
   * @ngModule
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display the cloud overview panel.
   */
  angular
    .module('horizon.dashboard.dc_admin.cloud_overview', [])
    .run(['$rootScope', '$cookies', '$location', run])
    .config(config);

  /*
    Keeps the subcloud name updated in the menu,
    instead of showing the region name.
  */
  function run($rootScope, $cookies, $location) {
    $rootScope.$on('$locationChangeSuccess', function() {
      var services_region = $cookies.get('services_region');

      //Finds the element where region name is displayed
      var region_element = document.querySelector('span.context-region');

      if (region_element) {
        //Set the subcloud name only if it is a subcloud
        if(services_region != 'RegionOne' && services_region != 'SystemController'){
          var subcloud_name = $cookies.get('subcloud_' + services_region);
          region_element.textContent = subcloud_name;
        }
      }
    });
  }

  config.$inject = [
    '$provide',
    '$windowProvider'
  ];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/dc_admin/';
    $provide.constant('horizon.dashboard.dc_admin.basePath', path);
  }

})();
