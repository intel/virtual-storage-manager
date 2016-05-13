
function Init_Data(){
    $("#txtKVPair").val("{\"k\":2,\"m\":1,\"technique\":\"reed_sol_van\"}");
    $("#txtPGNum").val("3")
};
$(function(){
Init_Data();
});


$(document).ajaxStart(function(){
    //load the spin
    ShowSpin();
});

function CreateECProFile(){
	//Check the field is should not null
	if($("#txtName").val() == "" || $("#txtPluginName").val() == ""
	|| $("#txtPluginPath").val() == ""
	|| $("#txtKVPair").val() == "" || $("#txtPGNum").val() == ""){
		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}
	var data = {
			"ec_profiles":[]
	}
    var ec_profile = {
                'name':$("#txtName").val(),
                'plugin':$("#txtPluginName").val(),
                'plugin_path':$("#txtPluginPath").val(),
                'plugin_kv_pair':$("#txtKVPair").val(),
                'pg_num':$("#txtPGNum").val(),
			}
	data["ec_profiles"].push(ec_profile)
	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/ecprofiles-management/add_ec_profile/",
		data: postData,
		dataType:"json",
		success: function(data){
				//console.log(data);
                if(data.error_code.length == 0){
                    window.location.href="/dashboard/vsm/ecprofiles-management/";
                    showTip("info",data.info);
                }
                else{
                    showTip("error",data.error_msg);
                }
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500)
                	showTip("error","INTERNAL SERVER ERROR")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
}

$(document).ajaxStart(function(){
    //load the spin
    ShowSpin();
});
