function getFont(treeId, node) {
	return node.font ? node.font : {};
}

var CRUSHMAP = "";
var _TYPE_LIST = [];
var setting = {
	check: {
		enable: false,
		nocheckInherit: false
	},
	view: {
		showLine: true,
		fontCss: getFont,
		nameIsHTML: true,
		showIcon: false,
	},
	data: {
		simpleData: {
			enable: true
		}
	},
	callback: {
		onClick: onClickEvent
	}
};

function onClickEvent(event, treeId, treeNode, clickFlag) {
	//if the node is not the last level
	if(treeNode.type_id > _TYPE_LIST[0].id){
		console.log(treeNode);
		console.log(treeNode.children[0]);

		$("#txtParentName").val(treeNode.name);
		$("#hfParentID").val(treeNode.id);
		if(treeNode.children.length > 0){
			$("#txtTypeName").val(treeNode.type_name);
			$("#hfTypeID").val(treeNode.type_id);
		}
	}

}

$(document).ready(function(){
	loadTree();
});


function loadTree(){
	var data = {
		"crushmap":"",
		"cephconf":"",
	}

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/zonemgmt/crushmap_datasource/",
		data: postData,
		dataType:"json",
		success: function(data){
				switch(data.status){
					case "OK":
						_TYPE_LIST = data.type_list;
						CRUSHMAP = $.fn.zTree.init($("#divCrushmapTree"), setting, data.crushmap);
						CRUSHMAP.expandAll(true);
						console.log(_TYPE_LIST);
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


function addZone(){
	var zone_data = {
		zone_name:$("#txtZoneName").val(),
		parent_id:$("#hfParentID").val(),
		zone_parent_name:$("#txtParentName").val(),
		zone_parent_type:$("#txtTypeName").val(),
	}

	if(zone_data.zone_name == ""
	|| zone_data.parent_id == ""
	|| zone_data.zone_parent_name == ""
	|| zone_data.zone_parent_type == ""){
		showTip("error","All the fields should not be empty!");
		return false;
	}

	var postData = JSON.stringify(zone_data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/zonemgmt/add/",
		data: postData,
		dataType:"json",
		success: function(data){
				switch(data.status){
					case "OK":
						//refresh the tree
						loadTree();
						cleanCtrl();
						showTip("success",data.message);
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

function cleanCtrl(){
	$("#txtZoneName").val("");
	$("#hfParentID").val("");
	$("#txtParentName").val("");
	$("#hfTypeID").val("");
	$("#txtTypeName").val("");
}