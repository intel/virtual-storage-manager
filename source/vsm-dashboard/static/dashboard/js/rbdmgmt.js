
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

    if($("#tPools") && $("#tPools").length>0){
        $("#tPools>tbody>tr>.multi_select_column.hidden").each(function(){
            this.className = "multi_select_column";
        })
    }
}


$("#btnSubmit").click(function(){
    var data_list = new Array();

    $("#tPools>tbody>tr").each(function(){
        var tr_id = this.id;
        var checkbox = $("#"+tr_id).find(".table-row-multi-select");
        
        if(checkbox[0].checked){
            id = checkbox.val();
            data = {id:id};
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
