
require.config({
    paths:{
        echarts:"../../../../static/lib/echarts"
    }
});

var cClusterGague;
var cPGs;
require(
    [
        'echarts',
        'echarts/chart/gauge',
        'echarts/chart/pie',
    ],
    function(ec){
        cClusterGague = ec.init(document.getElementById('divCapcitySummary'));
		cPGs = ec.init(document.getElementById('divPGRect'));
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
			    url: "/dashboard/vsm/PG/",
			    data: null,
			    dataType:"json",
			    success: function(data){
			            cPGs.setOption(GetPieOption(data.active_clean,data.not_active_clean))
			    	}
		  	  });
		},15000);

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
    }

);


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
                center:['50%','60%']
            }
        ],
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
