
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
    $(".present-pool-commit").live("click", function(){
        var rows_num = $(".modal-body .pool_id").length - 1;
        console.log(rows_num);
        var data_list = new Array();
        for (var i=1; i <= rows_num; i++)
        {
            row_id = $($(".modal-body .pool_id")[i]).html();
            row = $("#poolsaction__row__" + row_id);
            checked = row.find(".multi_select_column").find("input").is(":checked");
            if(checked == true)
            {
                id = row.find(".multi_select_column").find("input").val();
                console.log(id);
            }else{
                console.log("pass");
                continue;
            }

            data = {id:id};
            data_list.push(data);
            console.log(data_list);
        }
        data_list_json = JSON.stringify(data_list);
        console.log(data_list_json);
        token = $("input[name=csrfmiddlewaretoken]").val();
        modal_stack = $("#modal_wrapper .modal");
        horizon.modals.modal_spinner(gettext("Working"));
        horizon.ajax.queue({
            data: data_list_json,
            type: "post",
            dataType: "json",
            url: "/dashboard/vsm/rbdpools/pools/present",
            success: function (data) {
                //prepare refresh status
                for( x in data_list){
                    $("#pools__row__"+data_list[x]['id']).addClass("status_unknown").removeClass("status_up");
                    $("#pools__row__"+data_list[x]['id']).find(".status_up").addClass("status_unknown").removeClass("status_up");
                }
                console.log(data.status);
                horizon.alert(data.status, data.message);
                setTimeout(horizon.datatables.update, 2000);
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                horizon.alert("error", "OpenStack Access not configured!");
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
        $(this).closest('.modal').modal('hide');

    });

})(jQuery)
