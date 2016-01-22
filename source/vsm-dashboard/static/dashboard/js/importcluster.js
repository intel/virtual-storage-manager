
function getFont(treeId, node) {
	return node.font ? node.font : {};
}

function onClickEvent(event, treeId, treeNode, clickFlag) {
}

var CRUSHMAP = "";

var setting = {
	view: {
		showLine: true,
		fontCss: getFont,
		nameIsHTML: true
	},
	data: {
		simpleData: {
			enable: true
		}
	},
	callback: {
		//beforeClick: beforeClick,
		onClick: onClickEvent
	}
};


$(function(){
	console.log("Import Cluster Ready");
	initCtrlCSS();
	atuoDetectDialog("Auto Detect",$("#divAutoDetectInfo")[0].innerHTML);
	$("#divAutoDetectInfo").remove();
});

function initCtrlCSS(){
	var ctrlSelect = $("select");
	for(var i=0;i<ctrlSelect.length;i++){
		ctrlSelect[i].className = "form-control";
	}

	var ctrlText = $("input[type='text']");
	for(var i=0;i<ctrlText.length;i++){
		ctrlText[i].className = "form-control";
	}
}

function atuoDetectDialog(title,body){
	var html = "";
	html += "<div class='modal-dialog' style='z-index:1045'>";
	html += "	<div class='modal-content' >";
	html += "		<div class='modal-header'>";
	html += "			<button type='button' class='close' data-dismiss='modal' aria-label='Close'><span aria-hidden='true'>&times;</span></button>";
	html += "			<h4 class='modal-title' id='myModalLabel'>";
	html += title;
	html += "			</h4>";
	html += "		</div>";
	html += "		<div class='modal-body'>";
	html += body;
	html += "		</div>";
	html += "		<div class='modal-footer'>";
	html += "			<button id='btnDialogSubmit' type='button' class='btn btn-primary' onclick='addDetect()'>Auto Detect</button>";
	html += "			<button id='btnDialogCancel' type='button' class='btn btn-default' data-dismiss='modal'>Close</button>";
	html += "		</div>";
	html += "	</div>";
	html += "</div>";

	var dialogWrapper = $("#modal_wrapper")[0];
	dialogWrapper.id = "modal_wrapper";
	dialogWrapper.className = "modal fade";
	dialogWrapper.innerHTML = html;

	return $("#modal_wrapper");
}

function openAddDetectDialog(){
	$("#modal_wrapper").modal("show");

	return false;
}

function addDetect(){

	if($("#txtMonitorKeyring").val() == ""){
		showTip("error","Monitor Keyring should not be empty");
		return  false;
	}

	var ctrlServerList = $("#selMonitorHost")[0];
	var monitor_id = ctrlServerList.value;
	var monitor_name = ctrlServerList.options[ctrlServerList.selectedIndex].text;
	var keyring = $("#txtMonitorKeyring").val();


	$("#selMonitorHost2")[0].selectedIndex = ctrlServerList.selectedIndex;
	$("#txtMonitorKeyring2").val($("#txtMonitorKeyring").val());


	var data = {
		"monitor_id":monitor_id,
		"monitor_host_name":monitor_name,
		"monitor_keyring":keyring,
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/cluster-import/auto_detect/",
		data: postData,
		dataType:"json",
		success: function(data){
				$("#txtCrushmap")[0].innerHTML += data.message;

				ctrlServerList.selectedIndex = 0;
				$("#txtMonitorKeyring").val("")
				$("#modal_wrapper").modal("hide");
				$(".messages").empty();


				if(data.status == "Failed"){
					showTip("error",data.message);
					return  false;
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



function validate(){

	if(    $("#txtCrushmap").val() == ""
	 	|| $("#txtCephConf").val() == ""){
		showTip("error","Configuration should not be empty");
		return  false;
	}

	var data = {
		"crush_map":$("#txtCrushmap")[0].value,
		"ceph_conf":$("#txtCephConf")[0].value,
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/cluster-import/validate_conf/",
		data: postData,
		dataType:"json",
		success: function(data){
				switch(data.status){
					case "OK":
						$("#btnAutoDetect").hide();
						$("#btnImportValidate").hide();
						$("#btnImportCluster").show();
						$("#divMonitorHost2").show();
						$("#divtxtMonitorKeyring2").show();
						showTip("success",data.message);

                        //Create the crushmap
						loadTree(data.crushmap);
						break;
					case "Failed":
						showTip("error",data.message);
						break;
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

function importCluster(){

	if(   $("#selMonitorHost2").val() == ""
	   || $("#txtMonitorKeyring2").val() == ""
	   || $("#txtCrushmap")[0].value  == ""
	   || $("#txtCephConf")[0].value  == ""){
		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	var monitor_host_id = $("#selMonitorHost2").val();
	var monitor_host_name = $("#selMonitorHost2")[0].options[$("#selMonitorHost2")[0].selectedIndex].text;
	var monitor_keyring = $("#txtMonitorKeyring2").val();
	var crushmap = $("#txtCrushmap").val();
	var cephconf = $("#txtCephConf").val();

	var data = {
		"monitor_host_id":monitor_host_id,
		"monitor_host_name":monitor_host_name,
		"monitor_keyring":monitor_keyring,
		"crush_map":crushmap,
		"ceph_conf":cephconf,
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/cluster-import/import_cluster/",
		data: postData,
		dataType:"json",
		success: function(data){
			switch(data.status){
				case "OK":
                    window.location.href = "/dashboard/vsm/";
					break;
				case "Failed":
					showTip("error",data.message);
					break;
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


function loadTree(data){
	CRUSHMAP = $.fn.zTree.init($("#divCrushmapTree"), setting, data);
	CRUSHMAP.expandAll(true);
}


