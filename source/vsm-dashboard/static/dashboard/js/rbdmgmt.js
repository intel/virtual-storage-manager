
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

    //LoadSelected()
    LoadSelected();
});


function OpenTableCheckbox(){
    //Opent the table header
    if($(".multi_select_column.hidden.tablesorter-header.sorter-false").length>0)
        $(".multi_select_column.hidden.tablesorter-header.sorter-false")[0].className = "multi_select_column";

    if($(".multi_select_column.hidden").length>0)
        $(".multi_select_column.hidden")[0].className = "multi_select_column";

    if($("#tPools") && $("#tPools").length>0){
        $("#tPools>tbody>tr>.multi_select_column.hidden").each(function(){
            this.className = "multi_select_column";
        })
    }
}


function LoadSelected(){
    $.ajax({
        data: {},
        type: "get",
        dataType: "json",
        url: "/dashboard/vsm/rbdpools/get_select_data/",
        success: function (data) {
            var html = "";
            html += "<select class='cinder_volume_host' style='width:80px'>";
            for(var i=0;i<data.length;i++){
                html += "<option value='"+data[i].value+"' >"+data[i].host+"</option>";
            }
            html += "</select>";

             var ctrlSelected = $(".zone");
            for(var i=1;i<ctrlSelected.length;i++){
                ctrlSelected[i].innerHTML = html;
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 500)
                showTip("error","INTERNAL SERVER ERROR")
        },
        complete: function(){

        }
    });
}


$("#btnSubmit").click(function(){
    var data_list = new Array();

    $("#tPools>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        if(checkbox[0].checked){
            id = checkbox.val();
            var sel_index = $("#"+tr_id).find(".cinder_volume_host").val();
            cinder_volume_host = $("#"+tr_id).find(".cinder_volume_host")[0].options[sel_index].text;
            data = {id:id, cinder_volume_host:cinder_volume_host};
            data_list.push(data);
        }
    })

    if(data_list.length==0)
    {
        return false;
    }

    var data_list_json = JSON.stringify(data_list);
    token = $("input[name=csrfmiddlewaretoken]").val();

    $.ajax({
        data: data_list_json,
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/rbdpools/pools/present",
        success: function (data) {
            console.log(data);
            if(data.status == "warning")
                showTip(data.status,data.message);
            else
                window.location.href="/dashboard/vsm/rbdpools/";
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
})
