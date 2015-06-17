
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


//1.Add Servers
//2.Remove Servers
//3.Add Monitors
//4.Remove Monitors
//5.Start Servers
//6.Remove Servers
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
        default:
            index = 0;
            action = "null";
            break;
    }

    var action = {"index":index
                 ,"action":action}
    return action;
}







/*

(function() {
    function mon_zone_limit(zone_list){
        for( var i=0;i<zone_list.length;i++)
        {
            delta_num = zone_list[i]["count"] - zone_list[i]["selected_count"];
            if (delta_num <= 0)
            {
                return true;
            }
        }
        return false;
    };
    function find_zone(item, zone_list){
        var index = -1;
        $.each(zone_list, function(key,val){
            if (val['zone'] == item)
            {
                index = key;
                return false;
            }
            return true;
        });
        return index;
    };
    function post_request(url_str, data_list)
    {
        data_list_json = JSON.stringify(data_list);
        console.log(data_list_json);
        token = $("input[name=csrfmiddlewaretoken]").val();
        modal_stack = $("#modal_wrapper .modal");
        horizon.modals.modal_spinner(gettext("Working"));
        
        horizon.ajax.queue({
            data: data_list_json,
            type: "post",
            dataType: "json",
            url: url_str,//"/dashboard/vsm/storageservermgmt/servers/remove",
            success: function (data) {
                //prepare refresh status
                for( x in data_list){
                    $("#server_list__row__"+data_list[x]['id']).addClass("status_unknown").removeClass("status_up");
                    $("#server_list__row__"+data_list[x]['id']).find(".status_up").addClass("status_unknown").removeClass("status_up");
                }
                console.log(data.status);
                horizon.alert(data.status, data.message);
                setTimeout(horizon.datatables.update, 2000);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                horizon.alert("error", "Network Error");
                horizon.modals.spinner.modal('hide');
            },
            headers: {
              "X-CSRFToken": token
            },
            complete: function(){
                horizon.modals.spinner.modal('hide');
                modal_stack.remove();
            }
        });
     

    }
    function post_add_servers(data_list)
    {
        url = "/dashboard/vsm/storageservermgmt/servers/add";
        post_request(url, data_list);
    };
    function post_remove_servers(data_list)
    {
        url = "/dashboard/vsm/storageservermgmt/servers/remove";
        post_request(url, data_list);
    };
    function post_stop_servers(data_list)
    {
        url = "/dashboard/vsm/storageservermgmt/servers/stop"
        post_request(url, data_list);
    };
    function post_start_servers(data_list)
    {
        url = "/dashboard/vsm/storageservermgmt/servers/start"
        post_request(url, data_list);
    };
    function jump_ok_form(data_list, topic){
        $('#messagebox_modal').modal('show');
        $('#modal_ok').show();
        $('#modal_ok').unbind("click");
        $('#modal_ok').click(function(){
            console.log("form_ok");
            $('#messagebox_modal').modal('hide');
            if(topic == "add_servers")
            {
                post_add_servers(data_list);
            }
            else if(topic == "remove_servers")
            {
                post_remove_servers(data_list);
            }
            else if(topic == "stop_servers")
            {
                post_stop_servers(data_list);
            }
            else if(topic == "start_servers")
            {
                post_start_servers(data_list);
            }
            
        });
    };
    function jump_cancel_form(){
        $('#messagebox_modal').modal('show');
        $('#modal_ok').hide();
    };
    $(".add-server-commit").live("click", function(){ 
        var pre_mon_count = 0;
        //It is not exist
        $("#server_list tbody tr").each(function(){
            if($(this).find(".monitor_tag").html() == "yes" &&
               $(this).find(".status_up").html() == "Active" )
            {
                pre_mon_count++;
            }
        });
        console.log("pre_mon_count:%d", pre_mon_count);

        var rows_num = $(".modal-body .zone").length - 1;
        console.log(rows_num);
        var data_list = new Array();
        var selected_mon_count = 0;
        for (var i=1; i <= rows_num; i++)
        {
            row_id = $($(".modal-body .server_id")[i]).html();
            row = $("#serversaction__row__" + row_id);
            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(checked == true)
            {
                id = row.find(".multi_select_column").find("input").val();
                console.log(id);
            }else{
                console.log("pass");
                continue;
            }

            zone_id = row.find(".zone").find("select").val();
            monitor = row.find(".monitor").find("input").attr("checked") ? true : false;
            storage = row.find(".storage").find("input").attr("checked") ? true : false;
            if(monitor)
            {
                selected_mon_count++;
            }
            data = {id:id, is_monitor:monitor, is_storage:storage, zone_id:zone_id};
            data_list.push(data);
            console.log(data_list);
        }
        total_mon_count = pre_mon_count + selected_mon_count;
        console.log("total_mon_count:%s", total_mon_count);

        even_warning = false;
        less_three_warning = false;

        ew_msg = "";
        ltw_msg = "";

        if(selected_mon_count != 0 &&total_mon_count % 2 == 0)
        {
            even_warning = true;
            ew_msg = "This action will result in an even number of monitors!<br/>";
        }
        if(selected_mon_count != 0 &&total_mon_count < 3)
        {
            less_three_warning = true;
            ltw_msg = "This action will result in less than three monitors!<br/>";
        }
        head_msg = "Stable cluster operation requires a minimum of three monitors and the total number of monitors to be odd.<br/>"
        if(even_warning || less_three_warning)
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ew_msg+ltw_msg);
            jump_ok_form(data_list, "add_servers");
        }
        else
        {
            post_add_servers(data_list);
        }
        $(this).closest('.modal').modal('hide');

    });

    $(".remove-server-commit").live("click", function(){ 
        console.log("text_osds");
        var _osds = $("#osds_text").text();
        console.log(_osds);
        console.log(_osds.constructor);
        osds = $.parseJSON(_osds);

        console.log("text_storage_groups");
        var _sgs = $("#storage_groups_text").text();
        console.log(_sgs);
        sgs = $.parseJSON(_sgs);
        //Init
        for(var n in sgs)
        {
            console.log("sgs:%s", sgs[n].capacity_avail);
            //sgs[n]['removed_capacity_used'] = 0;
            sgs[n]['removed_capacity_total'] = 0;
            //sgs[n]['near_full_threshold'] = 1.0;
            //sgs[n]['full_threshold'] = 10.0;
        }

        console.log("text_storage_group_threshold");
        var _thresholds = $("#storage_group_threshold_text").text();
        console.log(_thresholds);
        thresholds = $.parseJSON(_thresholds);

        var rows_num = $(".modal-body .zone").length - 1;
        console.log(rows_num);
        var data_list = new Array();
        var zone_list = new Array();
        var count_mon = 0;
        var total_mon = 0;
        for (var i=1; i <= rows_num; i++)
        {
            row_id = $($(".modal-body .server_id")[i]).html();
            row = $("#serversaction__row__" + row_id);
            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(row.find(".monitor_tag").html() == "yes")
            {
                total_mon++;
                zone = row.find(".zone").html();
                index = find_zone(zone, zone_list);
                
                if (index != -1)
                {
                    console.log("index");
                    console.log(index);
                    zone_list[index]['count'] += 1;
                } 
                else
                {
                    var zone_dict = {};
                    zone_dict['zone'] = zone;
                    zone_dict['count'] = 1;
                    zone_dict['selected_count'] = 0;
                    zone_list.push(zone_dict);
                }
            }
            if(checked == true)
            {
                id = row.find(".multi_select_column").find("input").val();
                console.log(id);
            }else{
                console.log("pass");
                continue;
            }
            //remove_monitor = row.find(".remove_monitor").find("input").attr("checked") ? true : false;
            remove_storage = row.find(".remove_storage").find("input").attr("checked") ? true : false;

            server = row.find(".server_name").html();
            console.log(server);
            for(var j in sgs)
            {
                removed_capacity_total= 0;
                for(var k in osds)
                {
                    if(osds[k]['server'] == server)
                    {
                        if(sgs[j]['storage_group_name'] == osds[k]['storage_group'])
                        {
                            removed_capacity_total += osds[k]['capacity_total'];
                        }
                    }
                }
                console.log(removed_capacity_total);
                sgs[j]['removed_capacity_total'] += removed_capacity_total;
            }
            console.log(sgs);

            if(row.find(".monitor_tag").html() == "yes")
            {
                remove_monitor = true;
                count_mon++;
                zone = row.find(".zone").html();
                index = find_zone(zone, zone_list);

                if (index != -1)
                {
                    console.log("index");
                    zone_list[index]['selected_count'] += 1;
                }
            }
            else
            {
                remove_monitor = false;
            }
            
            data = {id:id, remove_monitor:remove_monitor, remove_storage:remove_storage};
            data_list.push(data);
            console.log(data_list);
        }
        console.log(zone_list);
        console.log(sgs);

        mon_num = total_mon - count_mon;
        near_full_warning = false;
        full_warning = false;
        even_warning = false;
        less_three_warning = false;
        least_mon_zone_warning = false;
        
        fw_msg = "";
        nfw_msg = "";
        ew_msg = "";
        ltw_msg = "";
        lmzw_msg = "";
        
        for(var index in sgs)
        {
            if(sgs[index].capacity_total <= sgs[index].removed_capacity_total)
            {
                continue; 
            }
            ratio = sgs[index].capacity_used / (sgs[index].capacity_total - sgs[index].removed_capacity_total);
            console.log("ratio");
            console.log(ratio);
            if(ratio > thresholds.full_threshold / 100)
            {
                full_warning = true;
                fw_msg = "This action will result in any storage group over the storage group full threshold!<br/>";
                break; 
            }
            else if(ratio > thresholds.near_full_threshold / 100)
            {
                near_full_warning = true; 
                nfw_msg = "This action will result in any storage group over the storage group near full threshold!<br/>";
            }
        } 

        if(mon_num % 2 == 0)
        {
            even_warning = true;
            ew_msg = "This action will result in an even number of monitors!<br/>";
        }
        if(mon_num < 3)
        {
            less_three_warning = true;
            ltw_msg = "This action will result in less than three monitors!<br/>";
        }
        if(mon_zone_limit(zone_list))
        {
            least_mon_zone_warning = true;
            lmzw_msg = "This action will result in less than one monitor in some zone!<br/>";
        }

        head_msg = "Stable cluster operation requires a minimum of three monitors and the total number of monitors to be odd.<br/>"
        //$('#messagebox_modal .modal-header h3').html("Warning!");
        //if((mon_num % 2 == 0) && (mon_num < 3) && (mon_zone_limit(zone_list)))
        if(less_three_warning || full_warning) 
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ltw_msg+fw_msg+ew_msg+lmzw_msg);
            //jump_ok_form(data_list);
            jump_cancel_form();
        }
        else if(even_warning || least_mon_zone_warning || near_full_warning)
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ew_msg+lmzw_msg+nfw_msg);
            jump_ok_form(data_list, "remove_servers");
        }
        else
        {
            post_remove_servers(data_list);
        }
        $(this).closest('.modal').modal('hide');
    });

    $(".start-server-commit").live("click", function(){
        var pre_mon_count = 0;
        var count_mon = 0;
        $("#server_list tbody tr").each(function(){
            if($(this).find(".monitor_tag").html() == "yes" &&
               $(this).find(".status_up").html() == "Active" )
            {
                pre_mon_count++;
            }
        });
        console.log("pre_mon_count:%d", pre_mon_count);
        var rows_num = $(".modal-body .zone").length - 1;
        console.log(rows_num);
        var data_list = new Array();
        for (var i=1; i <= rows_num; i++)
        {
            row_id = $($(".modal-body .server_id")[i]).html();
            row = $("#serversaction__row__" + row_id);
            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(checked == true)
            {
                id = row.find(".multi_select_column").find("input").val();
                console.log(id);
            }else{
                console.log("pass");
                continue;
            }
            if(row.find(".monitor_tag").html() == "yes")
            {
                count_mon++;
            }
            data = {id: id};
            data_list.push(data);
            console.log(data_list);
        }
        mon_num = pre_mon_count + count_mon;
        even_warning = false;
        less_three_warning = false;
        least_mon_zone_warning = false;

        ew_msg = "";
        ltw_msg = "";
        lmzw_msg = "";

        if(mon_num % 2 == 0)
        {
            even_warning = true;
            ew_msg = "This action will result in an even number of monitors!<br/>";
        }
        if(mon_num < 3)
        {
            less_three_warning = true;
            ltw_msg = "This action will result in less than three monitors!<br/>";
        }
        //if(mon_zone_limit(zone_list))
        //{
        //    least_mon_zone_warning = true;
        //    lmzw_msg = "This action will result in less than one monitor in some zone!<br/>";
        //}
        head_msg = "Stable cluster operation requires a minimum of three monitors and the total number of monitors to be odd.<br/>"
        if(less_three_warning || even_warning )
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ew_msg+ltw_msg);
            jump_ok_form(data_list,"start_servers");
        }
        else
        {
            post_start_servers(data_list);
        }
        $(this).closest('.modal').modal('hide');

    });

    $(".stop-server-commit").live("click", function(){
        var rows_num = $(".modal-body .zone").length - 1;
        console.log(rows_num);
        var data_list = new Array();
        var zone_list = new Array();
        var count_mon = 0;
        var total_mon = 0;
        for (var i=1; i <= rows_num; i++)
        {
            row_id = $($(".modal-body .server_id")[i]).html();
            row = $("#serversaction__row__" + row_id);
            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(row.find(".monitor_tag").html() == "yes")
            {
                total_mon++;
                zone = row.find(".zone").html();
                index = find_zone(zone, zone_list);

                if (index != -1)
                {
                    console.log("index");
                    console.log(index);
                    zone_list[index]['count'] += 1;
                }
                else
                {
                    var zone_dict = {};
                    zone_dict['zone'] = zone;
                    zone_dict['count'] = 1;
                    zone_dict['selected_count'] = 0;
                    zone_list.push(zone_dict);
                }
            }
            if(checked == true)
            {
                id = row.find(".multi_select_column").find("input").val();
                console.log(id);
            }else{
                console.log("pass");
                continue;
            }
            remove_monitor = row.find(".remove_monitor").find("input").attr("checked") ? true : false;
            remove_storage = row.find(".remove_storage").find("input").attr("checked") ? true : false;

            if(row.find(".monitor_tag").html() == "yes")
            {
                remove_monitor = true;
                count_mon++;
                zone = row.find(".zone").html();
                index = find_zone(zone, zone_list);

                if (index != -1)
                {
                    console.log("index");
                    zone_list[index]['selected_count'] += 1;
                }
            }
            else
            {
                remove_monitor = false;
            }

            data = {id:id, remove_monitor:remove_monitor, remove_storage:remove_storage};
            data_list.push(data);
            console.log(data_list);
        }

        mon_num = total_mon - count_mon;
        even_warning = false;
        less_three_warning = false;
        least_mon_zone_warning = false;

        ew_msg = "";
        ltw_msg = "";
        lmzw_msg = "";

        if(mon_num % 2 == 0)
        {
            even_warning = true;
            ew_msg = "This action will result in an even number of monitors!<br/>";
        }
        if(mon_num < 3)
        {
            less_three_warning = true;
            ltw_msg = "This action will result in less than three monitors!<br/>";
        }
        if(mon_zone_limit(zone_list))
        {
            least_mon_zone_warning = true;
            lmzw_msg = "This action will result in less than one monitor in some zone!<br/>";
        }
        head_msg = "Stable cluster operation requires a minimum of three monitors and the total number of monitors to be odd.<br/>"
        //$('#messagebox_modal .modal-header h3').html("Warning!");
        if(less_three_warning)
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ltw_msg+ew_msg+lmzw_msg);
            jump_cancel_form();
        }
        else if(even_warning || least_mon_zone_warning)
        {
            $('#messagebox_modal .modal-body p').html(head_msg+ew_msg+lmzw_msg);
            jump_ok_form(data_list,"stop_servers");
        }
        else
        {
            post_stop_servers(data_list);
        }
        $(this).closest('.modal').modal('hide');

    });

           
})(jQuery)
*/