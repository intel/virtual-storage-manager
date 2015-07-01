$(function(){
	InitCtrlCSS();
});

function InitCtrlCSS(){
	var ctrlSelect = $("select");
	for(var i=0;i<ctrlSelect.length;i++){
		ctrlSelect[i].className = "form-control";
	}

	var ctrlText = $("input[type='text']");
	for(var i=0;i<ctrlText.length;i++){
		ctrlText[i].className = "form-control";
	}
}


$("#btnCreate").click(function(){
	var ip = $("#id_ip").val();
	var re =  /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
	if(re.test(ip) == false){
		showTip("error","The IP is not validation");
		return  false;
	}

	var data = {"ip":ip};
	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/openstackconnect/create_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/openstackconnect/";
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

});


$("#btnUpdate").click(function(){
	var id = $("#id_id").val();
	var ip = $("#id_ip").val();
	var re =  /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
	if(re.test(ip) == false){
		showTip("error","The IP is not validation");
		return  false;
	}

	var data = {"id":id,"ip":ip};
	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/openstackconnect/update_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/openstackconnect/";
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

});/**
 * Created by root on 15-7-2.
 */
