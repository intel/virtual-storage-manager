
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

/* This is the base Vsm JavaScript object. There is only ever one of these
 * loaded (referenced as vsm with a lower-case h) which happens immediately
 * after the definition below.
 *
 * Scripts that are dependent on functionality defined in the Vsm object
 * must be included after this script in templates/base.html.
 */
var Vsm = function () {
  var vsm = {},
      initFunctions = [];

  /* Use the addInitFunction() function to add initialization code which must
   * be called on DOM ready. This is useful for adding things like event
   * handlers or any other initialization functions which should precede user
   * interaction but rely on DOM readiness.
   */
  vsm.addInitFunction = function (fn) {
    initFunctions.push(fn);
  };

  /* Call all initialization functions and clear the queue. */
  vsm.init = function () {
    for (var i = 0; i < initFunctions.length; i += 1) {
      initFunctions[i]();
    }

    // Prevent multiple executions, just in case.
    initFunctions = [];
  };

  return vsm;
};

// Create the one and only vsm object.
var vsm = new Vsm();

