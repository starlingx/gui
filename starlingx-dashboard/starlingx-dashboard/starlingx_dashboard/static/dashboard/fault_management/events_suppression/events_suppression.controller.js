/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
/**
 * Copyright (c) 2024 Wind River Systems, Inc.
 *
 * SPDX-License-Identifier: Apache-2.0
 *
 */

(function() {
	'use strict';

	angular
	  .module('horizon.dashboard.fault_management.events_suppression')
	  .controller('EventsSuppressionController', ['horizon.dashboard.fault_management.events_suppression.service', '$scope', EventsSuppressionController]);

	var fieldMappings = {
		'alarm_id': 'Event ID',
		'description': 'Description',
		'suppression_status': 'Status'
	  };

	function EventsSuppressionController(eventsSuppressionService, $scope) {
	  $scope.downloadEventsSuppressionData = function() {
		eventsSuppressionService.getPromise().then(function(response) {
		  var csvData = convertToCSV(response.data.items, fieldMappings);
		  triggerDownload(csvData, 'events-suppression-data.csv');
		});
	  };

	  function convertToCSV(objArray, fieldMappings) {
		var array = objArray;
		var str = '';
		var row = '';

		// Header
		for (var index in objArray[0]) {
		  if (fieldMappings[index]) {
			row += '"' + fieldMappings[index].replace(/"/g, '""') + '",';
		  }
		}
		row = row.slice(0, -1);
		str += row + '\r\n';

		// Data
		for (var i = 0; i < array.length; i++) {
		  var line = '';
		  for (var index in array[i]) {
			if (fieldMappings[index]) {
			  var data = array[i][index];

			  if (data && typeof data === 'string') {
				// Escape double quotes and replace internal line breaks
				data = data.replace(/"/g, '""').replace(/(\r\n|\n|\r)/gm, " ");
			  }

			  line += '"' + data + '",';
			}
		  }
		  line = line.slice(0, -1);
		  str += line + '\r\n';
		}
		return str;
	  }

	  function triggerDownload(csvData, filename) {
		var blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
		var link = document.createElement("a");
		if (link.download !== undefined) {
		  var url = URL.createObjectURL(blob);
		  link.setAttribute("href", url);
		  link.setAttribute("download", filename);
		  link.style.visibility = 'hidden';
		  document.body.appendChild(link);
		  link.click();
		  document.body.removeChild(link);
		}
	  }
	}
  })();
