/**
 * Created by shouanxx on 3/26/2015.
 */
require.config({
    paths:{
        echarts:"../../static/lib/echarts",
    }
});

var cClusterGague;
var cIOPs;
var cLatency;
var cBandwidth;
var cCPU;
var IOPs_EndTime = "";
var Latency_EndTime = "";
var BandWidth_EndTime = "";
var CPU_EndTime = "";
var token = $("input[name=csrfmiddlewaretoken]").val();
require(
    [
        'echarts',
        'echarts/chart/line',
        'echarts/chart/bar',
        'echarts/chart/pie',
        'echarts/chart/gauge'
    ],
    function(ec){
        cClusterGague = ec.init(document.getElementById('divClusterGauge'));
        //init the cluster gague when page loaded...
        cClusterGague.setOption(GenerateGaugeOption(0.0));
        cPGs = ec.init(document.getElementById('divPGRect'));
        cIOPs = ec.init(document.getElementById('divIOPsContent'));
        cLatency = ec.init(document.getElementById('divLatencyContent'));
        cBandwidth = ec.init(document.getElementById('divBandwidthContent'));
        cCPU = ec.init(document.getElementById('divCPUContent'));
       
        cIOPs.setOption(GenerateLineOption());
        cLatency.setOption(GetLatencyOption());
        cBandwidth.setOption(GetBandwidthOption());
        cCPU.setOption(GenerateInitCPUOption());

    	//load Capacity
        loadCapacity();
        setInterval(function(){
            loadCapacity();
        },15000);

  
    	//load Capacity
        loadPG();
        setInterval(function(){
            loadPG();
        },15000);
    

        //IOPS  
        loadIOP();

        //Latency
        loadLatency();

        //Bandwith
        loadBandwidth();

        //CPU
        loadCPU();
    }
);


$(document).ready(function(){
    //Hide Page Title
    HidePageHeader();

    loadVersion();
    loadClusterStatus();
    loadOSD();
    loadMonitor();
    loadMDS();
    loadStorage();

    //Load Interval
    loadInterval();
})

function loadInterval(){
     setInterval(function(){
        loadClusterStatus();
 	    loadOSD();
        loadMonitor();
        loadMDS();
	    loadStorage();
     } ,15000);
}

function HidePageHeader(){
    $(".page-header").hide();
}

function ShowPerformace(){
    if($("#divPerformanceCantainer")[0].style.display == "none"){
        $("#divPerformanceCantainer").show();
        $("#imgExpandCollapse")[0].src = "/static/dashboard/img/collapse.png";
    }
    else{
        $("#divPerformanceCantainer").hide();
        $("#imgExpandCollapse")[0].src = "/static/dashboard/img/expand.png";
    }
}

function loadVersion(){
    $.ajax({
	type: "get",
	url: "/dashboard/vsm/version/",
	data: null,
	dataType:"json",
	success: function(data){
         //console.log(data);
        $("#lblVersionUpdate")[0].innerHTML =data.update;

        if(data.version == null)
            $("#lblVersion")[0].innerHTML= "--";
        else
            $("#lblVersion")[0].innerHTML= data.version;

	    if(data.ceph_version == null)
            $("#lblCephVersion")[0].innerHTML= "--";
        else
            $("#lblCephVersion")[0].innerHTML= data.ceph_version;
	   },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
    });
}

function loadClusterStatus(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/cluster/",
        data: null,
        dataType: "json",
        success: function (data) {
            var statusTip = "";
            var statusClass = "";
            var noteClass = "";

           switch (data.status) {
                case "HEALTH_OK":
                    statusTip = "health";
                    statusClass = "cluster-tip cluster-tip-health";
                    noteClass = "alert alert-success";
                    break;
                case "HEALTH_WARN": //warning
                    statusTip = "warning";
                    statusClass = "cluster-tip cluster-tip-warning";
                    noteClass = "alert alert-warning";
                    break;
                case "HEALTH_ERROR": //error
                    statusTip = "error";
                    statusClass = "cluster-tip cluster-tip-error";
                    noteClass = "alert alert-danger";
                    break;
            }

    		var note="";
    		for(var i=0;i<data.note.length;i++){
                    	note += data.note[i];
    			if(i!=data.note.length-1){
    				note +="<br />"
    			}
    		}

		    $("#lblClusterName")[0].innerHTML = data.name;
            $("#lblClusterTip")[0].innerHTML = statusTip;
            $("#lblClusterTip")[0].className = statusClass;
            $("#divClusterContent")[0].innerHTML = note;
            $("#divClusterContent")[0].className = noteClass;
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
    });
}

function loadOSD(){
    $.ajax({
	type: "get",
	url: "/dashboard/vsm/osd/",
	data: null,
	dataType:"json",
	success: function(data){
            // console.log(data);
            $("#lblOSDEpoch")[0].innerHTML = data.epoch;
            $("#lblOSDUpdate")[0].innerHTML = data.update;
            $("#divOSD_INUP")[0].innerHTML = data.in_up;
            $("#divOSD_INDOWN")[0].innerHTML = data.in_down;
            $("#divOSD_OUTUP")[0].innerHTML = data.out_up;
            $("#divOSD_OUTDOWN")[0].innerHTML = data.out_down;
            $("#lblOSDCapacityAvailable")[0].innerHTML = data.capacity_available_count;
            $("#lblOSDCapacityNearFull")[0].innerHTML = data.capacity_near_full_count;
            $("#lblOSDCapacityFull")[0].innerHTML = data.capacity_full_count;

            //data.capacity_near_full_count = 1;

            //init
            $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_health.png";
            //when error
            if(data.in_down>0 || data.capacity_full_count){
                $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_error.png";
                return;
            }
            //when warnning
            if(data.out_up>0 || data.out_down>0 || data.capacity_near_full_count){
                $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_warning.png";
                return;
            }
	    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
    });
}

function loadMonitor(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/monitor/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblMonitorEpoch")[0].innerHTML = data.epoch;
            $("#lblMonitorUpdate")[0].innerHTML = data.update;

            var rect =null;
            $("#divMonitorRect").empty();
            for(var i=0;i<data.quorum.length;i++) {
                if (i == data.selMonitor)
                   rect = "<div class='vsm-rect vsm-rect-monitor vsm-rect-green'>"+data.quorum[i]+"</div>";
                else
                    rect = "<div class='vsm-rect vsm-rect-monitor'>"+data.quorum[i]+"</div>";
                $("#divMonitorRect").append(rect);
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
 });
}

function loadMDS(){
	$.ajax({
	    type: "get",
	    url: "/dashboard/vsm/mds/",
	    data: null,
	    dataType:"json",
	    success: function(data){
    		//console.log(data)
    		$("#lblMDSEpoch")[0].innerHTML = data.epoch;
    		$("#lblMDSUpdate")[0].innerHTML = data.update;


            //show metadata
            if(data.MetaData == null)
                $("#divMDS_Metadata")[0].innerHTML = "0";
            else
                $("#divMDS_Metadata")[0].innerHTML = "1";

            if(data.PoolData == null)
                $("#divMDS_Data")[0].innerHTML = "0";
            else
                $("#divMDS_Data")[0].innerHTML = data.PoolData.length;

            
            $("#divMDS_IN")[0].innerHTML = data.In;
            $("#divMDS_UP")[0].innerHTML = data.Up;
            $("#divMDS_FAILED")[0].innerHTML = data.Failed;
            $("#divMDS_STOPPED")[0].innerHTML = data.Stopped;

            //init
            $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_health.png";
            //when error
            if(data.Failed>0){
                $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_error.png";
                return;
            }
            //when warnning
            if(data.Stopped>0){
                $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_warning.png";
                return;
            }         
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
	});
}

function loadStorage(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/storage/",
        data: null,
        dataType:"json",
        success: function(data){
            //console.log(data)
            $("#lblStorageUpdate")[0].innerHTML = data.update;
            $("#divStorageNormal")[0].innerHTML = data.normal;
            $("#divStorageNearFull")[0].innerHTML = data.nearfull;
            $("#divStorageFull")[0].innerHTML = data.full;

             //when error
            if(data.full>0){
                $("#imgStorageInfo")[0].src = "/static/dashboard/img/info_error.png";
                return;
            }
            //when warnning
            if(data.nearfull>0){
                $("#imgStorageInfo")[0].src = "/static/dashboard/img/info_warning.png";
                return;
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
    });
}

function loadCapacity(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/capcity/",
        data: null,
        dataType:"json",
        success: function(data){
            cClusterGague.setOption(GenerateGaugeOption(data.percent));
            //update the capacity value
            $("#lblCapacityUsed")[0].innerHTML = ((parseInt(data.used)/1024)/1024/1024).toFixed(2).toString() + " GB";
            $("#lblCapacityTotal")[0].innerHTML = ((parseInt(data.total)/1024)/1024/1024).toFixed(2).toString() + " GB";
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
     });
}

function loadPG(){
    $.ajax({
        type: "get",
        url: "/dashboard/vsm/PG/",
        data: null,
        dataType:"json",
        success: function(data){
                $("#lblPGUpdate")[0].innerHTML = data.update;
                cPGs.setOption(GetPieOption(data.active_clean,data.not_active_clean))
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            if(XMLHttpRequest.status == 401)
                window.location.href = "/dashboard/auth/logout/";
        }
     });
}

function loadIOP(){
    setTimeout(function (){
        if($("#divPerformanceCantainer")[0].style.display != "none") {
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/IOPS/",
                data: JSON.stringify({"timestamp": IOPs_EndTime}),
                dataType: "json",
                success: function (data) {
                    metrics = data.metrics;
                    var axisData = "00:00:00";
                    for (var i = 0; i < metrics.length; i++) {
                        IOPs_EndTime = metrics[i].timestamp;
                        axisData = new Date(parseInt(metrics[i].timestamp) * 1000).format("hh:mm:ss")

                        //add new node
                        cIOPs.addData([
                            [
                                0,        //read line
                                metrics[i].r_value,
                                false,
                                false,
                            ],
                            [
                                1,        //write line
                                metrics[i].w_value,
                                false,
                                false,
                            ],
                            [
                                2,        //read write line
                                metrics[i].rw_value,
                                false,
                                false,
                                axisData
                            ]
                        ]);
                    }

                    //load the IOP again
                    //loadIOP();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (XMLHttpRequest.status == 401)
                        window.location.href = "/dashboard/auth/logout/";
                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function () {

                }
            });
        }
        loadIOP();
    }, 15000);
}


function loadLatency(){
    setTimeout(function (){
        if($("#divPerformanceCantainer")[0].style.display != "none") {
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/latency/",
                data: JSON.stringify({"timestamp": Latency_EndTime}),
                dataType: "json",
                success: function (data) {
                    metrics = data.metrics;
                    var axisData = "00:00:00";
                    for (var i = 0; i < metrics.length; i++) {
                        Latency_EndTime = metrics[i].timestamp
                        var axisData = new Date(parseInt(metrics[i].timestamp) * 1000).format("hh:mm:ss")

                        //add new node
                        cLatency.addData([
                            [
                                0,        //read line
                                metrics[i].r_value,
                                false,
                                false,
                            ],
                            [
                                1,        //write line
                                metrics[i].w_value,
                                false,
                                false,
                            ],
                            [
                                2,        //read_write line
                                metrics[i].rw_value,
                                false,
                                false,
                                axisData
                            ]
                        ]);
                    }

                    //reload latency
                    //loadLatency();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (XMLHttpRequest.status == 401)
                        window.location.href = "/dashboard/auth/logout/";
                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function () {

                }
            });
        }
        loadLatency();
    }, 15000);
}

function loadBandwidth(){
    setTimeout(function (){
        if($("#divPerformanceCantainer")[0].style.display != "none") {
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/bandwidth/",
                data: JSON.stringify({"timestamp": BandWidth_EndTime}),
                dataType: "json",
                success: function (data) {
                    metrics = data.metrics;
                    var axisData = "00:00:00";
                    for (var i = 0; i < metrics.length; i++) {
                        BandWidth_EndTime = metrics[i].timestamp
                        var axisData = new Date(parseInt(metrics[i].timestamp) * 1000).format("hh:mm:ss")

                        //add new node
                        cBandwidth.addData([
                            [
                                0,        //in
                                metrics[i].in_value,
                                false,
                                false,
                            ],
                            [
                                1,        //out
                                metrics[i].out_value,
                                false,
                                false,
                                axisData
                            ]
                        ]);
                    }

                    //reload the bandwidth
                    //loadBandwidth();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (XMLHttpRequest.status == 401)
                        window.location.href = "/dashboard/auth/logout/";
                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function () {

                }
            });
        }
        loadBandwidth();
    }, 15000);
}

function loadCPU(){
    setTimeout(function (){
        if($("#divPerformanceCantainer")[0].style.display != "none") {
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/CPU/",
                data: JSON.stringify({"timestamp": CPU_EndTime}),
                dataType: "json",
                success: function (data) {
                    if (data.time.length > 0) {
                        cCPU.clear();
                        var timestampList = new Array();
                        var legendList = new Array();
                        var seriesList = new Array();
                        //get the timestamp list
                        for (var i = 0; i < data.time.length; i++) {
                            if (i == data.time.length - 1) {
                                CPU_EndTime = data.time[i]
                            }
                            var axisData = new Date(parseInt(data.time[i]) * 1000).format("hh:mm:ss")
                            timestampList.push(axisData);
                        }

                        for (var i = 0; i < data.cpus.length; i++) {
                            var cpu = data.cpus[i];
                            //get the legend list
                            legendList.push(cpu.name);
                            var series = {
                                name: cpu.name,
                                type: 'line',
                                smooth: true,
                                data: []
                            };


                            for (var j = 0; j < cpu.data.length; j++) {
                                series.data.push(cpu.data[j])
                            }
                            seriesList.push(series);
                        }
                        cCPU.setOption(GenerateCPUOption(timestampList, legendList, seriesList));
                    }

                    //Reload the data
                    //loadCPU();

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (XMLHttpRequest.status == 401)
                        window.location.href = "/dashboard/auth/logout/";
                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function () {

                }
            });
        }
        loadCPU();
    },15000);
}

function GenerateGaugeOption(value) {
    option = {
        tooltip: {
            formatter: "{a} <br/>{b} : {c}%"
        },
        series: [
            {
                name: '',
                type: 'gauge',
                detail: {
                    formatter: '{value}%',
                    textStyle:{
                        fontSize:20
                    }
                },
                data: [{value: value, name: ''}],
                splitLine:{
                    show: true,
                    length :5,
                    lineStyle: {
                        color: '#0062a8',
                        width: 1,
                        type: 'solid'
                    }
                },
                axisLine:{
                    show: true,
                    lineStyle: {
                        color: [
                            [0.2, '#228b22'],
                            [0.8, '#48b'],
                            [1, '#ff4500']
                        ],
                        width: 10
                    }
                },
                axisTick:{
                    show: true,
                    splitNumber: 5,
                    length :5,
                    lineStyle: {
                        color: '#eee',
                        width: 1,
                        type: 'solid'
                    }
                },
                radius:['30%', '100%'],
                center:['50%','55%']
            }
        ]
    };

    return option;
}

function GenerateLineOption(){
    var option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'85%'
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:["iops_r","iops_w","iops_rw"]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0
                },
                data :InitAxis_X()
            }
        ],
        yAxis : [
            {
                type : 'value',
                scale: false,
                min:0,
                //max:15,
                axisLabel:{
                    show:true,
                    interval:'auto'
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        dataZoom:{
            show:false,
            start:30,
            end:100
        },
        series : [
            {
                name:'iops_r',
                type:'line',
                smooth:true,
                data:InitValues(0)
            },
            {
                name:'iops_w',
                type:'line',
                smooth:true,
                data:InitValues(0)
            },
            {
                name:'iops_rw',
                type:'line',
                smooth:true,
                data:InitValues(0)
            }
        ]
    };
    return option;
}

function GenerateCPUOption(timestampList,legendList,seriesList){
    var option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'85%'
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:legendList
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0
                },
                data :timestampList
            }
        ],
        yAxis : [
            {
                type : 'value',
                scale: false,
                min:0,
                //max:15,
                axisLabel:{
                    show:true,
                    interval:'auto'
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        series : seriesList
    };
    return option;
}

function GenerateInitCPUOption(){
    var option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'85%'
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:[""]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0
                },
                data :InitAxis_X()
            }
        ],
        yAxis : [
            {
                type : 'value',
                scale: false,
                min:0,
                //max:15,
                axisLabel:{
                    show:true,
                    interval:'auto',
                    formatter: '{value}'
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        dataZoom:{
            show:false,
            start:30,
            end:100
        },
        series : [
            {
                name:'--',
                type:'line',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
        ]
    };
    return option;
}

function GetLatencyOption(){
    option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'85%'
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:["latency_r","latency_w","latency_rw"]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0
                },
                data : InitAxis_X()
            }
        ],
        yAxis : [
           {
                type : 'value',
                scale: false,
                min:0,
                //max:15,
                axisLabel:{
                    show:true,
                    interval:'auto'
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        dataZoom:{
            show:false,
            start:30,
            end:100
        },
        series : [
            {
                name:'latency_r',
                type:'line',
                stack: 'A',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
            {
                name:'latency_w',
                type:'line',
                stack: 'B',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
            {
                name:'latency_rw',
                type:'line',
                stack: 'C',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            }
        ]
    };
    return option;
}

function GetBandwidthOption(){
    option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'85%'
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:["bandwidth_in","bandwidth_out"]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0
                },
                data : InitAxis_X()
            }
        ],
        yAxis : [
           {
                type : 'value',
                scale: false,
                min:0,
                //max:15,
                axisLabel:{
                    show:true,
                    interval:'auto'
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        dataZoom:{
            show:false,
            start:30,
            end:100
        },
        series : [
            {
                name:'bandwidth_in',
                type:'line',
                stack: 'A',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
            {
                name:'bandwidth_out',
                type:'line',
                stack: 'B',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            }
        ]
    };
    return option;
}

//AC: active+clean
//NAC: not active+clean
function GetPieOption(AC,NAC){
    var option = {
	    tooltip : {
		trigger: 'item',
		formatter: "{b} : {c} ({d}%)"
	    },
            series : [
		{
		    name:'PG Summary',
		    type:'pie',
		    radius : '60%',
		    center: ['50%', '50%'],
		    data:[
		        {value:AC, name:'Active+Clean'},
		        {value:NAC, name:'Not Active+Clean'},
		    ]
		}
	    ],
            color:["green","orange"]
 	};
                    
	return option;
}

function InitAxis_X(){
    var now = new Date();
    var res = [];
    var len = 10;
    while (len--) {
        res.push("00:00:00");
    }
    return res;
}

function InitValues(value){
    var res = [];
    var len = 10;
    while (len--) {
        res.push(value);
    }
    return res;
}


Date.prototype.format = function(format) {
    var o = {
        "M+": this.getMonth() + 1,
        // month
        "d+": this.getDate(),
        // day
        "h+": this.getHours(),
        // hour
        "m+": this.getMinutes(),
        // minute
        "s+": this.getSeconds(),
        // second
        "q+": Math.floor((this.getMonth() + 3) / 3),
        // quarter
        "S": this.getMilliseconds()
        // millisecond
    };
    if (/(y+)/.test(format) || /(Y+)/.test(format)) {
        format = format.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    }
    for (var k in o) {
        if (new RegExp("(" + k + ")").test(format)) {
            format = format.replace(RegExp.$1, RegExp.$1.length == 1 ? o[k] : ("00" + o[k]).substr(("" + o[k]).length));
        }
    }
    return format;
};



