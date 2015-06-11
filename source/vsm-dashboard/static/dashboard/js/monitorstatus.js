$(function(){
    //load Monitor data,5 min update
    loadMonitor();
    loadInterval();
});



function loadMonitor(){
        $.ajax({
            type: "get",
            url: "/dashboard/vsm/monitor/",
            data: null,
            dataType:"json",
            success: function(data){
				//console.log(data)                
				$("#lblMonitorEpoch")[0].innerHTML ="Epoch:"+ data.epoch;
                $("#lblMonitorUpdate")[0].innerHTML ="Update:"+ data.update;

                var rect =null;
                $("#divMonitorRect").empty();
                for(var i=0;i<data.quorum.length;i++) {
                    if (i == data.selMonitor)
                       rect = "<div class='vsm-rect vsm-rect-monitor vsm-rect-green'>"+data.quorum[i]+"</div>";
                    else
                        rect = "<div class='vsm-rect vsm-rect-monitor'>"+data.quorum[i]+"</div>";
                    $("#divMonitorRect").append(rect);
                }
            }
     });
}


function loadInterval(){
	setInterval(function(){
        loadMonitor();
    },15000);

}