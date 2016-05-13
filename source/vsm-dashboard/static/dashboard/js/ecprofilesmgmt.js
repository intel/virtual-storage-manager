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


//remove the ec_profiles
$("#ec_profiles__action_remove_ec_profiles").click(function(){
	var ec_profile_id_list = {"ec_profile_id_list":[]}
	
	var is_selected = false;

	$("#ec_profiles>tbody>tr").each(function(){
        if(this.children[0].children[0].checked) {

            var ec_profile_id = this.children[0].children[0].value;
            is_selected = true;
            ec_profile_id_list["ec_profile_id_list"].push(ec_profile_id);

        }
	})

    if(is_selected == false){
        showTip("warning","please select the EC ProFile!");
        return false;
    }

	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/ecprofiles-management/remove_ec_profiles/",
		data: JSON.stringify(ec_profile_id_list),
		dataType:"json",
		success: function(data){
				console.log(data);
                if(data.error_code.length == 0){
                    window.location.href="/dashboard/vsm/ecprofiles-management/";
                    showTip("info",data.info);
                }
                else{
                    showTip("error",data.error_msg);
                }
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").show();
					$("#divOSDTip")[0].innerHTML = XMLHttpRequest.statusText;
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
	return false;
});

