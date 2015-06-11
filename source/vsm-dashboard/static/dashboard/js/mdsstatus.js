$(function(){
    //load MDS data,5 min update
    loadMDS();
    loadInterval();
});



function loadMDS(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/mds/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblMDSEpoch")[0].innerHTML ="Epoch:"+ data.epoch;
            $("#lblMDSUpdate")[0].innerHTML ="Update:"+ data.update;

            $("#lblMDSMetaData")[0].innerHTML = data.MetaData;
            $("#lblMDSPoolData")[0].innerHTML = data.PoolData;
            $("#divMDS_IN")[0].innerHTML = data.In;
            $("#divMDS_UP")[0].innerHTML = data.Up;
            $("#divMDS_FAILED")[0].innerHTML = data.Failed;
            $("#divMDS_STOPPED")[0].innerHTML = data.Stopped;
        }
    });
}


function loadInterval() {
    setInterval(function () {
        loadMDS();
    }, 15000);
}
