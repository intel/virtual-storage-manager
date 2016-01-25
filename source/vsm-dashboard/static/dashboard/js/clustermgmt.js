
/* Copyright 2014 Intel Corporation, All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the"License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied. See the License for the
 specific language governing permissions and limitations
 under the License.
 */

(function() {
    var checkboxCell = $(".multi_select_column.hidden");
    for(var i=0;i<checkboxCell.length;i++){
        checkboxCell[i].className = "multi_select_column";
    }

    if($("#clusteraction").length>0){
       
        $("#clusteraction>tbody>tr").each(function(){
            var colIsMonitor = this.children[8];
            var value = colIsMonitor.innerHTML;
            if(value == "yes")
                colIsMonitor.innerHTML = "<input type='checkbox' class='chkIsMonitor' value='0' checked='true'>";
            else
                colIsMonitor.innerHTML = "<input type='checkbox' class='chkIsMonitor' value='0'>";
            
        })
    }
    $(".create-cluster-commit").click(function(){
        var data_list = new Array();
        var zone_id_has_monitor_list = new Array();
        var zone_id_all = new Array();


        //get the data list
        for (var i=1; i <= $("td.zone").length; i++)
        {
            var is_ok = true;
            row_id = $($(".server_id")[i]).html();
            row = $("#clusteraction__row__" + row_id);

            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(checked == true ){
                id = row.find(".server_id").html();
                is_monitor = row.find(".chkIsMonitor")[0].checked; 
                is_storage = true;
                if(row.find(".is_storage ")[0].innerText == "no")
                    is_storage = false;

                zone_id = row.find(".zone").find("select").val();
                zone_name = row.find(".zone").html();
                data = {id:id, is_monitor:is_monitor, is_storage:is_storage, zone_id:zone_id};
                data_list.push(data);
                if ($.inArray(zone_name,zone_id_all)==-1){zone_id_all.push(zone_name)}
                if(is_monitor == true){
                    if ($.inArray(zone_name,zone_id_has_monitor_list)==-1){zone_id_has_monitor_list.push(zone_name)}
                }
            }
        }
        if (zone_id_all.length>zone_id_has_monitor_list.length){
            alert("Warning:there is some zone which no monitor in!");
            return false;
        }

        data_list_json = JSON.stringify(data_list);
        token = $("input[name=csrfmiddlewaretoken]").val();
        modal_stack = $("#modal_wrapper .modal");

        $.ajax({
            data: data_list_json,
            type: "post",
            dataType: "json",
            url: "/dashboard/vsm/clustermgmt/cluster/create",
            success: function (data) {
                for( x in data_list){
                    $("#server_list__row__"+data_list[x]['id']).addClass("status_unknown").removeClass("status_up");
                    $("#server_list__row__"+data_list[x]['id']).find(".status_up").addClass("status_unknown").removeClass("status_up");
                }

                window.location.href="/dashboard/vsm/clustermgmt/?status=created";
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {

            },
            headers: {
              "X-CSRFToken": token
            },
            complete: function(){

            }
        });

    });


   
    $(".integrate-cluster-commit").click(function(){
    	var SelectedNodeCount = 0;
    	var SelectedNodeList = new Array();
    	$(".multi_select_column>input").each(function(i,item){

    		if(item.checked==true && i!=0)
    			{
    				SelectedNodeCount++;
    				SelectedNodeList.push(item.parentNode.parentNode);
    			}
    	});

    	if(SelectedNodeCount==0)
    		{
    			alert("Please select nodes.");
    			return;
    		}


    	var strSelectedNodesJSON = "[";
    	for(var i=0;i<SelectedNodeList.length;i++)
    		{
    		    if(i>0) {
                    strSelectedNodesJSON+=",";
                }
    			node = SelectedNodeList[i];
    			strSelectedNodesJSON+="{";
    			strSelectedNodesJSON+="\"id\":\""+node.children[1].innerText+"\",";
    			strSelectedNodesJSON+="\"name\":\""+node.children[2].innerText+"\",";
    			strSelectedNodesJSON+="\"mgmtIP\":\""+node.children[3].innerText+"\",";
    			strSelectedNodesJSON+="\"publicIP\":\""+node.children[4].innerText+"\",";
    			strSelectedNodesJSON+="\"clusterIP\":\""+node.children[5].innerText+"\",";
    			strSelectedNodesJSON+="\"zone\":\""+node.children[6].innerText+"\",";
    			strSelectedNodesJSON+="\"OSDs\":\""+node.children[7].innerText+"\",";
    			strSelectedNodesJSON+="\"monitor\":\""+node.children[8].innerText+"\",";
    			strSelectedNodesJSON+="\"status\":\""+node.children[11].innerText+"\"";
    			strSelectedNodesJSON+="}";
    		}
    	strSelectedNodesJSON = strSelectedNodesJSON.substring(0,strSelectedNodesJSON.length);
    	strSelectedNodesJSON+="]";

    	 token = $("input[name=csrfmiddlewaretoken]").val();
    	  $.ajax({
              data: strSelectedNodesJSON,
              type: "post",
              dataType: "json",
              url: "/dashboard/vsm/clustermgmt/cluster/integrate",
              success: function (data) {

              },
              error: function (XMLHttpRequest, textStatus, errorThrown) {

              },
              headers: {
                "X-CSRFToken": token
              },
              complete: function(){

              }
          });

    });


    var check_status = function(){
        var _check_status = function(){
            var status = null;
            var server_list = $("#server_list tbody tr");
            for(var i=0; i<server_list.length; i++){
                status =  $(server_list[i]).find("td").last().html();
                if(status !== "Active"){
                    return false;
                }
            }
            return true;
        }
        var status = _check_status();
        if(status){
            $(".sidebar").find("a").each(function(){
                $(this).attr("href", $(this).attr("href").replace("#",""));
            });
        } else {
            var href = "";
            $(".sidebar").find("a").each(function(){
                href = $(this).attr("href");
                if(href[0] != "#"){
                    $(this).attr("href", "#"+href);
                }
            });
        }
    }


    var init = function(){
        if($(".btn-create").length){
            setInterval(check_status, 1000);
        }
    }
    $(document).ready(function(){
        init();
    });
})(jQuery)





