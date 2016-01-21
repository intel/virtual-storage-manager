$(function(){
        CheckClusterExist();
})

function CheckClusterExist(){
        $.ajax({
        data: "",
        type: "get",
        dataType: "json",
        url: "/dashboard/vsm/clustermgmt/check_cluster_exist/",
        success: function (data) {
            if(data.is_exsit==false){
                $("dl.nav_accordion>dd>div>ul>li>a").each(function(){
                    var nav_name = this.innerHTML;
                    if(nav_name!="Create Cluster" && nav_name!="Import Cluster" && nav_name!="Add/Remove User"){
                        this.href = "#";
                        this.style.color = "#ccc";
                    }
                });
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        },
        complete: function(){

        }
    });
}
