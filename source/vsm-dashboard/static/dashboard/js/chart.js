
/* Copyright 2014 Intel Corporation, All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the"License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied. See the License for the
 specific language governing permissions and limitations
 under the License.
 */

var get_random_data = function (limit) {
    var data = [];

    var getRandomInt = function (min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    for (var i = 1; i < limit; i++) {
        data.push({
            index: i+19,
            name: 'test',
            value: getRandomInt(0, 1000)
        });
    }

    return data;
}

$(function () {
    console.log(charts);
    //var data = [{index:1, name: "test", value: 123}, {index:20, name: "test", value: 155}]
    //console.log(data);
    //ay.pie_chart('pie-a', data, {percentage: true});
    //ay.pie_chart('pie-b', get_random_data(10), {radius_inner: 50});
    //ay.pie_chart('pie-c', get_random_data(20), {group_data: 1});
    for(k in charts){
        var chart = charts[k];
        console.log(chart.type);
        $(".chart-container").append("<div class='chart'>" +
                "<svg class='" + chart.type +"-" + chart.name+"'></svg>"+
            "<div class=verbose><strong>"+chart.verbose_name+"<br/><span>"+chart.used+"</span>% Capacity Used </strong></div>" +
        "</div>");
        ay.pie_chart(chart.type+"-"+chart.name,
            chart.datas, {percentage: false})

    }
});
