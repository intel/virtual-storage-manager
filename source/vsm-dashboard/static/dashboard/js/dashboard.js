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
var IOP_EndTime = "";
var Latency_EndTime = "";
var Bandwidth_EndTime = "";
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
        cPGs = ec.init(document.getElementById('divPGRect'));
        cIOPs = ec.init(document.getElementById('divIOPsContent'));
        cLatency = ec.init(document.getElementById('divLatencyContent'));
        cBandwidth = ec.init(document.getElementById('divBandwidthContent'));
       
        cIOPs.setOption(GenerateLineOption());
        cLatency.setOption(GetLantencyOption());
        cBandwidth.setOption(GetBandwidthOption());
        
    	$.ajax({
                type: "get",
                url: "/dashboard/vsm/capcity/",
                data: null,
                dataType:"json",
                success: function(data){
    		    //console.log(data.value);
                        cClusterGague.setOption(GenerateGaugeOption(data.value));
                    }
             });
  
    	$.ajax({
                type: "get",
                url: "/dashboard/vsm/PG/",
                data: null,
                dataType:"json",
                success: function(data){
                        $("#lblPGUpdate")[0].innerHTML ="Update:&nbsp&nbsp"+data.update;
                        cPGs.setOption(GetPieOption(data.active_clean,data.not_active_clean))
                    }
             });
       
        setInterval(function(){
             $.ajax({
    	     type: "get",
    	     url: "/dashboard/vsm/capcity/",
    	     data: null,
    	     dataType:"json",
    	     success: function(data){
    	             option.series[0].data[0].value = data.value;
    	             cClusterGague.setOption(option, true);
    	         }
    	     });
         },15000);
   
    	setInterval(function(){
    	     $.ajax({
    		    type: "get",
    		    url: "/dashboard/vsm/PG/",
    		    data: null,
    		    dataType:"json",
    		    success: function(data){
    		            cPGs.setOption(GetPieOption(data.active_clean,data.not_active_clean))
    		    	}
    	   	  });
    	},15000);

        //IOPS
        loadIOP();

        //Lantency
        loadLantency();

        //Bandwith
        loadBandwith();
    }
);


function loadIOP(){
    setTimeout(function (){
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/IOPS/",
                data: JSON.stringify({"timestamp":IOP_EndTime }),
                //data:"",
                dataType: "json",
                success: function (data) {
                    metrics = data.metrics;
                    for(var i=0;i<metrics.length;i++){
                        IOP_EndTime = metrics[i].timestamp;
                        var axisData = new Date(parseInt(metrics[i].timestamp)*1000).format("hh:mm:ss")

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
                                axisData
                            ],
                            [
                                1,        //write line
                                metrics[i].rw_value,
                                false,
                                false,
                            ]
                        ]);
                    }

                    //Reload the data
                    console.log((new Date()).getSeconds());
                    loadIOP();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function(){

                }
            });
    }, 15000);
}

function loadLantency(){
    setTimeout(function (){
        $.ajax({
            type: "post",
            url: "/dashboard/vsm/latency/",
            data: JSON.stringify({"timestamp":Latency_EndTime }),
            dataType: "json",
            success: function (data) {
                metrics = data.metrics;
                var axisData = "00:00:00";
                for(var i=0;i<metrics.length;i++){
                    Latency_EndTime = metrics[i].timestamp;
                    var axisData = new Date(parseInt(metrics[i].timestamp)*1000).format("hh:mm:ss")

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

                //Reload the data
                console.log((new Date()).getSeconds());
                loadLantency();
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {

            },
            headers: {
                "X-CSRFToken": token
            },
            complete: function(){

            }
        });
    }, 15000);
}

function loadBandwith(){
    setTimeout(function (){
            $.ajax({
                type: "post",
                url: "/dashboard/vsm/bandwidth/",
                data: JSON.stringify({"timestamp":Bandwidth_EndTime }),
                dataType: "json",
                success: function (data) {
                    //data {"metrics": metrics}
                    metrics = data.metrics;
                    var axisData = "00:00:00";
                    for(var i=0;i<metrics.length;i++){
                        Bandwidth_EndTime = metrics[i].timestamp
                        var axisData = new Date(parseInt(metrics[i].timestamp)*1000).format("hh:mm:ss")

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
                    //Reload the data
                    console.log((new Date()).getSeconds());
                    loadBandwith();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                },
                headers: {
                    "X-CSRFToken": token
                },
                complete: function(){

                }
            });
        }, 15000);
}

$(document).ready(function(){
    //loadVersion();
    //loadClusterStatus();
    //loadOSD();
    //loadMonitor();
    //loadMDS();
    //loadStorage();

    //Load Interval
    //loadInterval();
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

function loadVersion(){
    $.ajax({
	type: "get",
	url: "/dashboard/vsm/version/",
	data: null,
	dataType:"json",
	success: function(data){
         //console.log(data);
        $("#lblVersionUpdate")[0].innerHTML ="Update:&nbsp&nbsp"+data.update;

        if(data.version == null)
            $("#lblVersion")[0].innerHTML= "VSM Version:&nbsp&nbsp--";
        else
            $("#lblVersion")[0].innerHTML= "VSM Version:&nbsp&nbsp"+data.version;

	    if(data.ceph_version == null)
            $("#lblCephVersion")[0].innerHTML= "Ceph Version:&nbsp&nbsp--";
        else
            $("#lblCephVersion")[0].innerHTML= "Ceph Version:&nbsp&nbsp"+data.ceph_version;
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

		$("#lblClusterName")[0].innerHTML = "Cluster Name:"+data.name;
                $("#lblClusterTip")[0].innerHTML = statusTip;
                $("#lblClusterTip")[0].className = statusClass;
                $("#divClusterContent")[0].innerHTML = note;
                $("#divClusterContent")[0].className = noteClass;
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
	    //console.log(data);
	    $("#lblOSDEpoch")[0].innerHTML ="Epoch:"+ data.epoch;
	    $("#lblOSDUpdate")[0].innerHTML ="Update:"+ data.update;
	    $("#divOSD_INUP")[0].innerHTML = data.in_up;
	    $("#divOSD_INDOWN")[0].innerHTML = data.in_down;
	    $("#divOSD_OUTUP")[0].innerHTML = data.out_up;
	    $("#divOSD_OUTDOWN")[0].innerHTML = data.out_down;

        //data.in_down = 0;
        //data.out_up = 1;

        //init
        $("#divOSD")[0].style.border = "1px solid #ccc";
        $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_health.png";
        //when error
        if(data.in_down>0){
            $("#divOSD")[0].style.border = "1px solid red";
            $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_error.png";
            return;
	    }
        //when warnning
        if(data.out_up>0){
            $("#divOSD")[0].style.border = "1px solid orange";
            $("#imgOSDInfo")[0].src = "/static/dashboard/img/info_warning.png";
            return;
        }         
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

            if(data.MetaData == null)
                $("#lblMDSMetaData")[0].innerHTML = "--";
            else
                $("#lblMDSMetaData")[0].innerHTML = data.MetaData;

            if(data.PoolData == null)
                $("#lblMDSPoolData")[0].innerHTML = "--";
            else
                $("#lblMDSPoolData")[0].innerHTML = data.PoolData;

            
            $("#divMDS_IN")[0].innerHTML = data.In;
            $("#divMDS_UP")[0].innerHTML = data.Up;
            $("#divMDS_FAILED")[0].innerHTML = data.Failed;
            $("#divMDS_STOPPED")[0].innerHTML = data.Stopped;

            //init
            $("#divMDS")[0].style.border = "1px solid #ccc";
            $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_health.png";
            //when error
            if(data.Failed>0){
                $("#divMDS")[0].style.border = "1px solid red";
                $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_error.png";
                return;
            }
            //when warnning
            if(data.Stopped>0){
                $("#divMDS")[0].style.border = "1px solid orange";
                $("#imgMDSInfo")[0].src = "/static/dashboard/img/info_warning.png";
                return;
            }         
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
                $("#lblStorageUpdate")[0].innerHTML = "Update:"+ data.update;
                $("#lblStorageNormal")[0].innerHTML = data.normal;
                $("#lblStorageNearFull")[0].innerHTML = data.nearfull;
                $("#lblStorageFull")[0].innerHTML = data.full;
            }
     });
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
                detail: {formatter: '{value}%'},
                data: [{value: value, name: 'Capacity'}],
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
                        width: 10,
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
                radius:['30%', '95%'],
                center:['55%','50%']
            }
        ],
    };

    return option;
}

function GenerateLineOption(){
    var option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'90%',
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:["op_r","op_w","op_rw"]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0,
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
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        series : [
            {
                name:'op_r',
                type:'line',
                smooth:true,
                data:InitValues(0)
            },
            {
                name:'op_w',
                type:'line',
                smooth:true,
                data:InitValues(0)
            },
            {
                name:'op_rw',
                type:'line',
                smooth:true,
                data:InitValues(0)
            }
        ]
    };
    return option;
}

function GetLantencyOption(){
    option = {
        grid :{
            x:40,
            y:20,
            height:'80%',
            width:'90%',
        },
        tooltip:{
            trigger:'axis'
        },
        legend:{
            data:["lantency_r","lantency_w","lantency_rw"]
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                axisLabel:{
                    show:true,
                    interval:0,
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
                    interval:'auto',
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
        series : [
            {
                name:'lantency_r',
                type:'line',
                stack: 'A',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
            {
                name:'lantency_w',
                type:'line',
                stack: 'B',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:InitValues(0)
            },
            {
                name:'lantency_rw',
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
            x:60,
            y:20,
            height:'80%',
            width:'90%',
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
                    interval:0,
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
                    interval:'auto',
                },
                name : '',
                boundaryGap: [0.5, 0.5]
            }
        ],
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