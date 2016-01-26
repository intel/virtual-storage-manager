$(function(){
	InitCtrlCSS();
});

function InitCtrlCSS(){
	var ctrlSelect = $("select");
	for(var i=0;i<ctrlSelect.length;i++){
		ctrlSelect[i].className = "form-control";
	}

	var ctrlText = $("input[type='text']");
	for(var i=0;i<ctrlText.length;i++){
		ctrlText[i].className = "form-control";
	}

    var ctrlText = $("input[type='number']");
    for(var i=0;i<ctrlText.length;i++){
            ctrlText[i].className = "form-control";
    }
}


$("#btnRemoveCacheTier").click(function(){
	var CachePoolID = $("#id_cache_tier_pool").val();
	var data = {
       	'cache_tier': {
            'cache_pool_id': CachePoolID
        }
    }

    var postData = JSON.stringify(data);
    token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/remove_cache_tier_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
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

    return false;
})

function ChangePoolQuota(checked){
	$("#txtPoolQuota")[0].readOnly = !checked
	if(checked==false){
		$("#txtPoolQuota").val("");
	}
}

$("#id_name").change(function(){
    $("#id_tag").val(this.value);
});


$("#btnCreateErasureCodedPool").click(function(){
	//Check the field is should not null
	if(   $("#id_name").val() == ""
	   || $("#id_tag").val() == ""){

		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}


	var data = {
		"pool": {
            'name': $("#id_name").val(),
            'storageGroupId': $("#id_storage_group").val(),
            'storageGroupName': $("#id_storage_group")[0].options[$("#id_storage_group")[0].selectedIndex].text,
            'tag': $("#id_tag").val(),
            'clusterId': '0',
            'createdBy': 'VSM',
            'ecProfileId': $("#id_ec_profile").val(),
            'ecFailureDomain': $("#id_ec_failure_domain").val(),
            'enablePoolQuota':  $("#chkEnablePoolQuota")[0].checked,
            'poolQuota': $("#txtPoolQuota").val()
        }
	}

	var postData = JSON.stringify(data);
    token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/create_ec_pool_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
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

});