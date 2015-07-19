$(function(){
   //LoadFilterTextbox
    LoadFilterTextbox();

    //load OSD data,5 min update
     loadOSD();
     loadInterval();

     var trNodes = $("#server_list>tbody>tr");
     if(trNodes){
         pagerCount = parseInt(trNodes[0].children[15].innerHTML);
         pagerIndex = parseInt(trNodes[0].children[16].innerHTML);
         generatePager(pagerIndex,pagerCount);
     }
     addOptionButton();
})

//CheckFilterStatus
function LoadFilterTextbox(){
    var filterRow = ""
    filterRow += "  <div class='table_search client'>";
    filterRow += "      <input id='txtFilter' type='text' class='form-control' placeHolder='name,status,server,zone' />";    
    filterRow += "      <button id='btnFilter' class='btn btn-primary' onClick='search()'>filter</button>";
    filterRow += "  </div>";

    $(".table_actions.clearfix").append(filterRow);
}

function FilterReloadData(filterIndex){
    alert(filterIndex);
}

function SortReloadData(sortIndex){
    alert(sortIndex);
}


//load OSD data
function loadOSD(){
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


function search(){
    if($("#txtFilter").val() == ""){
        return false;
    }

    var token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        type: "post",
        url: "/dashboard/vsm/osd-status/filter_osd/",
        data: JSON.stringify({"keyword":$("#txtFilter").val()}),
        dataType:"json",
        success: function(data){
            console.log(data);
            /*
            <tr id="server_list__row__1">
                <td class="hide sortable normal_column">1</td>
                <td class="sortable osd_name normal_column">osd.0</td>
                <td class="vsm_status status_up sortable normal_column">Present</td>
                <td class="osd_state sortable normal_column">In-Up</td>
                <td class="sortable normal_column">1.0</td>
                <td class="sortable normal_column">20468</td>
                <td class="sortable normal_column">43</td>
                <td class="sortable normal_column">20424</td>
                <td class="capacity_percent_used sortable normal_column">0</td>
                <td class="sortable normal_column">node1</td>
                <td class="sortable normal_column">performance</td>
                <td class="sortable zone normal_column"></td>
                <td class="normal_column sortable span2">137days, 10 hours ago</td>
                <td class="hide normal_column sortable pageCount">1</td>
                <td class="hide pageIndex sortable normal_column">1</td>
                <td class="sortable hide pagerCount normal_column">1</td>
                <td class="pagerIndex hide sortable normal_column">1</td>
                <td class="sortable deviceInfo normal_column">
                    <a href="/dashboard/vsm/devices-management/?osdid=1">
                        <img style="margin-left:10px;cursor:pointer" src="/static/dashboard/img/info_32.png">
                    </a>
                </td>
            </tr>
            */

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


function loadInterval(){
    setInterval(function(){
        loadOSD();
    },15000);
};


function addOptionButton(){
    var trNodes = $("#server_list>tbody>tr");

    for(var i=0;i<trNodes.length;i++){
        var osd_id = trNodes[i].children[0].innerHTML;
        var tdOption = trNodes[i].children[17];
        var linkDetail = "";
        linkDetail += "<a href='/dashboard/vsm/devices-management/?osdid="+osd_id+"'>";
        linkDetail += "<img style='margin-left:10px;cursor:pointer' src='/static/dashboard/img/info_32.png' />";
        linkDetail += "</a>";
        tdOption.innerHTML =  linkDetail;
    }
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
    var pageCount =parseInt(trNodes[0].children[13].innerHTML);
    //var pageIndex = trNodes[0].children[15].innerHTML;

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
