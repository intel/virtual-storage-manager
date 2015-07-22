$(function(){
   
    loadObjects();
    loadPerformance();
    loadPG();
    loadCapacity();

    //load data,5 min update
    loadInterval();
});


function loadInterval() {
    setInterval(function () {
        loadObjects();
        loadPerformance();
        loadPG();
        loadCapacity();
    }, 15000);
}


function loadObjects(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/objects_summary/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblDegradedObjects")[0].innerHTML = data.degraded_objects;
            $("#lblDegradedTotal")[0].innerHTML = data.degraded_total;
            $("#lblDegradedRatio")[0].innerHTML = data.degraded_ratio;
            $("#lblUnfoundObjects")[0].innerHTML = data.unfound_objects;
            $("#lblUnfoundTotals")[0].innerHTML = data.unfound_total;
            $("#lblUnfoundRatio")[0].innerHTML = data.unfound_ratio;
        }
    });
}

function loadPerformance(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/performance_summary/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblRead")[0].innerHTML = data.read;
            $("#lblWrite")[0].innerHTML = data.write;
            $("#lblOperation")[0].innerHTML = data.operations;
        }
    });
}

function loadPG(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/pg_summary/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblPGMapVersion")[0].innerHTML = data.pgmap_version;
            $("#lblTotalPGs")[0].innerHTML = data.total_pgs;
            $("#lblUpdate")[0].innerHTML = data.update;
        }
    });
}


function loadCapacity(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/capacity_summary/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblDataCapacityUsed")[0].innerHTML = data.data_used;
            $("#lblTotalCapacityUsed")[0].innerHTML = data.total_used;
            $("#lblCapacityAvailable")[0].innerHTML = data.available;
            $("#lblCapacityTotal")[0].innerHTML = data.total;
        }
    });
}

