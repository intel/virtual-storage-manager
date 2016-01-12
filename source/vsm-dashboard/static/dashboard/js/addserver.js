var $ctrlServerList = $("#selServer")[0]
var $ctrlZoneList = $("#selZone")[0]

var SERVER_LIST = new Array();

//Loading
$(function(){
	//Init data
	var postdata = {"name":$ctrlServerList.value}
	PostData("get_server_by_name",postdata);
})

function ChangeServer(obj){
	var postdata = {"name":obj.value}
	PostData("get_server_by_name",postdata);
}

//function ChangeZone(selectedIndex){
//	$(".ctrl-zone").each(function(){
//		this.selectedIndex = selectedIndex;
//	})
//}

function UpdateZoneList(zone_id){
	for(var i=0;i<$ctrlZoneList.options.length;i++){
		if($ctrlZoneList.options[i].value == zone_id.toString()){
			$ctrlZoneList.selectedIndex = $ctrlZoneList.options[i].index;
		}
	}
}

function UpdateOSDTable(osd_list){
	//clear all the osd table
	$("#tbOSDList").empty();

	var html = "";
	if(osd_list.length == 0){
		html += "<tr id=\"trEmptyRow\" class=\"odd empty\">";
		html += "	<td colspan=\"6\">No items to display.</td>";
		html += "</tr>";
	}
	else{
		for(var i=0;i<osd_list.length;i++){
			html += "<tr id=\"tr_osd_"+osd_list[i].osd_id+"\" class=\"osd-item\">";
			html += "	<td class=\"sortable normal_column osd_id hidden\">"+osd_list[i].osd_id+"</td>";
			html += "	<td class=\"sortable normal_column osd_name \">"+osd_list[i].osd_name+"</td>";
			html += "	<td class=\"sortable normal_column zone \">"+CtrlZone(osd_list[i].zone)+"</td>";
			html += "	<td class=\"sortable normal_column weight \">"+CtrlWeight(osd_list[i].weight)+"</td>";
			html += "	<td class=\"sortable normal_column journal \">"+osd_list[i].journal+"</td>";
			html += "	<td class=\"sortable normal_column data \">"+osd_list[i].data+"</td>";
			html += "</tr>";
		}
	}
	$("#tbOSDList").html(html);
}

function AddServer(){
	var server_id = $("#hfServerID").val();
	for(var i=0;i<SERVER_LIST.length;i++){
		if(server_id == SERVER_LIST[i].id){
			SERVER_LIST.remove(i);
		}
	}

	var is_monitor = true;
	if($("#hfIsMonitor").val() == "yes")
		is_monitor = true;
	else
		is_monitor = false;

	var is_storage = true;
	if($("#hfIsStorage").val() == "yes")
		is_storage = true;
	else
		is_storage = false;

	var server = {
		id:$("#hfServerID").val(),
		name:$ctrlServerList.value,
		IP:$("#hfServerIP").val(),
		zone_id:$ctrlZoneList.value,
		is_monitor:is_monitor,
		is_storage:is_storage,
		osd_locations:[]
	}

	//add the osd list
	$(".osd-item").each(function(){
		var tr = $("#"+this.id);
		var ctrlLocation = tr.find(".ctrl-zone")[0];
        var location_name = ctrlLocation.options[ctrlLocation.selectedIndex].text;
        if(location_name == "--"){
            location_name = "";
        }
		osd = {
			id:tr.find(".osd_id")[0].innerHTML,
			location:location_name,
			weight:tr.find(".ctrl-weight")[0].value,
		}
		server.osd_locations.push(osd);
	})

    if(server.osd_locations.length>0){
        server.is_storage = true;
    }

	//Update the Server Table Row
	UpdateServerTable(server);

	SERVER_LIST.push(server);
}

function UpdateServerTable(server){
	//check the server is exsit
	var trID = "tr_server_"+server.id;
	if($("#"+trID).length > 0){
		$("#"+trID).remove();
	}

	var html = "";
	html += "<tr id=\""+trID+"\" class=\"server-item\">";
	html += "	<td class=\"sortable normal_column server_id hidden\">"+server.id+"</td>";
	html += "	<td class=\"sortable normal_column server_name \">"+server.name+"</td>";
	html += "	<td class=\"sortable normal_column address \">"+server.IP+"</td>";
	html += "	<td class=\"sortable normal_column is_monitor \">"+CtrlMonitor(server.id,server.is_monitor)+"</td>";
	html += "	<td class=\"sortable normal_column is_storage hidden \">"+server.is_storage+"</td>";
	html += "	<td class=\"sortable normal_column osd_count \">"+server.osd_locations.length+"</td>";
	html += "	<td class=\"sortable normal_column zone_info \">"+ZoneInfo(server.osd_locations)+"</td>";
	html += "	<td class=\"sortable normal_column \">";
	html += "		<button class=\"btn btn-danger\" onclick=\"RemoveServer('"+trID+"')\">Remove</button>";
	html += "	 </td>"
	html += "</tr>";

	$("#tbServerList").append(html);

	//check the empty row
	CheckServerTableEmptyRow();
}

function RemoveServer(trID){
	if(confirm("Are you sure to remove this server?")){
		$("#"+trID).remove();
		//check the empty row
		CheckServerTableEmptyRow();
	}
}

function SubmitAddServer(){
	PostData("add_server",SERVER_LIST);
}

function ChangeIsMonitor(obj,server_id){
	for(var i=0;i<SERVER_LIST.length;i++){
		if(SERVER_LIST[i].id == server_id){
			if(obj.checked)
				SERVER_LIST[i].is_monitor = true;
			else
				SERVER_LIST[i].is_monitor = false;

			console.log(SERVER_LIST[i]);
		}
	}
}

function PostData(method,postdata){
	var token = $("input[name=csrfmiddlewaretoken]").val();
	postData = JSON.stringify(postdata);

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/storageservermgmt/"+method+"/",
		data: postData,
		dataType:"json",
		success: function(data){
			switch(method){
				case "get_server_by_name":
					$("#hfIsMonitor").val(data.is_monitor);
					$("#hfIsStorage").val(data.is_storage);
					$("#hfServerIP").val(data.IP);
					$("#hfServerID").val(data.id);
					UpdateZoneList(data.zone_id);
					UpdateOSDTable(data.osd_list);
					break
				case "add_server":
					console.log(data);
					if(data.status == "OK"){
						window.location.href = "/dashboard/vsm/storageservermgmt/";
					}
					break;
			}
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			if(XMLHttpRequest.status == 500){
				showTip("error","Internal Error");
			}
		},
		headers: {
			"X-CSRFToken": token
		},
		complete: function(){

		}
    });
}


function CtrlZone(zone_name){
	var zone_options = $("#selOSDZone")[0].options;
	var html = "";
	html += "<select class=\"form-control ctrl-zone\">";
	for(var i=0; i<zone_options.length;i++){
		if(zone_options[i].text == zone_name){
			html += "<option value=\""+zone_options[i].value+"\" selected=\"selected\">";
		}
		else{
			html += "<option value=\""+zone_options[i].value+"\">";
		}

		html += zone_options[i].text;
		html += "</option>";
	}
	html += "</select>";

	return html;
}


function CtrlWeight(value){
	var html = "";
	html += "<input type=\"text\" class=\"form-control ctrl-weight\" value=\""+value+"\" />";
	return html;
}


function CtrlMonitor(server_id,checked){
	var html = "";
	var checked_tag = "";
	html += "<input type=\"checkbox\" class=\"ctrl-monitor\" onclick=\"ChangeIsMonitor(this,'"+server_id+"')\" ";
	if(checked == true)
		html += "checked=\"checked\"";
	html+="/>";
	return html;
}

function ZoneInfo(osd_list){
	var zone_list = new Array();

	//Generate the zone list
	for(var i=0;i<osd_list.length;i++){
		var is_zone_exsit = false;
		for(var j=0;j<zone_list.length;j++){
			if(osd_list[i].location == zone_list[j].name){
				is_zone_exsit = true;
				break;
			}
		}
		if(is_zone_exsit == false){
			zone = {
				name:osd_list[i].location,
				osd_list:[]
			}
			zone_list.push(zone);
		}
	}
	// //get the osd in different zone
	for(var i=0;i<osd_list.length;i++){
		for(var j=0;j<zone_list.length;j++){
			if(osd_list[i].location == zone_list[j].name){
				var osd = {
					id:osd_list[i].id,
					weight:osd_list[i].weight,
				}
				zone_list[j].osd_list.push(osd)
			}
		}
	}

	//generate the zone info.
	var html = "";
	for(var i=0;i<zone_list.length;i++){
		html += "<span class=\"zone-name\">";
		html += zone_list[i].name;
		html += ":</span>";
		html += "<span class=\"zone-count\">";
		html += zone_list[i].osd_list.length;
		html += "</span>";
		html += "<br/>"
	}

	return html;
}

function CheckServerTableEmptyRow(){
	if($(".server-item").length == 0)
		$("#trServerEmptyRow").show();
	else
		$("#trServerEmptyRow").hide();
}

/*remove the array element*/
Array.prototype.remove = function(dx) {
	if(isNaN(dx) || dx>this.length){return false}

	for(var i=0,n=0;i<this.length;i++){
		if(this[i]!=this[dx]){
			this[n++] = this[i]
		}
	}
	this.length -=1;
};
