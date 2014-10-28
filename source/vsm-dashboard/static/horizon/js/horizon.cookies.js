
/* Copyright 2014 Intel Corporation, All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the"License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied. See the License for the
 specific language governing permissions and limitations
 under the License.
 */

/* Convenience functions for dealing with namespaced Horizon cookies. */
horizon.cookies = {
  read: function (cookie_name) {
    // Read in a cookie which contains JSON, and return a parsed object.
    var cookie = $.cookie("horizon." + cookie_name);
    if (cookie === null) {
      return {};
    }
    return $.parseJSON(cookie);
  },
  write: function (cookie_name, data) {
    // Overwrites a cookie.
    $.cookie("horizon." + cookie_name, JSON.stringify(data), {path: "/"});
  },
  update: function (cookie_name, key, value) {
    var data = horizon.cookies.read("horizon." + cookie_name);
    data[key] = value;
    horizon.cookies.write(cookie_name, data);
  },
  remove: function (cookie_name) {
    $.cookie("horizon." + cookie_name, null);
  }
};
