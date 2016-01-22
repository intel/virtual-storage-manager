var DEVICE_LIST = [];

var $ctrlServer = $("#selServer")[0];
var $ctrlJournalDevice = $("#txtJournalDevice")[0];
var $ctrlDataDevice = $("#txtDataDevice")[0];
var $ctrlWeight = $("#txtWeight")[0];
var $ctrlStorageGroup = $("#selStorageGroup")[0];
var $ctrOSDLocation =  $("#selOSDLocation")[0];

var $ctrlFileUpload = $("#id_file")[0];
var $ctrlFileName = $("#lblFileName")[0];

var $divFileUpload = $("#divFileUpload")[0];
var $formFileUpload = $("#fUpload")[0];


var Server = {
	Create:function(){
		var server = {};
		server.name = $ctrlServer.options[$ctrlServer.selectedIndex].text;;
		server.node_id = $ctrlServer.options[$ctrlServer.selectedIndex].getAttribute("node-id");
		server.server_id = $ctrlServer.value;
		return server;
	}
}

var StorageGroup = {
	Create:function(){
		var sg = {};
		sg.name = $ctrlStorageGroup.options[$ctrlStorageGroup.selectedIndex].text;
		sg.id = $ctrlStorageGroup.value;
		return sg;
	}
}


var Location = {
	Create:function(){
		var location = {};
		location.name = $ctrOSDLocation.options[$ctrOSDLocation.selectedIndex].text;
		location.id = $ctrOSDLocation.value;
		return location;
	}
}

$(function(){
	//Update the OSD form data
	server = Server.Create();
	PostData("get_available_disks",{"server_id":server.node_id});

	//show the warning that import the osd
	$("#id_file").click(function(){
		if(confirm("If you import the OSD from the file, all the OSD items in the below table will be removed! Will you continue to do this?")==false){
			return false;
		}
	});

	//Update Import File Name
	$("#id_file").change(function(){
		$divFileUpload.style.display = "";
		var file_path = $ctrlFileUpload.value;
		var file_path_list = file_path.split('\\')
		$ctrlFileName.innerHTML = file_path_list[file_path_list.length-1];
	});
})


function ChangeServer(){
	//reset the add osd form
	ResetForm();

	server = Server.Create();
	//Update the upload field post url
	//$formFileUpload.action="/dashboard/vsm/devices-management/add_new_osd2/?service_id="+server.server_id;
	//Update the OSD form data
	PostData("get_available_disks",{"server_id":server.node_id});
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


function CheckOSDForm(){
	//Check the field is should not null
	if(   $ctrlJournalDevice.value == ""
	   || $ctrlDataDevice.value == ""
	   || $ctrlWeight.value == ""
	   || $ctrlStorageGroup.value == ""){

		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	//Check the device path is avaliable or not
	var path_data = {
		"server_id":Server.Create().node_id,
		"journal_device_path":$ctrlJournalDevice.value,
		"data_device_path":$ctrlDataDevice.value
	}

	//Post the data and check
	//if the check result is successful, add the osd
	PostData("check_device_path",path_data);
}


function AddOSDItemInTable(){
	var server = Server.Create();
	var sg = StorageGroup.Create();
    var location = Location.Create();

	var osdHtml = "";
		osdHtml += "<tr class=\"osd-item\">";
		osdHtml += "	<td class='sortable normal_column _node_id hidden'>"+server.node_id+"</td>";
		osdHtml += "	<td class='sortable normal_column server_name'>"+server.name+"</td>";
		osdHtml += "	<td class='sortable normal_column weight'>"+$ctrlWeight.value+"</td>";
		osdHtml += "	<td class='sortable normal_column sg_name'>"+sg.name+"</td>";
        osdHtml += "	<td class='sortable normal_column location'>"+location.name+"</td>";
		osdHtml += "	<td class='sortable normal_column journal'>"+$ctrlJournalDevice.value+"</td>";
		osdHtml += "	<td class='sortable normal_column device'>"+$ctrlDataDevice.value+"</td>";
		osdHtml += "	<td class='sortable normal_column'>";
		osdHtml += "		<button class=\"btn btn-danger\" onclick=\"RemoveOSD(this)\">Remove</button>";
		osdHtml += "	</td>";
		osdHtml += "</tr>";

	//check the empty row,and then remove
	if($("#trEmptyRow").length>0){
		$("#trEmptyRow").hide();
	}

	$("#tbOSDList").append(osdHtml);
}

function RemoveOSD(obj){
	if(confirm("Are you sure that you want to remove this OSD?")){
		obj.parentNode.parentNode.remove();
		//check the table rows
		if($("#tbOSDList")[0].children.length == 1){
			$("#trEmptyRow").show();
		}

	}	
}


function AddOSD(){
	var osd_list = [];

	var OSD_Items = $(".osd-item");
    if(OSD_Items.length == 0){
        showTip("error","Please add the OSD");
        return false;
    }

	for(var i=0;i<OSD_Items.length;i++){
		var osd = {
			"server_name":OSD_Items[i].children[1].innerHTML,
			"storage_group_name":OSD_Items[i].children[3].innerHTML,
            "osd_location":OSD_Items[i].children[4].innerHTML,
			"weight":OSD_Items[i].children[2].innerHTML,
			"journal":OSD_Items[i].children[5].innerHTML,
			"data":OSD_Items[i].children[6].innerHTML
		}
		osd_list.push(osd);
	}

	var post_data = {
		"disks":[]
	}

	//generate the server data
	var server_list = []
	for(var i=0;i<osd_list.length;i++){
		var isExsitServer = false;
		for(var j=0;j<server_list.length;j++){
			if(osd_list[i].server_name == server_list[j].server_name){
				isExsitServer = true;
				break;
			}
		}
		if(isExsitServer == false){
			server = {
				"server_name":osd_list[i].server_name,
				"osdinfo":[]
			};
			server_list.push(server)
		}	
	}


	//generate the osd data
	for(var i=0;i<osd_list.length;i++){
		for(var j=0;j<server_list.length;j++){
			if(osd_list[i].server_name == server_list[j].server_name){
				var osd = {
					"storage_group_name":osd_list[i].storage_group_name,
                    "osd_location":osd_list[i].osd_location,
            		"weight":osd_list[i].weight,
            		"journal":osd_list[i].journal,
            		"data":osd_list[i].data
				}
				server_list[j].osdinfo.push(osd);
			}
		}
	}

	//exe add osd
    post_data.disks = server_list;
    console.log(post_data);
    PostData("add_new_osd_action",post_data);
}


function UpdatePopoverForm(disks){
	DEVICE_LIST = disks;

	$("#selJournalDevice")[0].options.length = 0;
	$("#selDataDevice")[0].options.length = 0;
	for(var i=0;i<DEVICE_LIST.length;i++){
		if(i==0){
			$("#txtJournalDevice")[0].value = DEVICE_LIST[i].disk_name;
			$("#txtDataDevice")[0].value = DEVICE_LIST[i].disk_name;
			//add the device info
			$(".pop-journal").remove();
			$(".pop-data").remove();
			$("#lblJournalDeviceHelp").after(GenerateIcon("journal","Journal Device Info",GenerateDeviceInfo(DEVICE_LIST[i]))); 
			$("#lblDataDeviceHelp").after(GenerateIcon("data","Data Device Info",GenerateDeviceInfo(DEVICE_LIST[i]))); 
			//register the popover
			$("a[data-toggle=popover]").popover();
		}

		var option1 = new Option();
		var option2 = new Option();
		option1.value =DEVICE_LIST[i].disk_name;
		option1.text = DEVICE_LIST[i].disk_name;
		option2.value =DEVICE_LIST[i].disk_name;
		option2.text = DEVICE_LIST[i].disk_name;
		$("#selJournalDevice")[0].options.add(option1);
		$("#selDataDevice")[0].options.add(option2);
	}
}

function ResetForm(){
	$("#txtJournalDevice").val("");
	$("#txtDataDevice").val("");
	$("#txtWeight").val("");
	$("#selStorageGroup")[0].selectedIndex = 0;
	$(".pop-data").remove();
	$(".pop-journal").remove();
}

function PostData(method,postdata){
	var token = $("input[name=csrfmiddlewaretoken]").val();
	postData = JSON.stringify(postdata);

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/"+method+"/",
		data: postData,
		dataType:"json",
		success: function(data){
			switch(method){
				case "get_available_disks":
					UpdatePopoverForm(data);
					break;
				case "check_device_path":
					if(data.status == "OK"){
						//After check the path,then add the osd model into the table
						AddOSDItemInTable();
					}
					else{
						showTip("error",data.message);
					}
					break;
				case "add_new_osd_action":
					if(data.status == "OK"){
						window.location.href = "/dashboard/vsm/devices-management/";
					}
					else{
						showTip("error",data.message);
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
 	for(var i=0;i<DEVICE_LIST.length;i++){
 		if(name == DEVICE_LIST[i].disk_name){
			return DEVICE_LIST[i]; 			
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