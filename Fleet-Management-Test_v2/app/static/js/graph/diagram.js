/*該月每日最大需量*/
function daily_maxDemand(dialog, meterData, data) {

    // determine the color for the bar based on the percentage
    for ( i in data) {
        if (data[i]["label"] != null) {
            data[i]["color"] = "#ff4d4d";
        }
    }
    console.log(dialog);
    console.log(meterData);
    console.log(data);
    var chart = AmCharts.makeChart("tabpane_dailyPeak_" + meterData["address"] + '_' + meterData["ch"], {
        "type": "serial",
        "theme": "light",
        "dataProvider": data,
        "legend": {
            // "equalWidths": false,
            "useGraphSettings": true,
            "valueAlign": "left",
            "valueWidth": 120
        },
        "valueAxes": [{
            "gridColor": "#FFFFFF",
            "gridAlpha": 0.2,
            "dashLength": 0
        }],
        "gridAboveGraphs": true,
        "startDuration": 1,
        "graphs": [{
            "balloonFunction": function (item) {
                return "<span style='font-size:12px; font-family:Microsoft JhengHei;'> 時間:" + item.dataContext.time + "<br><b>需量:" + item.dataContext.peak_demand + " KW</b>[[additional]]</span>"
            },
            "fillAlphas": 0.8,
            "lineAlpha": 0.2,
            "type": "column",
            "title": "每日最大需量",
            "labelText": "[[label]]",
            "fontSize": 12,
            "color": "#ff4d4d",
            "legendValueText": "[[value]] KW",
            "valueField": "peak_demand",
            "fillColorsField": "color",
            "showHandOnHover": true,
        }],
        "chartCursor": {
            "categoryBalloonEnabled": false,
            "cursorAlpha": 0,
            "zoomable": false
        },
        "categoryField": "time",
        "categoryAxis": {
            "gridPosition": "start",
            "gridAlpha": 0,
            "tickPosition": "start",
            "tickLength": 20,
            "period": 'SS',
            "format": 'MMM DD JJ:NN:SS',
            "parseDates": true

        },
        "listeners": [{
            "event": "clickGraphItem",
            "method": function (event) {
                var parsetime = AmCharts.formatDate(new Date(event.item.category), "YYYY-MM-DD")
                // var parsetime = event.item.category.dataDateFormat = "YYYY-MM-DD";
                dialog.find(".tabpane_dailyPeak").hide();
                dialog.find(".tabpane_dailyPeak_page").show();
                var spinner_daily_maxDemand_period = show_spinner(dialog.find(".tabpane_dailyPeak1"));
                $.ajax({
                    type: "GET",
                    url: "/api/v1.0/peak_period_in_day",
                    dataType: 'json',
                    data: {
                        "address": meterData["address"],
                        "channel": meterData["ch"],
                        "datetime": parsetime
                    },
                    success: function (response) {
                        daily_power("tabpane_dailyPeak1_" + meterData["address"] + '_' + meterData["ch"], response);
                        remove_spinner(spinner_daily_maxDemand_period);
                    },
                    error: function () {
                        alert('no  每日最大需量區間並無資料 data')

                    }
                });
            }
        }]
    });
}
//click and show the peak demand  period in day
function daily_power(div, data) {
    console.log(data);
    var chart = AmCharts.makeChart(div, {
        "type": "serial",
        //圖例
        "mouseWheelZoomEnabled": false,
        "dataDateFormat": "YYYY-MM-DD JJ:NN:SS",
        "legend": {
            // "equalWidths": false,
            "useGraphSettings": true,
            "valueAlign": "left",
            "valueWidth": 120
        },
        //資料
        "dataProvider": data["demands"],
        "valueAxes": [
            //Demand值軸
            {
                "id": "demandAxis",
                "gridColor": "#FFFFFF",
                "gridAlpha": 0.5,
                "position": "left",
                "title": "KW",
                "minimum": 0
            },
        ],
        "gridAboveGraphs": true,
        "graphs": [{
            "id": "g1",
            "balloonText": "<span style='font-size:12px; font-family:Microsoft JhengHei;'> 時間:[[category]]<br><b>即時功率:[[value]] KW</b>[[additional]]</span>",
            "bullet": "round",
            "bulletsize": 0.5,
            "bulletBorderThickness": 1.5,
            "bulletBorderAlpha": 0.5,
            "bulletColor": "#FFFFFF",
            "useLineColorForBulletBorder": true,
            "balloon": {
                "drop": false
            },
            "hideBulletsCount": 24,
            "legendValueText": "[[value]] KW",
            "title": "每10秒功率",
            "labelPosition": "right",
            "valueField": "Value",
            "valueAxis": "demandAxis",
            "fillColorsField": "lineColor",
            "lineColorField": "lineColor",
            "fillAlphas": 0.3,
            //  "lineColor": " #1f77b4",
            "lineThickness": 2.5,
            "showHandOnHover": true
        }, ],
        "chartScrollbar": {
            "graph": "g1",
            "autoGridCount": true,
            "scrollbarHeight": 40,
            "color": "#000000"
        },
        "chartCursor": {
            "categoryBalloonEnabled": false,
            "categoryBalloonDateFormat": "MMM DD,JJ:NN:SS",
            "cursorPosition": "mouse",
            "cursorColor": "#D9E3EB",
            "cursorAlpha": 1,
            "fullWidth": true,
        },
        "valueScrollbar": {
            "autoGridCount": true,
            "color": "#000000",
            "scrollbarHeight": 50
        },
        "categoryField": "time",
        "categoryAxis": {
            "minPeriod": "10ss",
            "parseDates": true
        },
    });

}
