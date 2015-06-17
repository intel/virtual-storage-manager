$(function(){
    //CheckFilterStatus
    CheckFilterStatus();

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
function CheckFilterStatus(){
    var pathname = window.location.pathname;
    if(pathname.indexOf("not_up_in")>0){
        $("#chkFilter")[0].checked = true;
    }
    else{
        $("#chkFilter")[0].checked = false;
    }

}

//Filter the OSD table data
$("#chkFilter").click(function(){
    if(this.checked)
        window.location.href = "/dashboard/vsm/osd-status/not_up_in/";
    else
        window.location.href = "/dashboard/vsm/osd-status/";
});


//load OSD data
function loadOSD(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/osd/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data);
            $("#lblOSDEpoch")[0].innerHTML ="Epoch:"+ data.epoch;
            $("#lblOSDUpdate")[0].innerHTML ="Update:"+ data.update;
            $("#divOSD_INUP")[0].innerHTML = data.in_up;
            $("#divOSD_INDOWN")[0].innerHTML = data.in_down;
            $("#divOSD_OUTUP")[0].innerHTML = data.out_up;
            $("#divOSD_OUTDOWN")[0].innerHTML = data.out_down;
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
