$(function(){
	$("#id_file").change(function(){
		var file_path = $("#id_file").val();
		var file_path_list = file_path.split('\\')
		$("#lblFileName")[0].innerHTML = file_path_list[file_path_list.length-1];
	});
});


$("#btnImport").click(function(){
	console.log("import osd");
	var OSD_list = [];
	$("#osd_list>tbody>tr").each(function(){
		var osd = {
            "server_name":this.children[0].innerHTML,
            "storage_group_id":this.children[1].innerHTML,
            "weight":this.children[2].innerHTML,
            "journal":this.children[3].innerHTML,
            "data":this.children[4].innerHTML,
        }
        OSD_list.push(osd);
	});

	var post_data = {
		"disks":[]
	}

	//generate the server data
	var server_list = []
	for(var i=0;i<OSD_list.length;i++){
		var isExsitServer = false;
		for(var j=0;j<server_list.length;j++){
			if(OSD_list[i].server_name == server_list[j].server_name){
				isExsitServer = true;
				break;
			}
		}
		if(isExsitServer == false){
			server = {
				"server_name":OSD_list[i].server_name,
				"osdinfo":[]
			};
			server_list.push(server)
		}	
	}


	//generate the osd data
	for(var i=0;i<OSD_list.length;i++){
		for(var j=0;j<server_list.length;j++){
			if(OSD_list[i].server_name == server_list[j].server_name){
				var osd = {
					"storage_group_id":OSD_list[i].storage_group_id,
            		"weight":OSD_list[i].weight,
            		"journal":OSD_list[i].journal,
            		"data":OSD_list[i].data,
				}
				 server_list[j].osdinfo.push(osd);
			}
		}
	}
	//generate the post data
	post_data.disks = server_list;
	
	token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify(post_data);
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/batch_import/",
		data: postData,
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
})