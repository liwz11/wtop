// https://www.echartsjs.com/examples/zh/editor.html?c=area-rainfall

var time_list = [];
var ibw_list = [];
var obw_list = [];

var bw_chart = echarts.init(document.getElementById('bw'));

bw_init_option = {
	// 标题样式
    title: {
        text: '出入带宽',
        subtext: '',
        left: 'center',
        align: 'right'
    },
    // 图片位置
    grid: {
        bottom: 80
    },
    // 工具箱
    toolbox: {
        feature: {
            dataZoom: { yAxisIndex: 'none' },
            restore: {},
            saveAsImage: {}
        },
        right: 60
    },
    // 提示框
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross',
            animation: false,
            label: {
                backgroundColor: '#505765'
            }
        }
    },
    // 图例
    legend: {
        data: ['出带宽', '入带宽'],
        left: 60
    },
    // 区域缩放
    dataZoom: [
        {
            show: true,
            realtime: true,
            start: 80,
            end: 100
        },
        {
            type: 'inside',
            realtime: true,
            start: 80,
            end: 100
        }
    ],
    // 颜色
    color: ['#EE6363','#4682B4']
};


bw_data_option = {
	// y轴
    yAxis: [
        {
            name: '出带宽(Mbps)',
            type: 'value',
            // 横向网格线设置不显示
            splitLine: { show: false },
            max: function(value) {
            	return Math.ceil(value.max)
            },
        },
        {
            name: '入带宽(Mbps)',
            nameLocation: 'start',
            type: 'value',
            // 横向网格线设置不显示
            splitLine: { show: false },
            max: function(value) {
            	return Math.ceil(value.max)
            },
            inverse: true,
        }
    ],
	// x轴
    xAxis: [
        {
            type: 'category',
            // 坐标轴两边留白策略，即x轴坐标开始与结束位置都不在最边缘
            boundaryGap: false,
            // 坐标轴线样式
            axisLine: {onZero: false},
            data: []
        }
    ],
    series: [
        {
            name: '出带宽',
            type: 'line',
            //折线平滑
            smooth : true,
            animation: true,
            //折线堆积区域样式
            areaStyle: {},
            //线条样式
            lineStyle: { width: 1 },
            data: []
        },
        {
            name: '入带宽',
            type: 'line',
            //折线平滑
            smooth : true,
            yAxisIndex: 1,
            animation: true,
            //折线堆积区域样式
            areaStyle: {},
            //线条样式
            lineStyle: { width: 1 },
            data: []
        }
    ]
};


bw_chart.setOption(Object.assign(bw_init_option, bw_data_option));

var t = 0;
get_data();

function get_data() {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var res = xmlhttp.responseText;
            //console.log(res);

            var performance_list = JSON.parse(res);
            if(performance_list.length > 0) {
            	t = performance_list[performance_list.length - 1]['t'];

            	performance_list.forEach(function(item) {
            		time_list.push(item.t);
					ibw_list.push(item.ibw);
					obw_list.push(item.obw);
				});

            	//bw_data_option.yAxis[0].max = Math.ceil(Math.max.apply(null, obw_list)) + 1;
            	//bw_data_option.yAxis[1].max = Math.ceil(Math.max.apply(null, ibw_list)) + 1;
				bw_data_option.xAxis[0].data = time_list.map(function (str) {
	                return str.replace(' ', '\n');
	            });

				bw_data_option.series[0].data = obw_list;
				bw_data_option.series[1].data = ibw_list;

				bw_chart.setOption(bw_data_option);
            }
        }
    }

    xmlhttp.open("GET", "http://[DOMAIN]:[PORT]/get_data?t=" + t, true);
    xmlhttp.timeout = [TIMEOUT] * 1000;
    xmlhttp.send(null);

    setTimeout(function() {
        get_data();
    }, [INTERVAL] * 1000);
}