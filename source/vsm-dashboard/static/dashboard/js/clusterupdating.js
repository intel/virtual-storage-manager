$(function(){
	var search = window.location.search;
	if(search.split("=")[1]=="updating"){
		//Update the table status
	    UpdateClusterTable();
	    setInterval(function(){
	        UpdateClusterTable();
	    }, 5000);
	}
})

function UpdateClusterTable(){
	$.ajax({
        data: null,
        type: "get",
        dataType: "json",
        url: "/dashboard/vsm/clustermgmt/update_table/",
        success: function (data) {
        	var ActiveCount = 0;
        	for(var i=0;i<data.length;i++){
        		if(data[i].status == "Active"){
        			ActiveCount ++;
        		}
        		var html = "";
        		if(data[i].status == "unavailable" || data[i].status == "available" || data[i].status == "Active" || data[i].status == "Stopped"){
                    html = data[i].status;
               	}
                else{
                    html +="<td class=\"status sortable normal_column\">";
                    html +="    <div class='loading_gif'>";
                    html +="        <img src=\"/static/dashboard/img/loading.gif\">";
                    html +="    </div>";
                    html += data[i].status;
                    html +="</td>";
                }
                var tr_id = "#server_list__row__"+data[i].id;
        		$(tr_id).find(".status_up")[0].innerHTML = html;
        	}

        	console.log(ActiveCount);

        	if(ActiveCount == data.length){
        		window.location.href = "/dashboard/vsm/";
        	}


        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        headers: {
          
        },
        complete: function(){

        }
    });
}