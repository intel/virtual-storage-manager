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

    //disable control
    DisableControl();
}

function DisableControl(){
    if($("#id_auto_growth_pg").length>0){
            $("#id_auto_growth_pg")[0].readOnly = true;
    }

    if($("#id_pool_quota").length>0){
            $("#id_pool_quota")[0].readOnly = true;
    }
}

$("#id_disable_pg_auto_growth").click(function(){
    console.log(this.checked);
    if(this.checked)
        $("#id_auto_growth_pg")[0].readOnly = false;
    else
        $("#id_auto_growth_pg")[0].readOnly = true;
});

$("#id_enable_pool_quota").click(function(){
    console.log(this.checked);
    if(this.checked)
        $("#id_pool_quota")[0].readOnly = false;
    else
        $("#id_pool_quota")[0].readOnly = true;
});

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



$("#btnCreateErasureCodedPool").click(function(){
	//Check the field is should not null
	if(   $("#id_name").val() == ""
	   || $("#id_tag").val() == ""
	   || $("#id_pool_quota").val() == "" ){

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
            'enablePoolQuota': $("#id_enable_pool_quota")[0].checked,
            'poolQuota': $("#id_pool_quota").val(),
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