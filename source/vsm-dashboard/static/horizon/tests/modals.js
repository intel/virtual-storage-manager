
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
    module("Modals (horizon.modals.js)");

    test("Modal Creation", function () {
        var modal,
            title = "Test Title",
            body = "<p>Test Body</p>",
            confirm = "Test Confirm";
        modal = horizon.modals.create(title, body, confirm);
        ok(modal, "Verify our modal was created.");

        modal = $("#modal_wrapper .modal");
        modal.modal();
        equal(modal.length, 1, "Verify our modal was added to the DOM.");
        ok(modal.hasClass("in"), "Verify our modal is not hidden.");
        equal(modal.find("h3").text(), title, "Verify the title was added correctly.");
        equal(modal.find(".modal-body").text().trim(), body, "Verify the body was added correctly.");
        equal(modal.find(".modal-footer .btn-primary").text(), confirm, "Verify the footer confirm button was added correctly.");
        modal.find(".modal-footer .cancel").click();
        ok(!modal.hasClass("in"), "Verify our modal is hidden.");
    });
});
