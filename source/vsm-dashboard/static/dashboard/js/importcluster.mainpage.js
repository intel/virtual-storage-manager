$(function(){
    $("#server_list>tbody>tr>td.status_up").each(function(){
        if(this.innerHTML != "available"){
            $("#server_list__action_import_cluster").hide();
        }
    });
})
