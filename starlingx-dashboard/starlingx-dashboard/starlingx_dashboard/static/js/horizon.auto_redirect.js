/**
 *  Copyright (c) 2019 Wind River Systems, Inc.
 *
 *  SPDX-License-Identifier: Apache-2.0
 *
 */

horizon.addInitFunction(function () {
  // This is a workaround to automatically redirect to the login page when an authorization error page is displayed.
  // It occurs every time a user switches between RegionOne and SystemController in a distributed cloud setup
  // since the same dashboards are not accessible to both regions.
  // The login page will see the user is already logged in and redirect to the user's home page.
  if ($("#content_body:contains('You are not authorized to access this page')").length > 0){
    window.location.replace("/auth/login/")
  }
});
