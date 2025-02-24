/**
 * Copyright (c) 2017-2025 Wind River Systems, Inc.
*
* SPDX-License-Identifier: Apache-2.0
*
 */


(function() {
  'use strict';

  angular.module('horizon.dashboard.dc_admin.cloud_overview')
  .directive('updateFilteredCount', ['$filter', function($filter) {
    return {
      // Require the stTable controller from an ancestor (the table element).
      require: '^stTable',
      link: function(scope, element, attrs, stTableCtrl) {
        scope.$watchGroup([
          function() {
            return stTableCtrl.tableState().search.predicateObject;
          },
          function() {
            return scope.table.subClouds;
          }
        ], function(newValues) {
          var predicate = newValues[0];
          var fullCollection = newValues[1] || [];
          var filtered;
          if (!predicate) {
            filtered = fullCollection;
          } else {
            filtered = $filter('filter')(fullCollection, predicate);
          }
          scope.table.filteredCount = filtered.length;
        });
      }
    };
  }]);
})();

