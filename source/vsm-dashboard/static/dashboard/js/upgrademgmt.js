
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

$(function(){
    InitCtrlCSS();
});

function InitCtrlCSS(){
    var ctrlText = $("input[type='text']");
    for(var i=0;i<ctrlText.length;i++){
        ctrlText[i].className = "form-control";
    }
}

$("#btnCephUpgrade").click(function(){

    GenerateCephUpgradeData();

})





function PostRequest(data){
    var token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        data: data,
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/cephupgrade/ceph_upgrade/",
        success: function (data) {
            showTip(data.status,data.message);
            return false;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        headers: {
            "X-CSRFToken": token
        },
        complete: function(){

        }
    });
}




function GenerateCephUpgradeData() {
    var data_list = new Array();
    var pkg_url = $("#id_package_url").val();
    var key_url = $("#id_key_url").val();
    var proxy = $("#id_proxy").val();
    var ssh_user = $("#id_ssh_user").val();
    var data = {pkg_url:pkg_url,key_url:key_url,proxy:proxy,ssh_user:ssh_user};
    data_list.push(data);
    data = JSON.stringify(data_list);
    PostRequest(data);
}






