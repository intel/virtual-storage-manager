

function ChangePoolName(value){
	$("#txtTag").val(value);
}

function ChangeStorageGroup(obj){
	$("#txtPGNumber").val(parseInt(obj.options[obj.selectedIndex].getAttribute("pgNumber")));
}

function ChangeEableAutoQuto(checked){
	$("#txtPGNumber")[0].readOnly = checked
}

function ChangePoolQuota(checked){
	$("#txtPoolQuota")[0].readOnly = !checked
	if(checked==false){
		$("#txtPoolQuota").val("");
	}
}

function AddPool(){
	//Check the field is should not null
	if($("#txtPoolName").val() == ""){
		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}
	var data = {
			"pool":{
				"name":$("#txtPoolName").val(),
				"storageGroupId":$("#selStorageGroup").val(),
                'storageGroupName': $("#selStorageGroup")[0].options[$("#selStorageGroup")[0].selectedIndex].text,
				"replicatedStorageGroupId":'replica',
                'auto_growth_pg': $("#txtPGNumber").val(),
				'tag': $("#txtTag").val(),
				'clusterId': "0",
				'createdBy': "VSM",
				'enablePoolQuota': $("#chkPoolQuota")[0].checked,
				'poolQuota': $("#txtPoolQuota").val(),
			}
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/create_replicated_pool_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				//console.log(data);
                if(data.status == "OK"){
                    window.location.href="/dashboard/vsm/poolsmanagement/";
                }
                else{
                    showTip("error",data.message);
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