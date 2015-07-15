var labelTop = {
    normal : {
        color:  '#ffff33',
        label : {
            show : true,
            position : 'center',
            formatter : '{b}',
            textStyle: {
                baseline : 'bottom'
            }
        },
        labelLine : {
            show : false
        }
    }
};
var labelFromatter = {
    normal : {
        label : {
            formatter : function (params){
                return (100 - params.value).toFixed(2) + '%'
            },
            textStyle: {
                baseline : 'top',color:  '#000',
            }
        }
    }
}
var labelBottom = {
    normal : {
        color:  '#00cc00',
        label : {
            show : true,
            position : 'center',

        },
        labelLine : {
            show : false
        }
    },
    emphasis: {
        color: 'rgba(0,0,0,0)'
    }
};
var radius = [50, 65];


require.config({
    paths:{
        echarts:"../../../static/lib/echarts",
    }
});

require(
    [
        'echarts',
        'echarts/chart/pie',
    ],
    function(ec){
		$.ajax({
	            type: "get",
	            url: "/dashboard/vsm/storage-group-status/chart_data/",
	            data: null,
	            dataType:"json",
	            success: function(data){
                    for(var i=0;i<data.length;i++){
                        var divChart = "";
                        var divCharID = "divChart_"+data[i].id;
                        divChart += "<div id='" + divCharID + "' class='pie-chart'></div>";
                        $("#divPieChartsContent").append(divChart);

                        var chart = ec.init(document.getElementById(divCharID));
                        chart.setOption(GetPieOption(data[i].name,data[i].used,data[i].available));
                    }
	            }
	    });
    }
);

function GetPieOption(label,used,available){
    var option = {
    	series : [
        	{
	            type : 'pie',
	            center : ['50%', '50%'],
	            radius : radius,
	            x: '0%', // for funnel
	            itemStyle : labelFromatter,
	            data : [
	                {name:'other', value:available, itemStyle : labelBottom},
	                {name:label, value:used,itemStyle : labelTop}
	            ]
        	}
   		]
	};
	return option;
}



