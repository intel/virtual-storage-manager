
$(function(){
	console.log("Import Cluster Ready");

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
}

$("#btnImportCluster").click(function(){
	if(   $("#id_monitor_host").val() == ""
	   || $("#id_monitor_keyring").val() == ""
	   || $("#id_cluster_conf").val() == ""){
		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	var monitor_host_id = $("#id_monitor_host").val();
	var monitor_host_name = $("#id_monitor_host")[0].options[$("#id_monitor_host")[0].selectedIndex].text;
	var monitor_keyring = $("#id_monitor_keyring").val();
	var cluster_conf = $("#id_cluster_conf").val();

	var data = {
		"monitor_host_id":monitor_host_id,
		"monitor_host_name":monitor_host_name,
		"monitor_keyring":monitor_keyring,
		"cluster_conf":cluster_conf,
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/cluster-import/import_cluster/",
		data: postData,
		dataType:"json",
		success: function(data){
                if (data.status=='Failed') {
                     showTip("error",data.message)
                }
                else{
                    showTip("success",data.message)
                }
				window.location.href="/dashboard/vsm/cluster-import/";
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
})