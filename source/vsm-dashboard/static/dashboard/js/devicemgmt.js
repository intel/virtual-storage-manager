$(function(){
	//remove the splash from this module
	$("script[src='/static/dashboard/js/vsm.spin.js']").remove();


    //add the smart info icon
    addInfoNode();

    //Init the dialog
    InitDialog();
})



function InitDialog(){
	var dialogTitle = "Device Status";
 	var dialogContent = $("#divOSDInfo")[0].innerHTML;
 	var modal = GenerateDialog(dialogTitle,dialogContent,true,"OK");
 	$("#divOSDInfo").remove();
}


function addInfoNode(){

	var htmlDeviceIcon = "<img id='imgOSDDialog' onClick='getStateData({0},\"data\")'  src='/static/dashboard/img/{1}' />";
	var htmlJorunalDeviceIcon = "<img id='imgOSDDialog' onClick='getStateData({0},\"jorunal\")'  src='/static/dashboard/img/info_health.png' />"

    var trNodes = $("#osds>tbody>tr");

    for(var i=0;i<trNodes.length;i++){
        var osd_id = trNodes[i].children[0].children[0].value;
        var tdDataDevice = trNodes[i].children[9];
        var tdCapacity = trNodes[i].children[17];
        var tdJorunalDevice = trNodes[i].children[14];
        var tdOSDCapcityStatus = trNodes[i].children[16];
        
        //show device status
        var iconDeviceStatus = "info_health.png";

        //show osd capctiy status
        var iconOSDCapcityStatus = "osd_normal.png";
        switch(tdOSDCapcityStatus.innerHTML){
        	case "0":
        		iconOSDCapcityStatus = "osd_normal.png";
        		break;
        	case "1":
        		iconOSDCapcityStatus = "osd_near_full.png";
        		break;
        	case "2":
        		iconOSDCapcityStatus = "osd_full.png";
        		break;
        }

        tdDataDevice.innerHTML =   htmlDeviceIcon.replace("{0}",osd_id).replace("{0}",osd_id).replace("{1}",iconDeviceStatus);
        tdJorunalDevice.innerHTML = htmlJorunalDeviceIcon.replace("{0}",osd_id);

        //show capactiy values
        var total_capacity = trNodes[i].children[10].innerHTML;
        var used_capacity = trNodes[i].children[11].innerHTML;
        var available_capacity = trNodes[i].children[12].innerHTML;
        var html_capacity = "";
        	html_capacity += "<span class=\"vsm-label-90\">Used:</span>";
        	html_capacity += "<span class=\"vsm-label-90\">"+used_capacity+"(MB)</span>";
			html_capacity += "<br />";
			html_capacity += "<span class=\"vsm-label-90\">Available:</span>";
        	html_capacity += "<span class=\"vsm-label-90\">"+available_capacity+"(MB)</span>";
			html_capacity += "<br />";
			html_capacity += "<span class=\"vsm-label-90\">Total:</span>";
        	html_capacity += "<span class=\"vsm-label-90\">"+total_capacity+"(MB)</span>";
			html_capacity += "<br />";

        tdCapacity.innerHTML =   GenerateOSDStatusIcon(iconOSDCapcityStatus,'Capacity values',html_capacity);

    }

    //register the popover
    $("a[data-toggle=popover]").popover();
}

function GenerateOSDStatusIcon(img_status,popover_title,popover_content){
	var htmlOSDStatusIcon = "";
		htmlOSDStatusIcon += "<a class='img_popover' tabindex='0' ";
		htmlOSDStatusIcon += " role='button' ";
		htmlOSDStatusIcon += " data-toggle='popover' ";
		htmlOSDStatusIcon += " data-container='body' ";
		htmlOSDStatusIcon += " data-placement='bottom' ";
		htmlOSDStatusIcon += " data-trigger='click' ";
		htmlOSDStatusIcon += " data-html='true' ";
		htmlOSDStatusIcon += " onblur='HidePopover()' ";
		htmlOSDStatusIcon += " title='"+popover_title+"' ";
		htmlOSDStatusIcon += " data-content='"+popover_content+"' >";
		htmlOSDStatusIcon += "<img class='imgOSDStatus' src='/static/dashboard/img/"+img_status+"' />"
		htmlOSDStatusIcon += "</a>";
	return htmlOSDStatusIcon;
}

function HidePopover(){
	console.log("hide popover");
	$(".popover").popover("hide");
}


function getStateData(osd_id,device_tag){
	$("#modal_wrapper").modal("show");
	$("#btnDialogCancel").hide();
    $("#divSmartInfoContainer").hide();
    $("#tSmartInfo>tbody").empty();


	//get the device path
	var device_path = "--";
	switch(device_tag){
		case 'data':
			device_path = $("#osds__row__"+osd_id)[0].children[8].innerHTML;
			break;
		case 'jorunal':
			device_path = $("#osds__row__"+osd_id)[0].children[13].innerHTML;
			break;
	}
	$("#lblDevicePath")[0].innerHTML = device_path;
	

	$("#btnDialogSubmit").bind("click",function(){
		$("#lblDevicePath")[0].innerHTML = "--";
		$("#lblStatus")[0].innerHTML = "--";
		$("#lblFamily")[0].innerHTML =  "--";
		$("#lblSeriesNumber")[0].innerHTML =  "--";
		$("#lblFirmware")[0].innerHTML =  "--";
		$("#modal_wrapper").modal("hide");
	});

	token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify({"osd_id":osd_id,"device_path":device_path});
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/get_smart_info/",
		data: postData,
		dataType:"json",
		success: function(data){
				//console.log(data);
				$("#divOSDTip").hide();
				if (data.data == ""){
					return ;
				}

	        	var basicInfo = data.basic;
				var smartInfo = data.smart;
				$("#lblStatus")[0].innerHTML = basicInfo.DriveStatus;
				$("#lblFamily")[0].innerHTML =  basicInfo.DriveFamily;
				$("#lblSeriesNumber")[0].innerHTML =  basicInfo.SerialNumber;
				$("#lblFirmware")[0].innerHTML =  basicInfo.FirmwareVersion;

                //Get smart info
                if(smartInfo.length > 0) {
                    $("#divSmartInfoContainer").show();
	                $("#tSmartInfo>tbody").empty();
                    for (var i = 0; i < smartInfo.length; i++) {
                        var smart_row = "";
                        smart_row += "<tr>";
                        smart_row += "<td>" + smartInfo[i].key + "</td>";
                        smart_row += "<td><span class='span-label'>" + smartInfo[i].value + "</span></td>";
                        smart_row += "</tr>";
                        $("#tSmartInfo>tbody").append(smart_row);
                    }
                }
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").show();
					$("#divOSDTip")[0].innerHTML = XMLHttpRequest.statusText;
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}

    });
}


//restart the osd
$("#osds__action_restart_osds").click(function(){
	var osd_id_list = {"osd_id_list":[]}

    var is_selected = false;
	$("#osds>tbody>tr").each(function(){
        if(this.children[0].children[0].checked) {
            is_selected = true;
            var osd_id = this.children[0].children[0].value;
            osd_id_list["osd_id_list"].push(osd_id);
        }
	})

    if(is_selected == false){
        showTip("warning","please select the OSD");
        return false;
    }

	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/restart_osd/",
		data: JSON.stringify(osd_id_list),
		dataType:"json",
		success: function(data){
				console.log(data);
                window.location.href= "/dashboard/vsm/devices-management/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").show();
					$("#divOSDTip")[0].innerHTML = XMLHttpRequest.statusText;
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
	return false;
});

//remove the osd
$("#osds__action_remove_osds").click(function(){
	var osd_id_list = {"osd_id_list":[]}
	
	  var is_selected = false;
	$("#osds>tbody>tr").each(function(){
        if(this.children[0].children[0].checked) {
            is_selected = true;
            var osd_id = this.children[0].children[0].value;
            osd_id_list["osd_id_list"].push(osd_id);
        }
	})

    if(is_selected == false){
        showTip("warning","please select the OSD");
        return false;
    }

	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/remove_osd/",
		data: JSON.stringify(osd_id_list),
		dataType:"json",
		success: function(data){
				console.log(data);
                window.location.href= "/dashboard/vsm/devices-management/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").show();
					$("#divOSDTip")[0].innerHTML = XMLHttpRequest.statusText;
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
	return false;
});

//remove the osd
$("#osds__action_restore_osds").click(function(){
	var osd_id_list = {"osd_id_list":[]}

    var is_selected = false;
	$("#osds>tbody>tr").each(function(){
        if(this.children[0].children[0].checked) {
            is_selected = true;
            var osd_id = this.children[0].children[0].value;
            osd_id_list["osd_id_list"].push(osd_id);
        }
	})

    if(is_selected == false){
        showTip("warning","please select the OSD");
        return false;
    }

	token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/restore_osd/",
		data: JSON.stringify(osd_id_list),
		dataType:"json",
		success: function(data){
				 console.log(data);
                 window.location.href= "/dashboard/vsm/devices-management/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").show();
					$("#divOSDTip")[0].innerHTML = XMLHttpRequest.statusText;
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
	return false;
});

