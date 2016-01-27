/**
 * Created by root on 15-11-30.
 */
function getFont(treeId, node) {
	return node.font ? node.font : {};
}

function onClickEvent(event, treeId, treeNode, clickFlag) {
	if(treeNode.type_id != _TYPE_LIST[0].id){
		var take_id = treeNode.id.toString();
		var take_name = treeNode.name;
		var take_type_id = treeNode.type_id;

		var is_exsit = false;
		$(".take-id").each(function(){
			if(this.innerHTML.trim() == take_id.trim()){
				is_exsit = true;
			}
		});

		if(is_exsit==true){
			return false;
		}


		var type_list = GetTypeListByNode(treeNode);
    	$("#tTakeList>tbody").append(GenerateTakeHTML(take_id,take_name,"",type_list,0));
	}
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
		showIcon: false
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

$(document).ready(function(){
	loadTree();
});



function loadTree(){
	var data = {
		"crushmap":"",
		"cephconf":""
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
						_TYPE_LIST = data.type_list;
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
	_SG_ID = null;
	ResetForm();
	$("#divStorageGroupTable").hide();
	$("#divStorageGroupForm").show();
    $("#btnAddStorageGroup").show();
    $("#btnUpdateStorageGroup").hide();
}

function updateAction(id){
	_SG_ID = id;
	ResetForm();
	$("#divStorageGroupTable").hide();
	$("#divStorageGroupForm").show();
    $("#btnAddStorageGroup").hide();
    $("#btnUpdateStorageGroup").show();

	var trID = "storage_group_list__row__"+id;
	var tr = $("#"+trID);

	$("#txtName").val(tr.find(".name")[0].innerHTML.trim());
	$("#txtClass").val(tr.find(".class")[0].innerHTML.trim());
	$("#txtFriendlyName").val(tr.find(".friendly_name")[0].innerHTML.trim());
	$("#txtMarker")[0].value = rgb2hex(tr.find(".marker-circle")[0].getAttribute("fill"))


	var take_id_list = [];
	tr.find("input[type='hidden']").each(function(){
		var is_exsit_value =false;
		for(var i=0;i<take_id_list.length;i++){
			if(this.name==take_id_list[i]){
				is_exsit_value = true;
				break;
			}
		}
		if(is_exsit_value==false){
			take_id_list.push(this.name);
		}
	})

	for(var i=0;i<take_id_list.length;i++){
		var take_id = take_id_list[i];
		var take_name = $(".take-name[name=\""+take_id+"\"]").val();
		var type_name = $(".type-name[name=\""+take_id+"\"]").val();
		var take_num = $(".take-num[name=\""+take_id+"\"]").val();

		var tree_node = CRUSHMAP.getNodeByParam("id",parseInt(take_id),null);
		var type_list = GetTypeListByNode(tree_node);

		$("#tTakeList>tbody").append(GenerateTakeHTML(take_id,take_name,type_name,type_list,take_num));
	}
}



function ResetForm(){
	$("#txtName").val("");
	$("#txtClass").val("");
	$("#txtFriendlyName").val("");
	$("#txtMarker").val("");
	$("#tTakeList>tbody").empty();
}

function CancelAction(){
	$("#divStorageGroupTable").show();
	$("#divStorageGroupForm").hide();
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

	var is_value_empty = false;
	$(".text-take-num").each(function(){
		if(this.value=="" || this.value==null){
			this.style.border = "1px solid red";
			is_value_empty = true;
		}
		else{
			this.style.border = "1px solid #ccc";
		}
	});

	if(is_value_empty == true){
		return false;
	}



	//empty the error message
	$(".messages").empty();

	var take_list = [];
	$(".tr-take").each(function(){
		var trID = this.id;
		var selTakeType = $("#"+trID).find(".select-take-type")[0];
		var choose_leaf_type_id = selTakeType.value;
		var choose_leaf_type_name = selTakeType.options[selTakeType.selectedIndex].text;
		
		var choose_num = $("#"+trID).find(".text-take-num")[0].value;
		

		var take = {
			"take_id":$("#"+trID).find(".take-id")[0].innerHTML,
			"take_name":$("#"+trID).find(".take-name")[0].innerHTML,
			"choose_leaf_type_id":choose_leaf_type_id,
			"choose_leaf_type":choose_leaf_type_name,
			"choose_num":choose_num,
		}
		take_list.push(take);
	})

	var sg_data = {
        'storage_group': [{
        	'cluster_id':1,  //bad code. the origin is 1
        	'id':_SG_ID,
            'name': $("#txtName").val(),
            'friendly_name': $("#txtFriendlyName").val(),
            'storage_class': $("#txtClass").val(),
            'marker': $("#txtMarker").val(),
            'rule_info':{
            	"rule_name":$("#txtName").val(),
            	"type":"replicated",
            	"min_size":0,
            	"max_size":10,
            	"takes":take_list
            },
        },]
    }
    console.log(sg_data);
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
					if(action == "create"){
						AddStorageGroupHTML(sg_data.storage_group[0]);
					}
					else{
						UpdateStorageGroupHTML(sg_data.storage_group[0]);
					}

                    $("#divStorageGroupTable").show();
					$("#divStorageGroupForm").hide();
                    showTip("info",data.message);
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
	html += "	<td class='sortable normal_column friendly_name'>";
	html += 		data.friendly_name;
	html += "	</td>";
	html += "	<td class='sortable normal_column take'>";
	for(var i=0;i<data.rule_info.takes.length;i++){
		var displayText = data.rule_info.takes[i].take_name+"("+data.rule_info.takes[i].choose_leaf_type+","+data.rule_info.takes[i].choose_num+")";
		html += displayText;
		var take_id = data.rule_info.takes[i].take_id;
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-id\" value=\""+take_id+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-name\" value=\""+data.rule_info.takes[i].take_name+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"type-id\" value=\""+data.rule_info.takes[i].choose_leaf_type_id+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"type-name\" value=\""+data.rule_info.takes[i].choose_leaf_type+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-num\" value=\""+data.rule_info.takes[i].choose_num+"\"/>";
		html += "<br>";
	}
	html += "	</td>";
	html += "	<td class='sortable normal_column marker'>";
	html += "		<svg width=\"16\" height=\"16\">"
	html += "			<circle class=\"marker-circle\" cx=\"8\" cy=\"8\" r=\"8\" fill=\""+data.marker+"\" />"
	html += "		</svg>"

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
	tr.find(".marker-circle")[0].setAttribute("fill",data.marker);
	var html = "";
	for(var i=0;i<data.rule_info.takes.length;i++){
		var displayText = data.rule_info.takes[i].take_name+"("+data.rule_info.takes[i].choose_leaf_type+","+data.rule_info.takes[i].choose_num+")";
		html += displayText;
		var take_id = data.rule_info.takes[i].take_id;
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-id\" value=\""+take_id+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-name\" value=\""+data.rule_info.takes[i].take_name+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"type-id\" value=\""+data.rule_info.takes[i].choose_leaf_type_id+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"type-name\" value=\""+data.rule_info.takes[i].choose_leaf_type+"\"/>";
		html += "<input type=\"hidden\" name=\""+take_id+"\" class=\"take-num\" value=\""+data.rule_info.takes[i].choose_num+"\"/>";
		html += "<br>";
	}

	tr.find(".take")[0].innerHTML = html;

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

	var marker_list = [];
	$("#storage_group_list>tbody>tr").each(function(){
		var trID= "#"+this.id;
		var checked = $(trID).find(".table-row-multi-select")[0].checked;
		if(checked == true){
			//get the marker color
			var marker_color = rgb2hex($(trID).find(".marker-circle")[0].getAttribute("fill"))
			//get the take ID list
			$(trID).find(".take-id[type=\"hidden\"]").each(function(){
				marker_list.push({
					"takeID":this.value,
					"color":marker_color
				});
			});
		}
	});

	
	for(var i=0;i<marker_list.length;i++){
		var takeID = marker_list[i].takeID;
		var markerColor = marker_list[i].color;
		var treeNode = CRUSHMAP.getNodeByParam("id",parseInt(takeID),null);
		
		ALL_SUB_NODE = [];
		ALL_SUB_NODE.push(treeNode);
		GetAllSubNodes(treeNode.children);

		console.log(ALL_SUB_NODE);
		//Marker all the nodes
		for(var j=0;j<ALL_SUB_NODE.length;j++){
			var node_id = ALL_SUB_NODE[j].tId;
			$("#"+node_id+"_span").after(GenerateTreeMarker(markerColor));
		}

	}
}

function GenerateTreeMarker(color){
	var html ="";
	html += "<svg class=\"tree-marker\" width=\"16\" height=\"16\">";
	html += "	<circle class=\"marker-circle\" cx=\"8\" cy=\"8\" r=\"8\" fill=\""+color+"\" />";
	html += "</svg>";
	return html;
}


function TakeUp(takeID){
	$("#"+takeID).insertBefore($("#"+takeID).prev());
}

function TakeDown(takeID){
	$("#"+takeID).insertAfter($("#"+takeID).next());
}

function TakeRemove(takeID){
	$("#"+takeID).remove();
}

function GenerateTakeHTML(takeID,takeName,typeName,type_list,takeNum){
	var trID = "trTake_"+takeID;

	var html = "";
	html += "<tr id=\""+trID+"\" class=\"tr-take\">";
	html += "	<td class=\"take-id\" style=\"display:none\">"+takeID+"</td>";
	html += "	<td class=\"take-name\">"+takeName+"</td>";
	html += "	<td class=\"take-type\">";
	html += "		<select class=\"select-take-type form-control\">";
	for(var i=0;i<type_list.length;i++){
		if(typeName.toString() == type_list[i].name.toString()){
			html += "		<option value=\""+type_list[i].id+"\" selected=\"true\">";
		}
		else{
			html += "		<option value=\""+type_list[i].id+"\">";
		}
		html += type_list[i].name;
		html += "		</option>";
	}
	html += "		</select>";
	html += "	</td>";
	html += "	<td class=\"take-num\">";
	html += "		<input maxlength=\"10\" type=\"number\" class=\"text-take-num form-control\" placeholder=\"take number\" value=\""+takeNum+"\" />";
	html += "	</td>";
	html += "	<td class=\"take-action\">";
	html += "		<span class='glyphicon glyphicon-arrow-up' aria-hidden='true' onclick=\"TakeUp('"+trID+"')\"></span>";
	html += "		<span class='glyphicon glyphicon-arrow-down' aria-hidden='true' onclick=\"TakeDown('"+trID+"')\"></span>"
	html += "		<span class='glyphicon glyphicon-remove' aria-hidden='true' onclick=\"TakeRemove('"+trID+"')\"></span>"
	html += "	</td>";
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

String.prototype.trim = function(){
	return this.replace(/(^\s*)|(\s*$)/g,"");
}

var ALL_SUB_NODE = []
function GetAllSubNodes(children){
	for(var i=0;i<children.length;i++){
		ALL_SUB_NODE.push(children[i]);
		if(children[i].children!=null){
			GetAllSubNodes(children[i].children);
		}
	}
}

function GetTypeListByNode(node){
	//get all the sub nodes	
	ALL_SUB_NODE = [];
	GetAllSubNodes(node.children);
	var type_list = [];
	//add itself type
	type_list.push({
		"id":node.type_id,
		"name":node.type_name
	});
	//add sub node type
	for(var i=0;i<ALL_SUB_NODE.length;i++){
		//not a osd
		if(ALL_SUB_NODE[i].type_id ==_TYPE_LIST[0].id){
			continue;
		}

		var is_type_exist = false;
		for(var j=0;j<type_list.length;j++){
			if(type_list[j].id == ALL_SUB_NODE[i].type_id){
				is_type_exist = true;	
				break;
			}
		}
		if(is_type_exist==false){
			type_list.push({
				"id":ALL_SUB_NODE[i].type_id,
				"name":ALL_SUB_NODE[i].type_name
			});
		}
	}
	return type_list;
}

function ChangeName(value){
    $("#txtFriendlyName").val(value);
}

function ChangeStorageClass(value){
    $("#txtClass").val(value);
}