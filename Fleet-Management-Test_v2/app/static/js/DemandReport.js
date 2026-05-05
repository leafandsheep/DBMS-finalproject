let chart2;
$(function () {
    drawChart2();
    $('#search').click(updateData);
    // $('#begin-date-group').datetimepicker({
    //     format: 'YYYY-MM-DD',
    //     useCurrent: true,
    //     allowInputToggle: true
    // });
    // $('#end-date-group').datetimepicker({
    //     format: 'YYYY-MM-DD',
    //     useCurrent: true,
    //     allowInputToggle: true
    // });
});

function dataSeriesArray(real_data, forecast_data){
    let return_array = [], real_data_array = [],
        title_table_name_assoc = {
            'linear_regression_predict': 'Linear Regression',
            'vanilla_demand_predict_self_attention_96t': '96 Time steps',
            'vanilla_demand_predict_self_attention_weekholiday': 'Individual',
            'vanilla_demand_predict_no_attention': 'No Attention',
			'vanilla_demand_predict_4step': '4 time steps', 
			'vanilla_demand_predict_48step': '48 time steps', 
			'vanilla_demand_predict_96step': '96 time steps', 
			'demand_predict': 'predict_value',
        },
		line_color_array = {
			'linear_regression_predict': '#33cc33',
            'vanilla_demand_predict_self_attention_96t': '#0066ff',
            'vanilla_demand_predict_self_attention_weekholiday': '#33cc33',
            'vanilla_demand_predict_no_attention': '#ff8533',
			'vanilla_demand_predict_4step': '#33cc33', 
			'vanilla_demand_predict_48step': '#0066ff', 
			'vanilla_demand_predict_96step': '#ff8533', 
			'demand_predict_test': '#ff8533',
			//'vanilla_demand_predict_weekholiday_24hr': 'individual'
        };
        /*dash_type_array = {
            'stacked_demand_predict': 'longdash',
            'bidirectional_demand_predict': 'shortdot',
            'vanilla_demand_predict': 'DashDot'
        };*/
		dash_type_array = {
			'linear_regression_predict': 'Solid',
            'stacked_demand_predict': 'Solid',
            'bidirectional_demand_predict': 'Solid',
            'vanilla_demand_predict': 'Solid'
        };
    // 實際值陣列 [B]
	columnName = dashboard_type == 'london' ? 'energy' : 'demand_quarter';
    $.each(real_data, function(key, value) {
        real_data_array.push([
            (new Date(value['datetime'])).getTime(),
            value[columnName]
        ]);
    });
    return_array.push({
        name: 'demand',
        data: real_data_array,
		color: '#000000',
        dashStyle: 'Solid'
    });
    // 實際值陣列 [E]
    // 預測值陣列 [B]
    // $.each(forecast_data, function(table_name, update_data) {
        let data = [];
        $.each(forecast_data, function(key, value) {
            let forecast_value = value['prediction_4'] === null ? null : value['prediction_4'] * 1;
            data.push([
                (new Date(value['created_at'])).getTime(),
                forecast_value
            ]);
        });
        return_array.push({
            // name: title_table_name_assoc[table_name],
            // color: line_color_array[table_name],
            // dashStyle: dash_type_array[table_name],
            name: "predict_value",
            color: '#ff8533',
            dashStyle: 'Solid',
            data: data
        });
    // });
    // 預測值陣列 [B]
    return return_array;
}

function updateData() {
    var begin_date = $('#begin-date').val(),
        end_date = $('#end-date').val();
    $.ajax({
        type: 'POST',
        url: '/api/v1.0/getDemandData',
        data: {
            'begin_date': begin_date,
            'end_date': end_date
        },
        dataType: 'json'
    }).then(function(result) {
        if (!result['result']) {
            return false;
        }
        // console.log('demand_info' + result['data']['demand_info'])
        // console.log('forecast_data' + result['data']['demand_forecast'])
        var update_data = result['data'],
            series_data_array = dataSeriesArray(update_data['demand_info'], update_data['forecast_data']);
        chart2.update({
            series: series_data_array
        })
    });
}

function drawChart2() {
    // Create the chart2
    let series_data_array = dataSeriesArray(demandInfo, allForecastDataList);
     chart2 = Highcharts.stockChart('container', {
        accessibility: {
            enabled: false
        },

        time: {
            useUTC: false
        },

        rangeSelector: {
            buttons: [ {
                type: 'all',
                text: 'All'
            }],
            inputEnabled: false,
            selected: 0
        },
        title: {
            text: 'Demand Forecast'
        },

        exporting: {
            enabled: false
        },
         legend: {
             enabled: true,
             align: 'left',
             verticalAlign: 'top',
             borderWidth: 1
         },
         plotOptions: {
             series: {
                 lineWidth: 2
             }
         },
        series: series_data_array
    });
}
