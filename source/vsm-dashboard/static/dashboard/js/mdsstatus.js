$(function(){
    //load MDS data,5 min update
    loadMDS();
    loadInterval();
});



function loadMDS(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/mds_summary/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblEpoch")[0].innerHTML = data.epoch;
            $("#lblUp")[0].innerHTML = data.up;
            $("#lblIn")[0].innerHTML = data.in;
            $("#lblMax")[0].innerHTML = data.max;
            $("#lblFailed")[0].innerHTML = data.failed;
            $("#lblStopped")[0].innerHTML = data.stopped;
        }
    });
}


function loadInterval() {
    setInterval(function () {
        loadMDS();
    }, 15000);
}
