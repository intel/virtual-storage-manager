$(function(){
   //LoadFilterTextbox
    LoadFilterTextbox();

    //load OSD data,5 min update
     LoadOSDSummary();
     LoadInterval();

     //the default page index is 1
     LoadOSDTable(1);
})

//CheckFilterStatus
function LoadFilterTextbox(){
    var filterRow = ""
    filterRow += "  <div class='table_search client'>";
    filterRow += "      <input id='txtFilter' type='text' class='form-control' placeHolder='name,status,server,zone' />";    
    filterRow += "      <button id='btnFilter' class='btn btn-primary' onClick='LoadOSDTable(1)'>filter</button>";
    filterRow += "  </div>";

    $(".table_actions.clearfix").append(filterRow);
}

function LoadInterval(){
    setInterval(function(){
        LoadOSDSummary();
    },15000);
};

//load OSD data
function LoadOSDSummary(){
    var token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        type: "post",
        url: "/dashboard/vsm/osd_summary/",
        data: {"1":1},
        dataType:"json",
        success: function(data){
            //console.log(data);
            $("#lblEpoch")[0].innerHTML = data.epoch;
            $("#lblTotal")[0].innerHTML = data.total;
            $("#lblIn")[0].innerHTML = data.in;
            $("#lblUp")[0].innerHTML = data.up;
            $("#lblUpdate")[0].innerHTML = data.update;

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
        //    if(XMLHttpRequest.status == 500)
        //        showTip("error","INTERNAL SERVER ERROR")
        },
        headers: {
            "X-CSRFToken": token
        },
        complete: function(){

        }
    });
}


function LoadOSDTable(pageIndex){
    var token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        type: "post",
        url: "/dashboard/vsm/osd-status/get_osd_data/",
        data: JSON.stringify({"keyword":$("#txtFilter").val(),"pageIndex":pageIndex}),
        dataType:"json",
        success: function(data){
            osd_list = data.osd_list;
            $("#server_list>tbody").empty();
            for(var i=0;i<osd_list.length;i++){
                var html_tr = "";
                html_tr +="<tr id='server_list__row__"+ osd_list[i].id +"'>";
                html_tr +="<td class='sortable normal_column hide'>"+osd_list[i].id+"</td>";
                html_tr +="<td class='sortable normal_column osd_name'>"+osd_list[i].osd_name+"</td>";
                html_tr +="<td class='sortable normal_column vsm_status'>"+osd_list[i].vsm_status+"</td>";
                html_tr +="<td class='sortable normal_column osd_state'>"+osd_list[i].osd_state+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].crush_weight+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].capacity_total+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].capacity_used+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].capacity_avail+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].capacity_percent_used+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].server+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].storage_group+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].zone+"</td>";
                html_tr +="<td class='sortable normal_column'>"+osd_list[i].updated_at+"</td>";
                html_tr +="<td class='sortable normal_column hide'>"+osd_list[i].pageCount+"</td>";
                html_tr +="<td class='sortable normal_column hide'>"+osd_list[i].pageIndex+"</td>";
                html_tr +="<td class='sortable normal_column hide'>"+osd_list[i].pagerCount+"</td>";
                html_tr +="<td class='sortable normal_column hide'>"+osd_list[i].pagerIndex+"</td>";
                html_tr +="<td class='sortable normal_column'>";
                html_tr +="     <a href='/dashboard/vsm/devices-management/?osdid="+osd_list[i].id+"'>";
                html_tr +="         <img style='margin-left:10px;cursor:pointer' src='/static/dashboard/img/info_32.png'>";
                html_tr +="     </a>";
                html_tr +="</td>";

                $("#server_list>tbody").append(html_tr);
            }

            //Generate the pager
            var paginate = data.paginate;
            $("#hfPageIndex").val(paginate.page_index);
            $("#hfPageCount").val(paginate.page_count);
            $("#hfPagerIndex").val(paginate.pager_index);
            $("#hfPagerCount").val(paginate.pager_count);
            generatePager(paginate.pager_index,paginate.pager_count);

        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
        //    if(XMLHttpRequest.status == 500)
        //        showTip("error","INTERNAL SERVER ERROR")
        },
        headers: {
            "X-CSRFToken": token
        },
        complete: function(){

        }
    });
}



function nextPager(){
    var pagerCount = parseInt($("#hfPagerCount").val());
    var pagerIndex = parseInt($("#hfPagerIndex").val());
    pagerIndex ++;
    generatePager(pagerIndex,pagerCount)
}

function previousPager(){
    var pagerCount = parseInt($("#hfPagerCount").val());
    var pagerIndex = parseInt($("#hfPagerIndex").val());
    pagerIndex --;
    generatePager(pagerIndex,pagerCount)
}

var PagerSize = 10;
function generatePager(pagerIndex,pagerCount){
    //update the hidden feild value
    $("#hfPagerCount").val(pagerCount);
    $("#hfPagerIndex").val(pagerIndex); 

    var trNodes = $("#server_list>tbody>tr");
    var pageCount =parseInt($("#hfPageCount").val());

    var pagerStart = 0;
    var pagerEnd = 0;
    switch(pagerIndex){
        case 1:
            $(".pagelink").remove();
            for(var i=PagerSize;i>0;i--){
                var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pageIndex="+i+"'>"+i+"</a></li>";
                $("#liPrevious").after(link);
            }
            $("#liPrevious")[0].className = "disabled";
            $("#linkPrevious").removeAttr('href');
            $("#liNext")[0].className = "";
            //bind events
            $("#linkPrevious").unbind("click");
            $("#linkNext").bind("click",function(){
                 nextPager();
            });
            
           
            //if pageCount <= 5, the next button is disabled
            if(pageCount<=PagerSize){
                $("#liNext")[0].className = "disabled";
                $("#linkNext").removeAttr('href');
                $("#linkNext").unbind("click");
                $(".pagelink").remove();
                for(var i=pageCount;i>0;i--){
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pageIndex="+i+"'>"+i+"</a></li>";
                    $("#liPrevious").after(link);
                }
            }
            break;
        case pagerCount:
            $(".pagelink").remove();
            pagerStart = (pagerIndex-1)*PagerSize;
            pagerEnd = pageCount;
            for(var i=pageCount;i>pagerStart;i--){
                var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pageIndex="+i+"'>"+i+"</a></li>";
                $("#liPrevious").after(link);
            }
            $("#liNext")[0].className = "disabled";
            $("#linkNext").removeAttr('href');
            $("#liPrevious")[0].className = "";
            //bind event
            $("#linkNext").unbind('click');
            $("#linkPrevious").bind("click",function(){
                 previousPager();
            });
            
            break;
        default:
         $(".pagelink").remove();
            pagerStart = (pagerIndex-1)*PagerSize;
            pagerEnd = pagerStart+PagerSize;
            for(var i=pagerEnd;i>pagerStart;i--){
                var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pageIndex="+i+"'>"+i+"</a></li>";
                $("#liPrevious").after(link);
            }
            $("#liNext")[0].className = "";
            $("#liPrevious")[0].className = "";
               
            $("#linkNext").unbind("click");
            $("#linkPrevious").unbind("click");

             //bind event
            $("#linkNext").bind('click',function(){
                 nextPager();
            });
            $("#linkPrevious").bind("click",function(){
                 previousPager();
            });

            break; 
    }    
}
