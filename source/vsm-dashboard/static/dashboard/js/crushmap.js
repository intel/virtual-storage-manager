/**
 * Created by root on 15-11-30.
 */
function getFont(treeId, node) {
	return node.font ? node.font : {};
}

function onClickEvent(event, treeId, treeNode, clickFlag) {
	if(treeNode.type != 0){
		var take = treeNode.name;

		var is_exsit = false;
		$(".take-left").each(function(){
			if(trimStr(this.innerHTML) == trimStr(take)){
				is_exsit = true;
			}
		});

		if(is_exsit==true){
			return false;
		}

    	$("#divTakeList").append(GenerateTakeHTML(take));
    	RefreshTakeList();
	}
}

function onCheckEvent(event, treeId, treeNode){
	console.log(treeNode.take);
}


var CRUSHMAP = "";

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
		//beforeClick: beforeClick,
		onClick: onClickEvent,
		onCheck: onCheckEvent
	}
};

$(document).ready(function(){
	loadTree();
	//RefreshTakeList();
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
		url: "/dashboard/vsm/crushmap/get_crushmap/",
		data: postData,
		dataType:"json",
		success: function(data){
				switch(data.status){
					case "OK":
						console.log(data.crushmap);
						CRUSHMAP = $.fn.zTree.init($("#divCrushmapTree"), setting, data.crushmap);
						CRUSHMAP.expandAll(true);
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


var _SG_ID = -1;
function addAction(){
	_SG_ID = -1;
	resetForm();
	$("#btnAddStorageGroup").show();
}

function updateAction(id){
	_SG_ID = id;
	resetForm();

	var trID = "storage_group_list__row__"+id;
	var tr = $("#"+trID);
	var sg_take =  trimStr(tr.find(".take")[0].innerHTML);


	$("#txtName").val(trimStr(tr.find(".name")[0].innerHTML));
	$("#txtClass").val(trimStr(tr.find(".class")[0].innerHTML));
	$("#txtFriendlyName").val(trimStr(tr.find(".friendly_name")[0].innerHTML));
	$("#txtMarker")[0].value = rgb2hex(tr.find(".glyphicon")[0].style.color);

	var take_list = sg_take.split(',');
	for(var i=0;i<take_list.length;i++){
		$("#divTakeList").append(GenerateTakeHTML(trimStr(take_list[i])));
	}
	RefreshTakeList();
	//mark the tree checkbox



	$("#btnUpdateStorageGroup").show();
}

function resetForm(){
	$("#txtName").val("");
	$("#txtClass").val("");
	$("#txtFriendlyName").val("");
	$("#txtMarker").val("");
	$("#divTakeList").empty();
	$("#btnAddStorageGroup").hide();
	$("#btnUpdateStorageGroup").hide();

	$(".button.chk").each(function(){
		this.className = "button chk checkbox_false_full";
	});
}

function PostAction(action){
	//check the field
	//Check the field is should not null
	if(   $("#txtName").val() == ""
	   || $("#txtClass").val() == ""
	   || $("#txtFriendlyName").val() == ""
	   || $("#txtMarker").val() == ""){
		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	//empty the error message
	$(".messages").empty();

	var take_list = [];
	$(".take-left").each(function(){
		take_list.push(this.innerHTML);
	})

	var sg_data = {
        'storage_group': {
        	'id':_SG_ID,
            'name': $("#txtName").val(),
            'friendly_name': $("#txtFriendlyName").val(),
            'storage_class': $("#txtClass").val(),
            'marker': $("#txtMarker").val(),
            'take': take_list,
            'cluster_id':1  //bad code. the origin is 1
        }
    }

	var postData = JSON.stringify(sg_data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/crushmap/"+action+"/",
		data: postData,
		dataType:"json",
		success: function(data){
			switch(data.status){
				case "OK":
					// CRUSHMAP = $.fn.zTree.init($("#divCrushmapTree"), setting, data.crushmap);
					// CRUSHMAP.expandAll(true);
					if(action == "create"){
						AddStorageGroupHTML(sg_data.storage_group);
					}
					else{
						UpdateStorageGroupHTML(sg_data.storage_group);
					}

					break;
				case "Failed":
					showTip("error",data.msg);
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

function AddStorageGroupHTML(data){
	var html = "";
	html += "<tr id='storage_group_list__row__"+ data.id +"' class='odd' data-object-id='"+ data.id +"'>";
	html += "	<td class='multi_select_column'>";
	html += "		<input class='table-row-multi-select' type='checkbox' value='"+ data.id +"' onclick=\"MarkTree()\">";
	html += "	</td>";
	html += "	<td class='sortable normal_column name'>";
	html += 		data.name;
	html += "	</td>";
	html += "	<td class='sortable normal_column class'>";
	html += 		data.storage_class;
	html += "	</td>";
	html += "	<td class='sortable normal_column take'>";
	html += 		data.take;
	html += "	</td>";
	html += "	<td class='sortable normal_column friendly_name'>";
	html += 		data.friendly_name;
	html += "	</td>";
	html += "	<td class='sortable normal_column marker'>";
	html += "		 <span class='glyphicon glyphicon-tag' aria-hidden='true'  style=\"color:"+data.marker+"\"></span>";
	html += "	</td>";
	html += "	<td class='actions_column'>";
	html += "		<button href='' class='btn btn-default btn-primary' onclick='updateAction("+ data.id +")'>Edit</button>";
	html += "	</td>";
	html += "</tr>";

	$("#storage_group_list>tbody").append(html);
}

function UpdateStorageGroupHTML(data){
	var trID = "storage_group_list__row__"+data.id;
	var tr = $("#"+trID);

	tr.find(".name")[0].innerHTML = data.name;
	tr.find(".class")[0].innerHTML = data.storage_class;
	tr.find(".friendly_name")[0].innerHTML = data.friendly_name;
	tr.find(".glyphicon")[0].style.color = data.marker;
	tr.find(".take")[0].innerHTML = data.take;
}


function SelectAllCheckBox(obj){
	$(".table-row-multi-select").each(function(){
		this.checked = obj.checked;
	});

	MarkTree();
}

function MarkTree(){
	//clean all the marker
	$(".tree-marker").remove();

	var sg_marker_list = [];
	$("#storage_group_list>tbody>tr").each(function(){
		var checked = $("#"+this.id).find(".table-row-multi-select")[0].checked;
		if(checked == true){
			sg_marker = {
				"sg_id":$("#"+this.id).find(".table-row-multi-select")[0].value,
				"take":$("#"+this.id).find(".take")[0].innerHTML.split(','),
				"marker":rgb2hex($("#"+this.id).find(".glyphicon")[0].style.color),
			};
			sg_marker_list.push(sg_marker);
		}
	});

	console.log(sg_marker_list);

	var nodes = CRUSHMAP.transformToArray(CRUSHMAP.getNodes());
	for(var i=0; i<nodes.length; i++){
		for(var j=0;j<sg_marker_list.length;j++){
			for(var z=0;z<sg_marker_list[j].take.length;z++){
				var marker = sg_marker_list[j].marker;
				var take = sg_marker_list[j].take[z];

				if(trimStr(take) == trimStr(nodes[i].name)){
					var node_id = nodes[i].tId
					$("#"+node_id+"_span").after(GenerateTreeMarker(marker));

					$("#"+node_id+"_ul>li>a").each(function(){
						$("#"+this.id).append(GenerateTreeMarker(marker));
					})
				}
			}
		}
	}
}

function GenerateTreeMarker(color){
	var html ="";
	html += "<span class=\"tree-marker glyphicon glyphicon-tag\" aria-hidden=\"true\"  style=\"color:"+color+"\"></span>";
	return html;

}


function TakeUp(takeID){
	$("#"+takeID).insertBefore($("#"+takeID).prev());
	RefreshTakeList();
}

function TakeDown(takeID){
	$("#"+takeID).insertAfter($("#"+takeID).next());
	RefreshTakeList();
}

function TakeRemove(takeID){
	$("#"+takeID).remove();
	RefreshTakeList();
}

function RefreshTakeList(){
	var take_list = $("#divTakeList").children();
	if(take_list == null || take_list.length == 0){
		return false;
	}

	if(take_list.length == 1){
		var take_id = take_list[0].id;
		$("#"+take_id).find(".glyphicon-arrow-up")[0].style.visibility = "hidden";
		$("#"+take_id).find(".glyphicon-arrow-down")[0].style.visibility = "hidden";
	}

	//check the item
	for(var i=0;i<take_list.length;i++){
		var take_id = take_list[i].id;
		$("#"+take_id).find(".glyphicon-arrow-up")[0].style.visibility = "visible";
		$("#"+take_id).find(".glyphicon-arrow-down")[0].style.visibility = "visible";

		if(i==0){
			$("#"+take_id).find(".glyphicon-arrow-up")[0].style.visibility = "hidden";
		}
		if(i==take_list.length-1){
			$("#"+take_id).find(".glyphicon-arrow-down")[0].style.visibility = "hidden";
		}
	}
}

function GenerateTakeHTML(take){
	var html = "";
	html += "<div id='"+ take +"' class='take'>";
	html += "	<div class='take-left'>";
	html += 		take;
	html += "	</div>";
	html += "	<div class='take-right'>";
	html += "		<span class='glyphicon glyphicon-arrow-up' aria-hidden='true' onclick=\"TakeUp('"+take+"')\"></span>";
	html += "		<span class='glyphicon glyphicon-arrow-down' aria-hidden='true' onclick=\"TakeDown('"+take+"')\"></span>"
	html += "		<span class='glyphicon glyphicon-remove' aria-hidden='true' onclick=\"TakeRemove('"+take+"')\"></span>"
	html += "	</div>";
	html += "</div>";

	return html;
}


function zero_fill_hex(num, digits) {
  var s = num.toString(16);
  while (s.length < digits)
    s = "0" + s;
  return s;
}


function rgb2hex(rgb) {
  if (rgb.charAt(0) == '#')
    return rgb;

  var ds = rgb.split(/\D+/);
  var decimal = Number(ds[1]) * 65536 + Number(ds[2]) * 256 + Number(ds[3]);
  return "#" + zero_fill_hex(decimal, 6);
}

function trimStr(str){
	return str.replace(/(^\s*)|(\s*$)/g,"");
}