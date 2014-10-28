
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

/* Utilities for common needs which aren't JS builtins. */
horizon.utils = {
  // Log function which checks for DEBUG and the existence of a console.
  log: function () {
    if (horizon.conf.debug && typeof(console) !== "undefined" && typeof(console.log) !== "undefined") {
      console.log(arguments);
    }
  },

  capitalize: function(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  },

  /*
    Adds commas to any integer or numbers within a string for human display.

    EG:
      horizon.utils.humanizeNumbers(1234); -> "1,234"
      horizon.utils.humanizeNumbers("My Total: 1234"); -> "My Total: 1,234"
  */
  humanizeNumbers: function(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  },

  /*
    Truncate a string at the desired length. Optionally append an ellipsis
    to the end of the string.

    EG:
      horizon.utils.truncate("String that is too long.", 18, true); ->
          "String that is too&hellip;"
  */
  truncate: function(string, size, includeEllipsis) {
    if(string.length > size) {
      if(includeEllipsis) {
        return string.substring(0, (size - 3)) + "&hellip;";
      } else {
        return string.substring(0, size);
      }
    } else {
      return string;
    }
  }
};
