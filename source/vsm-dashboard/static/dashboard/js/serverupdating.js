$(function() {
    //check the status
    CheckTheStatus();

    //Update the table status
    setInterval(function(){
        UpdateServerStatus();
    }, 5000);
})

function CheckTheStatus(){
    $("td.status").each(function(){
        if(this.innerHTML != "unavailable"  && this.innerHTML != "available" && this.innerHTML != "Active" && this.innerHTML != "Stopped"){
            var html = "";
            html +="<div class='loading_gif'>";
            html +="    <img src=\"/static/dashboard/img/loading.gif\">";
            html +="</div>";
            html +=this.innerHTML;
            this.innerHTML = html;
        }
    });
}

function UpdateServerStatus(){
    $.ajax({
        data: "",
        type: "get",
        dataType: "json",
        url: "/dashboard/vsm/storageservermgmt/update_server_list/",
        success: function (servers) {
            var html = "";
            if(servers.length == 0){
                html += "<tr class=\"odd empty\">";
                html += "<td colspan=\"10\">No items to display.</td>";
                html += "</tr>";
            }
            else{
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
                    if(servers[i].status == "unavailable" || servers[i].status == "available" || servers[i].status == "Active" || servers[i].status == "Stopped"){
                        html +="<td class=\"status sortable normal_column\">"+servers[i].status+"</td>";
                    }
                    else
                    {
                        html +="<td class=\"status sortable normal_column\">";
                        html +="    <div class='loading_gif'>";
                        html +="        <img src=\"/static/dashboard/img/loading.gif\">";
                        html +="    </div>";
                        html +=servers[i].status;
                        html +="</td>";
                    }
                    html +="</tr>";
                }
            }
            $("#server_list>tbody")[0].innerHTML = html;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        },
        complete: function(){

        }
    });
}