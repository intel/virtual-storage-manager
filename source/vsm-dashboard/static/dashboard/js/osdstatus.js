$(function(){
    var trNodes = $("#server_list>tbody>tr");
    if(trNodes){
        pagerCount = parseInt(trNodes[0].children[15].innerHTML);
        pagerIndex = parseInt(trNodes[0].children[16].innerHTML);
        generatePager(pagerIndex,pagerCount);
    } 
    
})



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
