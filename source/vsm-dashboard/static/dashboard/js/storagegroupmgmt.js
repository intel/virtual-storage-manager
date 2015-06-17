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


$("#btnAddStorageGroup").click(function(){
	var data = {
        'storage_group': {
            'name': $("#id_name").val(),
            'friendly_name': $("#id_friendly_name").val(),
            'storage_class': $("#id_storage_class").val(),
            'cluster_id':1  //bad code. the origin is 1
        }
    }

	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	console.log(token)
	console.log(postData)
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/storage-group-management/create_storage_group/",
		data: postData,
		dataType:"json",
		success: function(data){
			console.log(data);
			window.location.href="/dashboard/vsm/storage-group-management/";
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			showTip("error","Some error")
		},
		headers: {
			"X-CSRFToken": token
		},
		complete: function(){

		}
    });
})
