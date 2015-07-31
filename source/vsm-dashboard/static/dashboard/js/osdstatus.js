$(function(){
   //LoadFilterTextbox
    LoadFilterTextbox();

    //load OSD data,5 min update
     LoadOSDSummary();
     LoadInterval();

     //the default page index is 1
     //LoadOSDTable(1);

     GenerateData();
})



//CheckFilterStatus
function LoadFilterTextbox(){
    var filterRow = ""
    filterRow += "  <div class='table_search client'>";
    filterRow += "      <input id='txtFilter' type='text' class='form-control' placeHolder='name,status,server,zone' />";    
    filterRow += "      <button id='btnFilter' class='btn btn-primary' onClick='FilterOSDList()'>filter</button>";
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

function GenerateData(){
    $(".deviceInfo").each(function(index){
        if(index!=0){
            var osd_id = this.parentNode.getAttribute("data-object-id");
            var html ="";
            html += "<a href='/dashboard/vsm/devices-management/?osdid="+osd_id+"'>";
            html += "   <img style='margin-left:10px;cursor:pointer' src='/static/dashboard/img/info_32.png'>";
            html += "</a>"
            this.innerHTML = html;
        }
    })

    //Get the paginate data
    if($(".page_index").length>1){
        $("#hfPageIndex").val($(".page_index")[1].innerHTML);
        $("#hfPageCount").val($(".page_count")[1].innerHTML);
        $("#hfPagerIndex").val($(".pager_index")[1].innerHTML);
        $("#hfPagerCount").val($(".pager_count")[1].innerHTML);
        var pager_index = parseInt($(".pager_index")[1].innerHTML);
        var pager_count = parseInt($(".pager_count")[1].innerHTML);
        generatePager(pager_index,pager_count);
    }
    else{
        //hide the paginate
        $("#navPagination").hide();
    }

    //get the keyword
    var queryStr = window.location.href.split("?");
    var GETs = window.location.href.split("&");
    if(GETs.length == 2){
        var keyword = GETs[1].split("=")[1];
        $("#txtFilter").val(keyword);
    }   
}

function FilterOSDList(){
    var keyword = $("#txtFilter").val();
    if(keyword==""){
        window.location.href = "/dashboard/vsm/osd-status/?pagerIndex=1";
    }
    else{
        window.location.href = "/dashboard/vsm/osd-status/?pagerIndex=1&keyword="+keyword;
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
    var pageCount =parseInt($("#hfPageCount").val());

    var pagerStart = 0;
    var pagerEnd = 0;
    switch(pagerIndex){
        case 1:
            $(".pagelink").remove();
            for(var i=PagerSize;i>0;i--){
                var keyword = $("#txtFilter").val();
                if(keyword==""){
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"'>"+i+"</a></li>";
                }
                else{
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"&keyword="+keyword+"'>"+i+"</a></li>";
                }
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
                var keyword = $("#txtFilter").val();
                if(keyword==""){
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"'>"+i+"</a></li>";
                }
                else{
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"&keyword="+keyword+"'>"+i+"</a></li>";
                }
                $("#liPrevious").after(link);
                }
            }
            break;
        case pagerCount:
            $(".pagelink").remove();
            pagerStart = (pagerIndex-1)*PagerSize;
            pagerEnd = pageCount;
            for(var i=pageCount;i>pagerStart;i--){
               var keyword = $("#txtFilter").val();
                if(keyword==""){
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"'>"+i+"</a></li>";
                }
                else{
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"&keyword="+keyword+"'>"+i+"</a></li>";
                }
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
                var keyword = $("#txtFilter").val();
                if(keyword==""){
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"'>"+i+"</a></li>";
                }
                else{
                    var link = "<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+"&keyword="+keyword+"'>"+i+"</a></li>";
                }
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
