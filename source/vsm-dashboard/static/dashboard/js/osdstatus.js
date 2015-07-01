$(function(){
   //LoadFilterCheckbox
    LoadFilterCheckbox();

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
function LoadFilterCheckbox(){
    var chkBoxHtml = "";
    chkBoxHtml += "<input id='chkFilter' type='checkbox'  {0} onclick='ReloadData(this.checked)' >show not up and in</input>";

    var pathname = window.location.pathname;
    var _is_checked = ""
    if(pathname.indexOf("not_up_in")>0){
        _is_checked = "checked";
    }

    $("th[class='table_header']").append(chkBoxHtml.replace("{0}",_is_checked));
}

function ReloadData(is_checked){
    if(is_checked == true)
        window.location.href = "/dashboard/vsm/osd-status/not_up_in/";
    else
        window.location.href = "/dashboard/vsm/osd-status/";
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
            if(XMLHttpRequest.status == 500)
                showTip("error","INTERNAL SERVER ERROR")
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
