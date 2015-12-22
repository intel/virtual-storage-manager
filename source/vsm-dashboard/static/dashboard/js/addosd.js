var _DEVICE_LIST = []

//Load the page
$(function(){
	//Update the OSD form data
	var nodeID = $("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id");
	var data = {"service_id":nodeID};
	PostData("get_available_disks",data);

	//Update Import File Name
	$("#id_file").change(function(){
		var file_path = $("#id_file").val();
		var file_path_list = file_path.split('\\')
		$("#lblFileName")[0].innerHTML = file_path_list[file_path_list.length-1];
	});
})

function ChangeServer(obj,serverID){
	//reset the add osd form
	ResetForm();

	//Update the upload field post url
	$("#fUpload")[0].action="/dashboard/vsm/devices-management/add_new_osd/?service_id="+serverID;

	//Update the OSD list
	var data = {"service_id":serverID};
	PostData("get_osd_list",data);
	//Update the OSD form data
	var nodeID = obj.options[obj.selectedIndex].getAttribute("node-id");
	var data = {"service_id":nodeID};
	PostData("get_available_disks",data);
}

function UpdateOSDList(osd_list){
	$("#tbOSDList").empty();
	for(var i=0;i<osd_list.length;i++){
		var tbodyHtml = "";
		tbodyHtml += "<tr id='tr_'"+osd_list[i].id+" name='"+osd_list[i].name+"'>";
		tbodyHtml += "	<td class='sortable normal_column hidden'>"+osd_list[i].id+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'>"+osd_list[i].name+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'>"+osd_list[i].weight+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'>"+osd_list[i].storage_group+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'>"+osd_list[i].journal+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'>"+osd_list[i].device+"</td>";
		tbodyHtml += "	<td class='sortable normal_column'></td>";
		tbodyHtml += "</tr>";

		$("#tbOSDList").append(tbodyHtml);
	}
	$(".table_count")[0].innerHTML = "Displaying "+$("#tbOSDList")[0].children.length+" item";
}

function UpdateOSDForm(disks){
	_DEVICE_LIST = disks;
	console.log(_DEVICE_LIST);

	$("#selJournalDevice")[0].options.length = 0;
	$("#selDataDevice")[0].options.length = 0;
	for(var i=0;i<_DEVICE_LIST.length;i++){
		if(i==0){
			$("#txtJournalDevice")[0].value = _DEVICE_LIST[i].disk_name;
			$("#txtDataDevice")[0].value = _DEVICE_LIST[i].disk_name;
			//add the device info
			$(".pop-journal").remove();
			$(".pop-data").remove();
			$("#lblJournalDeviceHelp").after(GenerateIcon("journal","Journal Device Info",GenerateDeviceInfo(_DEVICE_LIST[i]))); 
			$("#lblDataDeviceHelp").after(GenerateIcon("data","Data Device Info",GenerateDeviceInfo(_DEVICE_LIST[i]))); 
			//register the popover
			$("a[data-toggle=popover]").popover();
		}

		var option1 = new Option();
		var option2 = new Option();
		option1.value =_DEVICE_LIST[i].disk_name;
		option1.text = _DEVICE_LIST[i].disk_name;
		option2.value =_DEVICE_LIST[i].disk_name;
		option2.text = _DEVICE_LIST[i].disk_name;
		$("#selJournalDevice")[0].options.add(option1);
		$("#selDataDevice")[0].options.add(option2);
	}
}

function OpenAddOSDPanel(){
	//Open the dialog
	$("#mAddOSD").modal("show");

	//Get current server node id
	var nodeID = $("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id");
	console.log("Node ID:"+nodeID);
}

function SelectDevice(type,device_name){
 	var device = GetDeviceByName(device_name);
 	var title = "";

 	$(".pop-"+type).remove();
    if(type == "journal"){
    	title = "Journal Device Info";
    	$("#txtJournalDevice").val(device_name);
    	$("#lblJournalDeviceHelp").after(GenerateIcon(type,title,GenerateDeviceInfo(device))); 
    }
    else{
    	title = "Data Device Info";
    	$("#txtDataDevice").val(device_name);
    	$("#lblDataDeviceHelp").after(GenerateIcon(type,title,GenerateDeviceInfo(device))); 
	}
	
    //register the popover
    $("a[data-toggle=popover]").popover();
 }


$("#btnAddOSD").click(function(){
	CheckOSDForm();
})

function CheckOSDForm(){
	//Check the field is should not null
	if(   $("#txtJournalDevice").val() == ""
	   || $("#txtDataDevice").val() == ""
	   || $("#txtWeight").val() == ""
	   || $("#selStorageGroup").val() == ""){

		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	//Check the device path is avaliable or not
	var path_data = {
		"server_id":$("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id"),
		"journal_device_path":$("#txtJournalDevice").val(),
		"data_device_path":$("#txtDataDevice").val()
	}

	//Post the data and check
	//if the check result is successful, add the osd
	PostData("check_device_path",path_data);
}

function AddOSD(){
	var server_id = $("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id");
	var osd_list = {"server_id":server_id,"osdinfo":[]};

	osd_list.osdinfo.push({
		"storage_group_id":$("#selStorageGroup").val(),
		"weight":$("#txtWeight").val(),
		"journal":$("#txtJournalDevice").val(),
		"data":$("#txtDataDevice").val()
	});

	//exe add osd
	PostData("add_new_osd_action",osd_list);
}

function ResetForm(){
	$("#txtJournalDevice").val("");
	$("#txtDataDevice").val("");
	$("#txtWeight").val("");
	$("#selStorageGroup")[0].selectedIndex = 0;
	$(".pop-data").remove();
	$(".pop-journal").remove();
}

function PostData(method,data){
	var token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify(data);

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/"+method+"/",
		data: postData,
		dataType:"json",
		success: function(data){
			switch(method){
				case "get_osd_list":
					UpdateOSDList(data.osdlist);
					break;
				case "get_available_disks":
					UpdateOSDForm(data);
					break;
				case "check_device_path":
					if(data.status == "OK"){
						//After check the path,then add the osd model
						AddOSD();
					}
					else{
						showTip("error",data.message);
					}
					break;
				case "add_new_osd_action":
					if(data.status == "OK"){
						window.location.href = "/dashboard/vsm/devices-management/add_new_osd/?service_id="+$("#selServer").val();
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


function GetDeviceByName(name){
 	for(var i=0;i<_DEVICE_LIST.length;i++){
 		if(name == _DEVICE_LIST[i].disk_name){
			return _DEVICE_LIST[i]; 			
 		}
 	}
 }

function GenerateDeviceInfo(data){
 	var htmlDeviceInfo = "";
    	htmlDeviceInfo += "<span class='vsm-label-60'>Name:</span>";
    	htmlDeviceInfo += "<span class='vsm-label-90'>"+data.disk_name+"</span>";
		htmlDeviceInfo += "<br />";
		htmlDeviceInfo += "<span class='vsm-label-60'>Path:</span>";
    	htmlDeviceInfo += "<span class='vsm-label-90'>"+data.by_path+"</span>";
		htmlDeviceInfo += "<br />";
		htmlDeviceInfo += "<span class='vsm-label-60'>UUID:</span>";
    	htmlDeviceInfo += "<span class='vsm-label-90'>"+data.by_uuid+"</span>";
		htmlDeviceInfo += "<br />";
	return htmlDeviceInfo;
 }

function GenerateIcon(type,popover_title,popover_content){
	var htmlOSDStatusIcon = "";
		htmlOSDStatusIcon += "<a class=\"img_popover pop-"+type+"\" tabindex='0' ";
		htmlOSDStatusIcon += " role='button' ";
		htmlOSDStatusIcon += " data-toggle='popover' ";
		htmlOSDStatusIcon += " data-container='body' ";
		htmlOSDStatusIcon += " data-placement='right' ";
		htmlOSDStatusIcon += " data-trigger='click' ";
		htmlOSDStatusIcon += " data-html='true' ";
		htmlOSDStatusIcon += " onblur='HidePopover()' ";
		htmlOSDStatusIcon += " title='"+popover_title+"' ";
		htmlOSDStatusIcon += " data-content=\""+popover_content+"\" >";
		htmlOSDStatusIcon += " <span class='glyphicon glyphicon-info-sign' aria-hidden='true'  style=\"color:#286090\"></span>"
		htmlOSDStatusIcon += "</a>";
	return htmlOSDStatusIcon;
}

function HidePopover(){
	$(".popover").popover("hide");
}

function gettext(str){
	return str;
}