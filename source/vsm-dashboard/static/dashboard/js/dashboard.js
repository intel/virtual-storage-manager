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
    
	// setInterval(function(){
	//     $.ajax({
	// 	    type: "get",
	// 	    url: "/dashboard/vsm/PG/",
	// 	    data: null,
	// 	    dataType:"json",
	// 	    success: function(data){
	// 	            cPGs.setOption(GetPieOption(data.active_clean,data.not_active_clean))
	// 	    	}
	//   	  });
	// },15000);


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
    loadVSMStatus();
    loadOSD();
    loadMonitor();
    //loadMDS();
    loadStorage();

    //Load Interval
    loadInterval();
})


function loadInterval(){
     setInterval(function(){
        loadVSMStatus();
 	    loadOSD();
        loadMonitor();
        //loadMDS();
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
        $("#lblVersion")[0].innerHTML= "Version:"+data.version;
	    $("#lblVersionUpdate")[0].innerHTML ="Update:"+data.update;
	   }
    });
}


function loadVSMStatus(){
        $.ajax({
            type: "get",
            url: "/dashboard/vsm/status/",
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

        if(data.in_down>0){
		$("#imgOSD")[0].src = "/static/dashboard/img/info_error.png";
                return;
	    }
            
            if(data.out_up>0){
                $("#imgOSD")[0].src = "/static/dashboard/img/info_warning.png";  
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
                    //if (i == data.selMonitor)
                    //    rect = "<div class='vsm-rect vsm-rect-1 vsm-rect-green'>"+data.quorum[i]+"</div>";
                    //else
                        rect = "<div class='vsm-rect vsm-rect-1'>"+data.quorum[i]+"</div>";
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

		var rect =null;
		$("#divMDSRect").empty();
		for(var i=0;i<data.MDS.length;i++) {
		    //if (i == data.selMDS)
		    //    rect = "<div class='vsm-rect vsm-rect-1 vsm-rect-green'>"+data.MDS[i]+"</div>";
		    //else
		        rect = "<div class='vsm-rect vsm-rect-1'>"+data.MDS[i]+"</div>";
		    $("#divMDSRect").append(rect);
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
                data : ['周一','周二','周三','周四','周五','周六','周日']
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
                name:'邮件营销',
                type:'line',
                stack: '总量',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[120, 132, 101, 134, 90, 230, 210]
            },
            {
                name:'联盟广告',
                type:'line',
                stack: '总量',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[220, 182, 191, 234, 290, 330, 310]
            },
            {
                name:'视频广告',
                type:'line',
                stack: '总量',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[150, 232, 201, 154, 190, 330, 410]
            },
            {
                name:'直接访问',
                type:'line',
                stack: '总量',
                itemStyle: {normal: {areaStyle: {type: 'default'}}},
                data:[320, 332, 301, 334, 390, 330, 320]
            },
            {
                name:'搜索引擎',
                type:'line',
                stack: '总量',
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
		    radius : '80%',
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