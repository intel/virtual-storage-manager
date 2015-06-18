$(function(){
    //add the smart info icon
    addInfoNode();
})

function addInfoNode(){

	var htmlDeviceIcon = "";
	htmlDeviceIcon += "<img id='imgOSDDialog' onClick='getStateData({0})'  src='/static/dashboard/img/{1}' />";
	htmlDeviceIcon += "<img id='imgOSDDialog'  src='/static/dashboard/img/{2}' />";

	var htmlJorunalDeviceIcon = "<img id='imgOSDDialog' onClick='getStateData({0})'  src='/static/dashboard/img/info_health.png' />"

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
        tdDataDevice.innerHTML =   htmlDeviceIcon.replace("{0}",osd_id).replace("{1}",iconDeviceStatus).replace("{2}",iconOSDCapcityStatus);
        tdJorunalDevice.innerHTML = htmlJorunalDeviceIcon.replace("{0}",osd_id);
    }
    var yep = false;
}

function getStateData(osd_id){
 	var dialogTitle = "SmartInfo";
 	var dialogContent = $("#divOSDInfo")[0].innerHTML;
 	var modal = GenerateDialog(dialogTitle,dialogContent,true,"OK");
 	modal.modal("show");
	$("#btnDialogCancel").hide();


	$("#btnDialogSubmit").bind("click",function(){
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
		modal.modal("hide");
	});



	token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify({"osd_id":osd_id,"action":"get_smart_info"});
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/devices/state",
		data: postData,
		dataType:"json",
		success: function(data){
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
				modal.find(".modal-body")[0].innerHTML = $("#divOSDInfo")[0].innerHTML;
				console.log(data);
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					$("#divOSDTip").append(XMLHttpRequest.statusText);
					$("#divOSDTip").show();
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}

    });
}

