/**
 * Created by shouanxx on 3/26/2015.
 */
require.config({
    paths:{
        echarts:"../../static/lib/echarts",
    }
});

var cThroughput;
var cLatency;
var cClusterGague;
require(
    [
        'echarts',
        'echarts/chart/line',
        'echarts/chart/bar',
        'echarts/chart/pie',
        'echarts/chart/gauge'
    ],
    function(ec){
        cIOPs = ec.init(document.getElementById('divIOPsContent'));
        cLatency = ec.init(document.getElementById('divLatencyContent'));
        cClusterGague = ec.init(document.getElementById('divClusterGauge'));
        cPGs = ec.init(document.getElementById('divPGRect'));
        cIOPs.setOption(GenerateLineOption());
        cLatency.setOption(GetAreaLineOption());
        
  
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


        /*var IOPsInterval = setInterval(function (){
            $.ajax({
                type: "get",
                url: "/dashboard/vsm/IOPS/",
                data: null,
                dataType: "json",
                success: function (data) {
                    var axisData = (new Date()).toLocaleTimeString().replace(/^\D*//*, '');
                    var line1Data =  [0,data.line1, false, false, axisData];
                    var line2Data =  [1,data.line2, false, false, axisData];
                    // 动态数据接口 addData
                    cIOPs.addData([line1Data,line2Data]);
                }
            });
        }, 15000);*/
    }

);


$(document).ready(function(){
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

function loadVersion(){
    $.ajax({
	type: "get",
	url: "/dashboard/vsm/version/",
	data: null,
	dataType:"json",
	success: function(data){
        console.log(data);
        $("#lblVersionUpdate")[0].innerHTML ="Update:"+data.update;

        if(data.version == null)
            $("#lblVersion")[0].innerHTML= "VSM Version:--";
        else
            $("#lblVersion")[0].innerHTML= "VSM Version:"+data.version;

	    if(data.ceph_version == null)
            $("#lblCephVersion")[0].innerHTML= "Ceph Version::--";
        else
            $("#lblCephVersion")[0].innerHTML= "Ceph Version::"+data.ceph_version;
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
                        statusClass = "btn btn-success";
                        noteClass = "alert alert-success";
                        break;
                    case "HEALTH_WARN": //warning
                        statusTip = "warning";
                        statusClass = "btn btn-warning";
                        noteClass = "alert alert-warning";
                        break;
                    case "HEALTH_ERROR": //error
                        statusTip = "error";
                        statusClass = "btn btn-danger";
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
                $("#btnClusterTip")[0].innerHTML = statusTip;
                $("#btnClusterTip")[0].className = statusClass;
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
                $("#lblMDSMetaData")[0].innerHTML = "0";
            else
                $("#lblMDSMetaData")[0].innerHTML = data.MetaData;

            if(data.PoolData == null)
                $("#lblMDSPoolData")[0].innerHTML = "0";
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

function GenerateLineOption(){
   var option = {
        tooltip : {
            trigger: 'axis'
        },
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                data :(function () {
                    var now = new Date();
                    var res = [];
                    var len = 10;
                    while (len--) {
                        res.unshift(now.toLocaleTimeString().replace(/^\D*/, ''));
                        now = new Date(now - 2000);
                    }
                    return res;
                })()
            }
        ],
        yAxis : [
            {
                type : 'value',
                min:0,
                max:15,
                axisLabel : {
                    formatter: '{value}'
                }
            }
        ],
        grid: {
            x:30,
            y:20,
            x2:30,
            y2:40,

        },
        series : [
            {
                name:'',
                type:'line',
                data:(function () {
                    var res = [];
                    var len = 10;
                    while (len--) {
                        res.push(0);
                    }
                    return res;
                })()
            },
            {
                name:'',
                type:'line',
                data:(function () {
                    var res = [];
                    var len = 10;
                    while (len--) {
                        res.push(0);
                    }
                    return res;
                })()
            },
        ]
    };
    return option;
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

function GetAreaLineOption(){
    option = {
        xAxis : [
            {
                type : 'category',
                boundaryGap : false,
                data : ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            }
        ],
        yAxis : [
            {
                type : 'value'
            }
        ],
         grid: {
            x:30,
            y:20,
            x2:30,
            y2:40,
        },
        series : [
            {
                name:'A',
                type:'line',
                stack: 'A',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[120, 132, 101, 134, 90, 230, 210]
            },
            {
                name:'B',
                type:'line',
                stack: 'B',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[220, 182, 191, 234, 290, 330, 310]
            },
            {
                name:'C',
                type:'line',
                stack: 'C',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[150, 232, 201, 154, 190, 330, 410]
            },
            {
                name:'D',
                type:'line',
                stack: 'D',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[320, 332, 301, 334, 390, 330, 320]
            },
            {
                name:'E',
                type:'line',
                stack: 'E',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[820, 932, 901, 934, 1290, 1330, 1320]
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

//clearInterval(timeTicket);
//    timeTicket = setInterval(function () {
//        option.series[0].data[0].value = (Math.random() * 100).toFixed(2) - 0;
//        myChart.setOption(option, true);
//    }, 2000);