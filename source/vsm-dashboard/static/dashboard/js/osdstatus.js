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

    //get the keyword (must be done first, as pagination assumes keyword is set)
    var queryStr = window.location.href.split("?");
    var GETs = window.location.href.split("&");
    if(GETs.length == 2){
        var keyword = GETs[1].split("=")[1];
        $("#txtFilter").val(keyword);
    }

    //get the paginate data
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
    var pageCount = parseInt($("#hfPageCount").val());
    var pageIndex = parseInt($("#hfPageIndex").val());

    var pagerStart = 0;
    var pagerEnd = 0;
    switch(pagerIndex){
        case 1:
            // always disable previous pager link on first page
            $("#liPrevious")[0].className = "disabled";
            $("#linkPrevious").removeAttr('href');
            $("#linkPrevious").unbind("click");

            //if pageCount > PagerSize enable the next link ...
            if (pageCount>PagerSize){
                updatePageLinks(pageIndex,0,PagerSize);

                // enable next pager link
                $("#liNext")[0].className = "";
                $("#linkNext").unbind("click").click(function(){
                     nextPager(pageIndex);
                });
            } else {    //... else disable it
                updatePageLinks(pageIndex,0,pageCount);

                // disable next pager link
                $("#liNext")[0].className = "disabled";
                $("#linkNext").removeAttr('href');
                $("#linkNext").unbind("click");
            }
            break;
        case pagerCount:
            updatePageLinks(pageIndex,(pagerIndex-1)*PagerSize,pageCount);

            // disable next link
            $("#liNext")[0].className = "disabled";
            $("#linkNext").removeAttr('href');
            $("#linkNext").unbind('click');

            // enable previous link
            $("#liPrevious")[0].className = "";
            $("#linkPrevious").unbind("click").click(function(){
                 previousPager(pageIndex);
            });
            break;
        default:
            pagerStart = (pagerIndex-1)*PagerSize;
            updatePageLinks(pageIndex,pagerStart,pagerStart+PagerSize);

            // enable both next and previous links
            $("#liNext")[0].className = "";
            $("#liPrevious")[0].className = "";
            $("#linkNext").unbind('click').click(function(){
                 nextPager(pageIndex);
            });
            $("#linkPrevious").unbind("click").click(function(){
                 previousPager(pageIndex);
            });
            break;
    }    
}

function updatePageLinks(pageIndex,pagerStart,pagerEnd){
    $(".pagelink").remove();
    for(var i=pagerEnd;i>pagerStart;i--){
        var classText = "";
        if(i==pageIndex){
            classText += " class='linkDisabled'";
        }
        var keyword = $("#txtFilter").val();
        var keywordText = "";
        if(keyword != ""){
            keywordText = "&keyword="+keyword;
        }
        $("#liPrevious").after("<li class='pagelink'><a href='/dashboard/vsm/osd-status/?pagerIndex="+i+keywordText+"'"+classText+">"+i+"</a></li>");
    }
}
