$(function(){
    //add the smart info icon
    addInfoNode();

    //Init the dialog
    InitDialog();
})



function InitDialog(){
	var dialogTitle = "SmartInfo";
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
        var tdDeviceStatus = trNodes[i].children[2];
        var tdDataDevice = trNodes[i].children[9];
        var tdJorunalDevice = trNodes[i].children[14];
        var tdOSDCapcityStatus = trNodes[i].children[16];
        
        //show device status
        var iconDeviceStatus = "info_health.png";
        if (tdDeviceStatus.innerHTML != "Present"){
        	iconDeviceStatus = "info_error.png";
        }
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

        tdDataDevice.innerHTML = "";
        tdDataDevice.innerHTML +=   htmlDeviceIcon.replace("{0}",osd_id).replace("{0}",osd_id).replace("{1}",iconDeviceStatus);
        tdDataDevice.innerHTML +=   GenerateOSDStatusIcon(iconOSDCapcityStatus,'Capacity values',html_capacity);
        tdJorunalDevice.innerHTML = htmlJorunalDeviceIcon.replace("{0}",osd_id);
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
		$("#lblTotalCapacity")[0].innerHTML =  "--";
		$("#lblUsedCapacity")[0].innerHTML = "--";
		$("#lblPercentageUsed")[0].innerHTML = "--";
		$("#lblTemperature")[0].innerHTML = "--";
		$("#lblUnitRead")[0].innerHTML = "--";
		$("#lblUnitWRITE")[0].innerHTML = "--";
		$("#modal_wrapper").modal("hide");
	});

	token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify({"osd_id":osd_id,"action":"get_smart_info"});
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/devices/state",
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
				$("#lblStatus")[0].innerHTML = basicInfo.status;
				$("#lblFamily")[0].innerHTML =  basicInfo.family;
				$("#lblSeriesNumber")[0].innerHTML =  basicInfo.seriesNumber;
				$("#lblFirmware")[0].innerHTML =  basicInfo.firmware;
				$("#lblTotalCapacity")[0].innerHTML =  basicInfo.totalCapacity;
				$("#lblUsedCapacity")[0].innerHTML =  basicInfo.usedCapacity;

	            $("#lblPercentageUsed")[0].innerHTML = smartInfo.percentageUsed
				$("#lblTemperature")[0].innerHTML = smartInfo.temperature;
				$("#lblUnitRead")[0].innerHTML = smartInfo.unitRead;
				$("#lblUnitWRITE")[0].innerHTML = smartInfo.unitWRITE;
				$("#modal_wrapper").find(".modal-body")[0].innerHTML = $("#divOSDInfo")[0].innerHTML;
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

