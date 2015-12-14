
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



$(function(){
    //Update the table status
    setInterval(function(){
        UpdateServerStatus();
    }, 5000);

    //Open the TableCheckbox
    OpenTableCheckbox();
});

function OpenTableCheckbox(){
    //Opent the table header
    if($(".multi_select_column.hidden.tablesorter-header.sorter-false").length>0)
        $(".multi_select_column.hidden.tablesorter-header.sorter-false")[0].className = "multi_select_column";

    if($(".multi_select_column.hidden").length>0)
        $(".multi_select_column.hidden")[0].className = "multi_select_column";

    if($("#tServers") && $("#tServers").length>0){
        $("#tServers>tbody>tr>.multi_select_column.hidden").each(function(){
            this.className = "multi_select_column";
        })
    }
}

function UpdateServerStatus(){
    $.ajax({
        data: "",
        type: "get",
        dataType: "json",
        url: "/dashboard/vsm/storageservermgmt/update_server_list/",
        success: function (servers) {
            console.log("Updated");
            var html = "";
            for(var i=0;i<servers.length;i++){
                html +="<tr id='server_list__row__"+ i +" data-display='"+servers[i].name+"' data-object-id='"+servers[i].id+"' >";
                html +="<td class=\"server_id sortable normal_column\">"+servers[i].id+"</td>";
                html +="<td class=\"sortable name normal_column\">"+servers[i].name+"</td>";
                html +="<td class=\"normal_column sortable primary_public_ip\">"+servers[i].primary_public_ip+"</td>";
                html +="<td class=\"secondary_public_ip sortable normal_column\">"+servers[i].secondary_public_ip+"</td>";
                html +="<td class=\"cluster_ip sortable normal_column\">"+servers[i].cluster_ip+"</td>";
                html +="<td class=\"ceph_ver sortable normal_column\">"+servers[i].ceph_ver+"</td>";
                html +="<td class=\"osds sortable normal_column\">"+servers[i].osds+"</td>";
                html +="<td class=\"monitor_tag sortable normal_column\">"+servers[i].is_monitor+"</td>";
                html +="<td class=\"zone sortable normal_column\">"+servers[i].zone+"</td>";
                html +="<td class=\"status sortable normal_column\">"+servers[i].status+"</td>";
                html +="</tr>";
            }
            $("#server_list>tbody")[0].innerHTML = html;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        complete: function(){

        }
    });
}
//Add Servers
$("#btnSubmit").click(function(){
    //the action including action option and action index.
    var action = CheckAction();

    var data;
    switch(action.index){
        case 1:
            data = GenerateAddServerData();
            break;
        case 2:
            data = GenerateRemoveServerData();
            break;
        case 3:
            //"add monitor" use the method as same as "add server"
            data = GenerateAddServerData(); 
            break;
        case 4:
            //"remove monitor" use the method as same as "add server"
            data = GenerateRemoveServerData();
            break;
        case 5://start server
            data = GenerateStartServerData();
            break;
        case 6://stop server
            data = GenerateRemoveServerData();
            break;
        default:
            data = "";
            //nothing to do
            return;
    }

    PostRequest(action,data);
});

//Upgrade Ceph
$("#btnCephUpgrade").click(function(){
    //invoke...
    GenerateCephUpgradeData();

})


$(".reset-status-action").click(function() {
    var token = $("input[name=csrfmiddlewaretoken]").val();
    var server_id = $(this).parent().parent().find(".server_id").html()
    console.log(server_id);
    $.ajax({
        data: "",
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/storageservermgmt/reset_status/"+ server_id,
        success: function (data) {
            console.log(data);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        headers: {
            "X-CSRFToken": token
        },
        complete: function(){

        }
    });
})


function PostRequest(action,data){
    var token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        data: data,
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/storageservermgmt/servers/"+action.action,
        success: function (data) {
            console.log(data);
            window.location.href="/dashboard/vsm/storageservermgmt/";
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        headers: {
            "X-CSRFToken": token
        },
        complete: function(){

        }
    });
}


function GenerateAddServerData(){
    var data_list = new Array();
    $("#tServers>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        
        if(checkbox[0].checked){
            id = checkbox.val();
            zone_id = $("#"+tr_id).find(".zone").find("select").val();
            monitor = $("#"+tr_id).find(".monitor").find("input")[0].checked ? true : false;
            try{
                storage = $("#"+tr_id).find(".storage").find("input")[0].checked ? true : false;
            }
            catch(e){
                storage = false;
            }


            data = {id:id, is_monitor:monitor, is_storage:storage, zone_id:zone_id};
            data_list.push(data);
        }
    })
    var data = JSON.stringify(data_list);
    return data;
}


function GenerateRemoveServerData(){
    var data_list = new Array();
    $("#tServers>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        
        if(checkbox[0].checked){
            id = checkbox.val();
            remove_monitor = $("#"+tr_id).find(".monitor_tag").html() == "yes" ? true : false;
            remove_storage = $("#"+tr_id).find(".remove_storage").find("input").attr("checked") ? true : false;
            data = {id:id, remove_monitor:remove_monitor, remove_storage:remove_storage};
            data_list.push(data);
        }
    })
    var data = JSON.stringify(data_list);
    return data;
}


function GenerateStartServerData(){
    var data_list = new Array();
    $("#tServers>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        
        if(checkbox[0].checked){
            id = checkbox.val();
            data = {id:id};
            data_list.push(data);
        }
    });
    var data = JSON.stringify(data_list);
    return data;
}

function GenerateStopServerData(){
    var data_list = new Array();
    $("#tServers>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        
        if(checkbox[0].checked){
            id = checkbox.val();
            var remove_monitor = $("#"+tr_id).find(".monitor_tag").html() == "yes" ? true:false;
            var remove_storage = $("#"+tr_id).find(".remove_monitor").find("input").attr("checked") ? true : false;
            data = {id:id, remove_monitor:remove_monitor, remove_storage:remove_storage};
            data_list.push(data);
        }
    });
    var data = JSON.stringify(data_list);
    return data;
}

function GenerateCephUpgradeData() {
    var data_list = new Array();
    var pkg_url = $("#id_package_url").val();
    var key_url = $("#id_key_url").val();
    var data = {pkg_url:pkg_url,key_url:key_url};
    data_list.push(data);
    data = JSON.stringify(data_list);

    var action = {"index":7
                 ,"action":"ceph_upgrade"}

    PostRequest(action,data);
}


//1.Add Servers
//2.Remove Servers
//3.Add Monitors
//4.Remove Monitors
//5.Start Servers
//6.Remove Servers
//7.Ceph Upgrade
//actually return the json data including postback_url 
function CheckAction(){
    var tag = $(".table_title")[0].innerHTML;
    var index = 0;
    var action  = "";
    switch(tag){
        case "Add Servers":
            index = 1;
            action = "add";
            break;
        case "Remove Servers":
            index = 2;
            action = "remove";
            break;
        case "Add Monitors":
            index = 3;
            action = "add";
            break;
        case "Remove Monitors":
            index = 4;
            action = "remove";
            break;
        case "Start Servers":
            index = 5;
            action = "start";
            break;
        case "Stop Servers":
            index = 6;
            action = "stop";
            break;
        case "Ceph Upgrade":
            index = 7;
            action = "ceph_upgrade";
            break;
        default:
            index = 0;
            action = "null";
            break;
    }

    var action = {"index":index
                 ,"action":action}
    return action;
}


