
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

horizon.addInitFunction(function () {
    module("Messages (horizon.messages.js)");

    test("Basic Alert", function () {
        var message, message2;
        message = horizon.alert("success", "A message!");
        ok(message, "Create a success message.");
        ok(message.hasClass("alert-success"), 'Verify the message has the "alert-success" class.');
        equal($('#main_content .messages .alert').length, 1, "Verify our message was added to the DOM.");
        horizon.clearAllMessages();
        equal($('#main_content .messages .alert').length, 0, "Verify our message was removed.");
    });

    test("Multiple Alerts", function () {
        message = horizon.alert("error", "An error!");
        ok(message.hasClass("alert-error"), 'Verify the first message has the "alert-error" class.');

        message2 = horizon.alert("success", "Another message");
        equal($('#main_content .messages .alert').length, 2, "Verify two messages have been added to the DOM.");

        horizon.clearErrorMessages();
        equal($('#main_content .messages .alert-error').length, 0, "Verify our error message was removed.");
        equal($('#main_content .messages .alert').length, 1, "Verify one message remains.");
        horizon.clearSuccessMessages();
        equal($('#main_content .messages .alert-success').length, 0, "Verify our success message was removed.");
        equal($('#main_content .messages .alert').length, 0, "Verify no messages remain.");
    });

    test("Alert With HTML Tag", function () {
        safe_string = "A safe message <a>here</a>!"
        message = horizon.alert("success", safe_string, "safe");
        ok(message, "Create a message with extra tag.");
        ok((message.html().indexOf(safe_string ) != -1), 'Verify the message with HTML tag was not escaped.');
        equal($('#main_content .messages .alert').length, 1, "Verify our message was added to the DOM.");
        horizon.clearAllMessages();
        equal($('#main_content .messages .alert').length, 0, "Verify our message was removed.");
    });
});
