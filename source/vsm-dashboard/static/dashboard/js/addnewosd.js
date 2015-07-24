 $(function(){
 	
 })


 $("#selServer").change(function(){
	var service_id = this.value;
	var token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify({"service_id":service_id});

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/get_osd_list/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				var osdlist = data.osdlist;

				$("#tbOSDList").empty();
				$("#txtJournalDevice").val("");
				$("#txtDataDevice").val("");
				$("#txtWeight").val("");
				$("#selStorageGroup")[0].selectedIndex = 0;

				for(var i=0;i<osdlist.length;i++){
					var tbodyHtml = "";
					tbodyHtml += "<tr id='tr_'"+osdlist[i].id+" name='"+osdlist[i].name+"'>";
					tbodyHtml += "	<td class='sortable normal_column hidden'>"+osdlist[i].id+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+osdlist[i].name+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+osdlist[i].weight+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+osdlist[i].storage_group+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+osdlist[i].journal+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+osdlist[i].device+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'></td>";
					tbodyHtml += "</tr>";

					$("#tbOSDList").append(tbodyHtml);
				}

				$(".table_count")[0].innerHTML = "Displaying "+$("#tbOSDList")[0].children.length+" item";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					console.log("internal error");
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
});


$("#btnAddOSD").click(function(){
	//Check the field is should not null
	if(   $("#txtJournalDevice").val() == ""
	   || $("#txtDataDevice").val() == ""
	   || $("#txtWeight").val() == ""
	   || $("#selStorageGroup").val() == ""){

		showTip("error","The field is marked as '*' should not be empty");
		return  false;
	}

	var journal_device = $("#txtJournalDevice").val();
	var data_device = $("#txtDataDevice").val();
	var weight = $("#txtWeight").val();
	var storage_group_id =$("#selStorageGroup").val();
	var storage_group =$("#selStorageGroup")[0].options[$("#selStorageGroup")[0].selectedIndex].text;

	//Check the path
	var token = $("input[name=csrfmiddlewaretoken]").val();
	var server_id = $("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id");
	var postData_json = {"server_id":server_id
						,"journal_device_path":journal_device
						,"data_device_path":data_device}
	var postData = JSON.stringify(postData_json);
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/check_device_path/",
		data: postData,
		dataType:"json",
		success: function(data){
				//console.log(data);
				if(data.status == "OK"){
					var tbodyHtml = "";
					tbodyHtml += "<tr class='new_osd' storage_group_id="+storage_group_id+">";
					tbodyHtml += "	<td class='sortable normal_column hidden'></td>";
					tbodyHtml += "	<td class='sortable normal_column'></td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+weight+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+storage_group+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+journal_device+"</td>";
					tbodyHtml += "	<td class='sortable normal_column'>"+data_device+"</td>";
					tbodyHtml += "	<td id='option_column' class='sortable normal_column'>";
					// tbodyHtml += "		<button class='btn btn-primary'>Update</button>";
					tbodyHtml += "		<button id='btnRemoveOSD' class='btn btn-danger remove-osd' >Remove</button>";
					tbodyHtml += "	</td>";
					tbodyHtml += "</tr>";

					$("#tbOSDList").append(tbodyHtml);
					$(".table_count")[0].innerHTML = "Displaying "+$("#tbOSDList")[0].children.length+" item";
				}
				else{
					showTip("error",data.message)
				}
				

		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					console.log("internal error");
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });




});

//remove osd from the table
$(document).on("click","#btnRemoveOSD",function(){
	this.parentNode.parentNode.remove();
});


$("#btnSubmitAddOSD").click(function(){
	var server_id = $("#selServer")[0].options[$("#selServer")[0].selectedIndex].getAttribute("node-id");
	var new_osd_list = {"server_id":server_id,"osdinfo":[]};

	if($(".new_osd").length == 0){ 
		showTip("error","Please add new osd");
		return false;
	}

	$(".new_osd").each(function(){
		var osd = {
			"storage_group_id":this.attributes["storage_group_id"].value
			,"weight":this.children[2].innerHTML
			,"journal":this.children[4].innerHTML
			,"data":this.children[5].innerHTML
		};

		new_osd_list.osdinfo.push(osd);
	})


	var token = $("input[name=csrfmiddlewaretoken]").val();
	var postData = JSON.stringify(new_osd_list);
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/devices-management/add_new_osd_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500){
					console.log("internal error");
				}
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
});