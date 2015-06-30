$(function(){
    //load Monitor data,5 min update
    loadMonitor();
    loadInterval();
});



function loadMonitor(){
        $.ajax({
            type: "get",
            url: "/dashboard/vsm/monitor_summary/",
            data: null,
            dataType:"json",
            success: function(data){
				// console.log(data)                
				$("#lblMonmapEpoch")[0].innerHTML = data.monmap_epoch;
                $("#lblMonitors")[0].innerHTML = data.monitors;
                $("#lblElectionEpoch")[0].innerHTML = data.election_epoch;
                $("#lblQuorum")[0].innerHTML = data.quorum;
                $("#lblUpdate")[0].innerHTML = data.update;
            }
     });
}


function loadInterval(){
	setInterval(function(){
        loadMonitor();
    },15000);

}