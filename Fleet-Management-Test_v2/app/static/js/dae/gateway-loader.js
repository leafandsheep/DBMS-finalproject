$(document).ready(function () {
    // 開機設定資料--讀取
    $.ajax({
        type: "GET",
        url: "/api/v1.0/query/settings",
        dataType: 'json',
        async: false,
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (response) {
            if (role == "Cloud") {
                response = JSON.parse(response);
            }
            if (response.length == 0) {
                swal({
                    title: '此Gateway尚未設定電錶',
                    type: 'success'
                })
            } else {
                for (item in response) {
                    insert_open_initset(response[item]);
                    if (role == "Cloud") {
                        meter(response[item]);
                    } else {
                        meter_gateway(response[item]);
                    }
                }
            }
        },
        error: function (response) {
            alert("開機設定資料讀取逾時");
        }
    });

    // 一般設定資料--讀取 [query/demand_settings]
    $.ajax({
        type: "POST",
        url: "/api/v1.0/query/demand_settings",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        async: false,
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            var min_rate = response[0]["value_min"] * 100 / response[0]["value"];
            var max_rate = response[0]["value_max"] * 100 / response[0]["value"];
            $(".gateway_bar_range").slider({
                range: true,
                min: 0,
                max: 100,
                step: 5,
                values: [min_rate, max_rate],
                slide: function (event, ui) {
                    $(".gateway_minimum").val(ui.values[0]);
                    $(".gateway_maximum").val(ui.values[1]);
                }
            });
            $(".gateway_minimum").val($(".gateway_bar_range").slider("values", 0));
            $(".gateway_maximum").val($(".gateway_bar_range").slider("values", 1));
            $(".gateway_bar_maxDemand").slider({
                range: "min",
                min: 100,
                max: 1000,
                step: 10,
                value: response[0]["value"],
                slide: function (event, ui) {
                    $(".gateway_maxDemand").val(ui.value);
                }
            });
            $(".gateway_maxDemand").val($(".gateway_bar_maxDemand").slider("value"));
            $(".gateway_offloadOverhead").val(response[0]["load_off_gap"]);
            $(".gateway_reloadDelayOverhead").val(response[0]["reload_delay"]);
            $(".gateway_reloadOverhead").val(response[0]["reload_gap"]);
            $(".gateway_groupCategory").val(response[0]["group"]);
            $(".gateway_offload_mode").val(response[0]["mode"]);
            $(".gateway_cycle").val(response[0]["cycle"]);
        },
        error: function (response) {
            alert("一般設定資料讀取逾時");
        }
    });

    for (var i = 1; i <= 12; i++) {
        $("#panel-groups-boolean").append('\
            <div style="margin: 40px 0;" class="checkbox" > \
                Group ' + i + '\
                <div class="switch pull-right gateway" id="gateway_change' + i + '" >\
                    <input id="gateway_cmn-toggle-' + i + '" data-group="' + i + '" class="cmn-toggle cmn-toggle-round" type="checkbox">\
                    <label for="gateway_cmn-toggle-' + i + '"></label>\
                </div>\
            </div>');

        $("#panel-groups-available").append('\
            <div  style="margin: 40px 0;" class="checkbox">\
                Group ' + i + '\
                <div class="switch pull-right group" id="group_change' + i + '"> \
                    <input id="group_cmn-toggle-' + i + '" data-group="' + i + '" class="cmn-toggle cmn-toggle-round" type="checkbox"> \
                    <label for="group_cmn-toggle-' + i + '" value="false"></label> \
                </div> \
            </div>');
    }

    // 卸載設定資料--讀取
    $.ajax({
        type: "POST",
        url: "/api/v1.0/query/offloads",
        async: false,
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (response) {
            if (role == "Cloud") {
                response = JSON.parse(response);
            }
            for (var idx = 0; idx < response.length; idx++) {
                $("#gateway_cmn-toggle-" + response[idx]["group"]).attr("checked", response[idx]["boolean"] === 'true');
                $("#group_cmn-toggle-" + response[idx]["group"]).attr("checked", response[idx]["available"] === 'true');
            }
        },
        error: function () {
            alert("即時控制設定資料讀取逾時");
        }
    });

    //一般反應設定資料--更新
    $(".btn_updateGateway").click(function () {
        $.ajax({
            type: "GET",
            url: "/api/v1.0/insert/demand_settings",
            dataType: 'json',
            data: {
                'gateway_uid': gateway_uid,
                "value": parseInt($(".gateway_maxDemand").val()),
                "value_max": parseInt($(".gateway_maximum").val() * $(".gateway_maxDemand").val() / 100),
                "value_min": parseInt($(".gateway_minimum").val() * $(".gateway_maxDemand").val() / 100),
                "load_off_gap": parseInt($(".gateway_offloadOverhead").val()),
                "reload_delay": parseInt($(".gateway_reloadDelayOverhead").val()),
                "reload_gap": parseInt($(".gateway_reloadOverhead").val()),
                "cycle": $("select[name='cycle']").val(),
                "mode": $(".gateway_offload_mode").val(),
                "group": $(".gateway_groupCategory").val(),
            },
            beforeSend: function (response) {
                swal('Wait...');
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                if (response["status"] == "ok") {
                    swal('一般反應設定更新成功', response['status'], 'success');
                    $(".dialog_gatewaySetting").dialog("close");

                } else {
                    swal('一般反應設定更新失敗', response['status'], 'error');
                }
            },
            error: function (response) {
                swal('一般反應設定更新逾時', response['status'], 'error');
            }
        });
    });

    //卸載設定資料--更新
    $(".dialog.dialog_control").find(".cmn-toggle.cmn-toggle-round").click(function () {
        var gateway_state = $("#gateway_cmn-toggle-" + $(this).attr("data-group")).prop('checked')
        var group_state = $("#group_cmn-toggle-" + $(this).attr("data-group")).prop('checked')
        $.ajax({
            type: "GET",
            url: "/api/v1.0/update/offloads",
            data: {
                "group": parseInt($(this).attr("data-group")),
                "boolean": gateway_state,
                "available": group_state
            },
            beforeSend: function () {
                swal({
                    title: 'Wait...',
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
            },
            success: function (response) {
                if (role == "Cloud") {
                    response = JSON.parse(response);
                }
                if (response["status"] == "ok")
                    swal('即時控制設定資料更新成功', response['status'], 'success');
                else
                    swal('即時控制設定資料更新失敗', response['status'], 'error');
            },
            error: function (response) {
                swal('即時控制設定資料更新逾時', response['status'], 'error');
            }
        });
        console.log(JSON.stringify({
            "group": parseInt($(this).attr("data-group")),
            "boolean": $("#gateway_cmn-toggle-" + $(this).attr("data-group")).prop('checked'),
            "available": $("#group_cmn-toggle-" + $(this).attr("data-group")).prop('checked')
        }));
    });

    //開機設定資料--更新
    $(".btn_updateMeter").click(function () {
        $.ajax({
            type: "GET",
            url: "/api/v1.0/update/settings",
            dataType: 'json',
            async: false,
            data: {
                "gateway_uid": gateway_uid,
                "query_update_ch": temp_ch,
                "query_update_address": temp_address,
                "update_id": updated_id,
                "update_model": $(".meter_update_model").val(),
                "update_address": $(".meter_update_address").val(),
                "update_ch": $(".meter_update_channel").val(),
                "update_speed": $(".meter_update_speed").val(),
                "update_circuit": $(".meter_update_circuit").val(),
                "update_pt": $(".meter_update_pt").val(),
                "update_ct": $(".meter_update_ct").val(),
                "update_type": $(".meter_update_type").val(),
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                if (response["status"] == "ok") {
                    swal('開機設定更新成功', response['state'], 'success');
                    this_button.children('.model').text($(".meter_update_model").val())
                    this_button.children('.address').text($(".meter_update_address").val())
                    this_button.children('.ch').text($(".meter_update_channel").val())
                    this_button.children('.speed').text($(".meter_update_speed").val())
                    this_button.children('.circuit').text($(".meter_update_circuit").val())
                    this_button.children('.pt').text($(".meter_update_pt").val())
                    this_button.children('.ct').text($(".meter_update_ct").val())
                    this_button.children('.main_type').text($(".meter_update_type").val())
                } else if (response["status"] == "repeat") {
                    swal('已有相同頻道' + $(".meter_update_address").val().toString() + '與位址' + $(".meter_update_channel").val().toString(), response['status'], 'error');
                } else if (response["status"] == "circuit_repeat") {
                    swal('已有相同迴路' + $(".meter_update_circuit").val().toString(), response['status'], 'error');
                }
                $('.col-lg-3.col-md-3.col-sm-12.col-xs-12.' + temp_address + '_' + temp_ch).children().children('.count').text($(".meter_update_model").val() + ' ' + $(".meter_update_address").val() + '/' + $(".meter_update_channel").val());
                $('.col-lg-3.col-md-3.col-sm-12.col-xs-12.' + temp_address + '_' + temp_ch).addClass($(".meter_update_address").val() + '_' + $(".meter_update_channel").val());
                $('.col-lg-3.col-md-3.col-sm-12.col-xs-12.' + $(".meter_update_address").val() + '_' + $(".meter_update_channel").val()).removeClass(temp_address + '_' + temp_ch);
            },
            error: function (response) {
                swal('開機設定更新逾時', response['state'], 'error');
            }
        });
    });

    //開機設定資料--更新table-frame
    $(".table.table-bordered.table_meter").on('click', '.btn.update', function () {
        updated_id = $(this).parents().parents().parents().attr("id");
        $('.page_meterList').hide();
        $('.page_meterSetting').show();
        $('.btn_to_page_meterList').click(function (e) {
            $('.page_meterSetting').hide();
            $('.page_meterList').show();
        });
        this_button = $(this).parent().parent();
        //開機設定資料更新
        temp_address = this_button.children('.address').text();
        temp_ch = this_button.children('.ch').text();
        temp_model = this_button.children('.model').text();
        temp_circuit = this_button.children('.circuit').text();
        temp_speed = this_button.children('.speed').text();
        temp_pt = this_button.children('.pt').text();
        temp_ct = this_button.children('.ct').text();
        temp_main_type = this_button.children('.meter_type').text();
        console.log(temp_main_type);
        $('.meter_update_model').val(temp_model);
        $('.meter_update_address ').val(temp_address);
        $('.meter_update_channel ').val(temp_ch);
        $('.meter_update_speed ').val(temp_speed);
        $('.meter_update_circuit').val(temp_circuit);
        $('.meter_update_pt').val(temp_pt);
        $('.meter_update_ct').val(temp_ct);
        $('.meter_update_type').val(temp_main_type);
    });

    //開機設定資料--新增 query/settings
    $(".btn_insertMeter").click(function () {
        console.log('開機設定資料新增');
        $.ajax({
            type: "GET",
            url: "/api/v1.0/insert/settings",
            dataType: 'json',
            data: {
                'gateway_uid': gateway_uid,
                "model": $(".meter_new_model").val().toString(),
                "address": $(".meter_address").val().toString(),
                "ch": $(".meter_channel").val().toString(),
                "speed": $(".meter_speed").val().toString(),
                "circuit": $(".meter_circuit").val().toString(),
                "pt": $(".meter_pt").val().toString(),
                "ct": $(".meter_ct").val().toString(),
                "type": $(".meter_type.form-control").val().toString(),
            },
            beforeSend: function (response) {
                swal('Wait...');
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                if (response['status'] == "repeat") {
                    swal('已有相同頻道' + $(".meter_channel").val().toString() + '與位址' + $(".meter_address").val().toString(), response['status'], 'failed');
                } else if (response['status'] == "circuit_repeat") {
                    swal('已有相同迴路' + $(".meter_circuit").val().toString(), response['status'], 'failed');
                } else if (response['status'] == "ok") {
                    console.log(response);
                    var row = $('<thead id="' + response['id'] + '">\
                    <tr>\
                    <th class="model" width="70">' + $(".meter_new_model").val().toString() + '</th>\
                    <th class="address">' + $(".meter_address").val().toString() + '</th>\
                    <th class="ch">' + $(".meter_channel").val().toString() + '</th>\
                    <th class="speed">' + $(".meter_speed").val().toString() + '</th>\
                    <th class="circuit">' + $(".meter_circuit").val().toString() + '</th>\
                    <th class="pt" >' + $(".meter_pt").val().toString() + '</th>\
                    <th class="ct">' + $(".meter_ct").val().toString() + '</th>\
                    <th class="meter_type">' + $(".meter_type.form-control").val().toString() + '</th>\
                    <th width="280px"><button class="btn btn-danger delete" type="button" href="#">刪除</button>\
                    <button class="btn btn-warning update" type="button" href="#">更新</button></th>\
                    </tr>\
                    </thead>').appendTo(".table_meter");
                    meter(data = {
                        'model': $(".meter_new_model").val().toString(),
                        'address': $(".meter_address").val().toString(),
                        'ch': $(".meter_channel").val().toString()
                    })
                    swal('開機設定新增成功', response['state'], 'success')
                }
            },
            error: function (response) {
                swal('開機設定新增逾時', response['state'], 'error');
            }
        });
    });

    //開機設定資料--刪除
    $(".table_meter").on('click', 'thead > tr > th > button.delete', function () {
        this_button = $(this).parent().parent();
        $.ajax({
            type: "GET",
            url: "/api/v1.0/delete/settings",
            dataType: 'json',
            async: false,
            data: {
                "gateway_uid": gateway_uid,
                id: this_button.parent().attr('id'),
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                if (response["status"] == "ok")
                    swal('開機設定刪除成功', response['status'], 'success')
                else {
                    swal('開機設定刪除失敗', response['status'], 'error')
                }
            },
            error: function (response) {
                swal('開機設定刪除失敗', response['state'], 'error')
            }
        });
        this_button.parent().remove();
        $('.col-lg-3.col-md-3.col-sm-12.col-xs-12.' + this_button.children('.address').text() + '_' + this_button.children('.ch').text()).remove();
    });

    //一般反應設定頁面
    $(".btn_setting_gateway").click(function () {
        $(".dialog_gatewaySetting").dialog({
            title: "一般反應設定",
            dialogClass: "dlg-no-close",
            width: 800,
            height: 600,
            resizable: false,
            resizeStop: function () {
                $(this).height($(this).parent().height() - $(this).prev('.ui-dialog-titlebar').height() - $(this).prev('.ui-dialog-buttonpane').height() - 34);
                $(this).width($(this).prev('.ui-dialog-titlebar').width() + 2);
                // $("#Demand_high, #Demand_high_Interval, #Demand").height($(this).height() - $(".modal-header").height() - $(".dateframe").height() - $("#myTab").height() - 34);
            },
        });
    });

    //開機設定頁面
    $(".btn_setting_meters").click(function () {
        $(".dialog_meterList").dialog({
            title: "開機設定",
            dialogClass: "dlg-no-close",
            width: 800,
            height: 600,
            resizable: false,
            resizeStop: function () {
                console.log($(this).parent().height(), $(this).prev('.ui-dialog-titlebar ').width())
                $(this).height($(this).parent().height());
                $(this).width($(this).prev('.ui-dialog-titlebar ').width());
            },
            open: function () {
                $('.page_meterList').show();
                $('.page_newMeter').hide();
            },
            close: function () {
                $('.page_meterSetting').hide();
                $('.page_meterList').hide();
                $('.page_newMeter').show();
            },
        });
    });

    //用電紀錄頁面
    $(".btn_setting_elerecord").click(function () {
        var numberforinsert = 0;
        $.ajax({
            type: "GET",
            url: "/api/v1.0/query/records",
            dataType: 'json',
            async: false,
            resizable: false,
            data: {},
            success: function (response) {
                numberforinsert = (response.length > 50 ? 50 : response.length); //取最近50個紀錄
                for (var idx = 0; idx < numberforinsert; idx++) {
                    var data = response[idx];
                    insert_ele_record(data);
                }
            },
            error: function (response) {
                alert("用電紀錄資料讀取逾時");
            }
        });
        $(".dialog_eleRecordList").dialog({
            title: "用電紀錄",
            dialogClass: "dlg-no-close",
            width: 800,
            height: 600,
            resizeStop: function () {
                $(this).height($(this).parent().height() - $(this).prev('.ui-dialog-titlebar').height() - $(this).prev('.ui-dialog-buttonpane').height() - 34);
                $(this).width($(this).prev('.ui-dialog-titlebar').width() + 2);
            },
            open: function () {
                $('.page_elerecordList').show();
                $('.page_searchEleRecordList').hide();
            },
            close: function () {
                $('.page_elerecordList').hide();
                for (var i = 1; i <= numberforinsert; i++) {
                    document.getElementById("elerecordtable").deleteRow(1);
                }
            },
        });
    });

    //即時控制頁面
    $(".btn_setting_control").click(function () {
        $(".dialog_control").dialog({
            title: "卸載設定",
            dialogClass: "dlg-no-close",
            width: 1000,
            height: 600,
            resizable: false,
            resizeStop: function () {
                $(this).height($(this).parent().height() - $(this).prev('.ui-dialog-titlebar').height() - $(this).prev('.ui-dialog-buttonpane').height() - 34);
                $(this).width($(this).prev('.ui-dialog-titlebar').width() + 2);
            },
        });
    });

    //一般反應設定頁面-button
    $('.btn_toSettingPage').click(function (e) {
        $(this).parents("div.dialog").find('.page_demandAnalysis').hide();
        $(this).parents("div.dialog").find('.page_meterSetting').show();
    });

    //返回一般反應設定頁面-button
    $('.btn_toDemandPage').click(function (e) {
        $(this).parents("div.dialog").find('.page_meterSetting').hide();
        $(this).parents("div.dialog").find('.page_demandAnalysis').show();
    });

    //新增開機設定頁面-button
    $('.open_setting').click(function () {
        $(this).parents("div.dialog").find('.page_meterList').hide();
        $(this).parents("div.dialog").find('.page_newMeter').show();
    })

    //返回開機設定頁面-button
    $('.btn_toMeterList').click(function () {
        $(this).parents("div.dialog").find('.page_meterList').show();
        $(this).parents("div.dialog").find('.page_newMeter').hide();
    });

    //用電紀錄頁面讀取
    $('.open_search').click(function () {
        console.log(typeof ($("#thedate2").val()));
        $.ajax({
            type: "GET",
            url: "/api/v1.0/search/record",
            dataType: 'json',
            async: false,
            data: {
                "circuit": $("#a").val().toString(),
                "date": $("#thedate").val().toString(),
                "dateend": $("#thedate2").val().toString(),
            },
            success: function (response) {
                for (var idx = 0; idx < response.length; idx++) {
                    var data = response[idx];
                    insert_ele_record_search(data);
                }
                forsearchelerecord = response.length;
            },
            error: function (response) {
                alert("用電紀錄資料讀取逾時");
            }
        });
        $(this).parents("div.dialog").find('.page_searchEleRecordList').show();
        $(this).parents("div.dialog").find('.page_elerecordList').hide();
    });

    //返回電表紀錄頁面-button
    $('.btn_toeleRecordList').click(function () {
        console.log(forsearchelerecord);
        $(this).parents("div.dialog").find('.page_elerecordList').show();
        $(this).parents("div.dialog").find('.page_searchEleRecordList').hide();
        for (var i = 1; i <= forsearchelerecord; i++) {
            document.getElementById("searchelerecordtable").deleteRow(1);
        }
    });

    $('#thedate').datepicker({
        dateFormat: 'yy-mm-dd'
    });

    $('#thedate2').datepicker({
        dateFormat: 'yy-mm-dd'
    });

    //即時推播
    // set callback handlers
    client.onConnectionLost = onConnectionLost;
    client.onMessageArrived = onMessageArrived;
    // connect the client
    client.connect({
        onSuccess: onConnect
    });
    // called when the client connects
    function onConnect() {
        // Once a connection has been made, make a subscription and send a message.
        console.log("onConnect");
        //The operator # Means listen all topic after UID
        client.subscribe(gateway_uid + "/client_response/#");
    }
    // called when the client loses its connection
    function onConnectionLost(responseObject) {
        if (responseObject.errorCode !== 0) {
            console.log("onConnectionLost:" + responseObject.errorMessage);
        }
    }
    // called when a message arrives
    function onMessageArrived(message) {
        console.log("onMessageArrived:" + message);
        /*
        mandatory The name of the destination to which the message is to be sent (for messages about to be sent)
        or the name of the destination from which the message has been received. (for messages received by the onMessage function).
        */
        console.log("onMessageArrived destinationName:" + message.destinationName);
        //read only The payload as an ArrayBuffer.
        // console.log("onMessageArrived payloadBytes:" + message.payloadBytes);
        //read only The payload as a string if the payload consists of valid UTF-8 characters.
        console.log("onMessageArrived payloadString:" + message.payloadString);
        var rs = message.destinationName.split("/");
        var data = JSON.parse(message.payloadString);
        if (rs[2] == "offload") {
            if (rs[3] == "update") {
                if (data[0]['available'] == "true") {
                    $("#group_cmn-toggle-" + data[0]['group']).prop("checked", true);
                }
                if (data[0]['available'] == "false") {
                    $("#group_cmn-toggle-" + data[0]['group']).prop("checked", false);
                }
                if (data[0]['boolean'] == "true") {
                    $("#gateway_cmn-toggle-" + data[0]['group']).prop("checked", true);
                }
                if (data[0]['boolean'] == "false") {
                    $("#gateway_cmn-toggle-" + data[0]['group']).prop("checked", false);
                }
            }
        }

    }
});

// 每月每日最大需量資料--讀取
function drawdiagram(dialog, meterData) {
    //該月每日最大需量
    var spinner_daily_maxDemand = show_spinner(dialog.find(".tabpane_dailyPeak"));
    $.ajax({
        type: "GET",
        url: "/api/v1.0/peak_period_everyday_in_month",
        dataType: 'json',
        data: {
            "address": meterData["address"],
            "channel": meterData["ch"],
            "datetime": dialog.find(".datetime").val() + '-01',
        },
        success: function (response) {
            if (response.length == 0)
                $('#tabpane_dailyPeak_' + meterData["address"] + '_' + meterData["ch"]).html('<div style="font-size:30px;text-align:center">此時段無資料</div>')
            else {
                daily_maxDemand(dialog, meterData, response);
            }
            remove_spinner(spinner_daily_maxDemand);
        },
        error: function () {
            alert('no  每日最大需量 data');
        }
    });
}

//開機設定資料 table_frame [query/settings]
function insert_open_initset(data) {
    var row = $('<thead id="' + data["id"] + '">\
                    <tr>\
                    <th class="model" width="70">' + data["model"] + '</th>\
                    <th class="address">' + data["address"] + '</th>\
                    <th class="ch">' + data["ch"] + '</th>\
                    <th class="speed">' + data["speed"] + '</th>\
                    <th class="circuit">' + data["circuit"] + '</th>\
                    <th class="pt" >' + data["pt"] + '</th>\
                    <th class="ct">' + data["ct"] + '</th>\
                    <th class="meter_type">' + data["meter_type"] + '</th>\
                    <th width="280px"><button class="btn btn-danger delete" type="button" href="#">刪除</button>\
                    <button class="btn btn-warning update" type="button" href="#">更新</button></th>\
                    </tr>\
                    </thead>').appendTo(".table_meter");
};

// 現在時間
function startTime(type) {
    var today = new Date(); //定義日期對象
    var yyyy = today.getFullYear(); //通過日期對象的getFullYear()方法返回年
    var MM = today.getMonth() + 1; //通過日期對象的getMonth()方法返回年
    var dd = today.getDate(); //通過日期對象的getDate()方法返回年
    var hh = today.getHours(); //通過日期對象的getHours方法返回小時
    var mm = today.getMinutes(); //通過日期對象的getMinutes方法返回分?
    var ss = today.getSeconds(); //通過日期對象的getSeconds方法返回秒

    // 如果分?或小時的值小於10，則在其值前加0，比如如果時間是下午3點20分9秒的話，則顯示15：20：09
    MM = checkTime(MM);
    dd = checkTime(dd);
    mm = checkTime(mm);
    ss = checkTime(ss);
    var day; //用於保存星期（getDay()方法得到星期編號）
    if (today.getDay() == 0) day = "星期日";
    if (today.getDay() == 1) day = "星期一";
    if (today.getDay() == 2) day = "星期二";
    if (today.getDay() == 3) day = "星期三";
    if (today.getDay() == 4) day = "星期四";
    if (today.getDay() == 5) day = "星期五";
    if (today.getDay() == 6) day = "星期六";
    switch (type) {
        case '1':
            $('.nowDateTimeSpan-demend').html(yyyy + "-" + MM + "-" + dd + " " + hh + ":" + mm + ":" + ss + "   " + day);
            setTimeout('startTime("1")', 1000); //每一秒中重新加載startTime()方法
            break;
        case '2':
            return yyyy + "-" + MM + "-" + dd + " " + hh + ":" + mm + ":" + ss;
    }
}

function checkTime(i) {
    if (i < 10)
        i = "0" + i;
    return i;
}

// 開機設定-->更新
function update_submit() {}

//用電紀錄資料取得
function insert_ele_record(data) {
    var row = $('<thead id="' + data['id'] + '">\
                    <tr>\
                    <td>' + data['id'] + '</td>\
                    <td>' + data['demand_value'] + '</td>\
                    <td>' + data['circuit'] + '</td>\
                    <td>' + data['created_at'] + '</td>\
                    </tr>\
                  </thead>').appendTo(".table_elerecord");
};

//用搜尋電紀錄資料取得
function insert_ele_record_search(data) {
    var row = $('<thead id="' + data['id'] + '">\
                    <tr>\
                    <td>' + data['id'] + '</td>\
                    <td>' + data['demand_value'] + '</td>\
                    <td>' + data['circuit'] + '</td>\
                    <td>' + data['created_at'] + '</td>\
                    </tr>\
                    </thead>').appendTo(".table_searchelerecord");
};

//loading
function show_spinner(div) {
    $(div).empty();
    return $('<div class="spinner"> \
                <div class="rect1"></div> \
                <div class="rect2"></div> \
                <div class="rect3"></div> \
                <div class="rect4"></div> \
                <div class="rect5"></div> \
                </div>').appendTo(div);
}

function remove_spinner(spinner) {
    spinner.remove();
}

var speed = "1000";
var timer = 0;
var pause = "5000";

//即時需量值資料讀取
function realtime_demand(dialog, meterData) {
    console.log(meterData["address"]);
    console.log(meterData["ch"]);
    $.ajax({
        type: "GET",
        url: "/api/v1.0/demand_min",
        dataType: 'json',
        data: {
            "address": meterData["address"],
            "channel": meterData["ch"],
        },
        success: function (response) {
            dialog.find('.real_demandtext > .realtime_power').html(response["demand_min"]);
        },
        error: function () {
            swal('即時需量值讀取失敗', 'error');
            alert("no data");
        }
    });
}

//multiple meter insert to demand_analyze page
function update_meterPage(meterData) {
    var dialog = $(' <div class="col-sm-12 page_meterSetting" style="display:none;">\
                    <i class="fa fa-reply fa-2x btn_toDemandPage" aria-hidden="true"></i>\
                    <div class="row">\
                        <div class="col-lg-12">\
                            <h1 class="page-header">更新開機設定</h1>\
                        </div>\
                        <!-- /.col-lg-12 -->\
                    </div>\
                    <div class="dialog container-fluid">\
                        <form method="POST" accept-charset="UTF-8">\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>機型:</strong>\
                                        <select class="form-control meter_update_model" name="model">\
                                            <option value="PM100">PM100</option>\
                                            <option value="PM200-A">PM200-A</option>\
                                            <option value="PM200-B">PM200-B</option>\
                                            <option value="PM200-C">PM200-C</option>\
                                            <option value="PM200-STD">PM200-STD</option>\
                                            <option value="PM210-4-A">PM210-4-A</option>\
                                            <option value="PM210-4-B">PM210-4-B</option>\
                                            <option value="PM210-4-C">PM210-4-C</option>\
                                            <option value="PM210-4-STD" selected="selected">PM210-4-STD</option>\
                                            <option value="PM210-A">PM210-A</option>\
                                            <option value="PM210-B">PM210-B</option>\
                                            <option value="PM210-C">PM210-C</option>\
                                            <option value="PM210-P-A">PM210-P-A</option>\
                                            <option value="PM210-P-B">PM210-P-B</option>\
                                            <option value="PM210-P-C">PM210-P-C</option>\
                                            <option value="PM210-P-STD">PM210-P-STD</option>\
                                            <option value="PM210-STD">PM210-STD</option>\
                                            <option value="PM210-X-A">PM210-X-A</option>\
                                            <option value="PM210-X-B">PM210-X-B</option>\
                                            <option value="PM210-X-C">PM210-X-C</option>\
                                            <option value="PM210-X-STD">PM210-X-STD</option>\
                                            <option value="PM250-4-A">PM250-4-A</option>\
                                            <option value="PM250-4-B">PM250-4-B</option>\
                                            <option value="PM250-4-C">PM250-4-C</option>\
                                            <option value="PM250-4-STD">PM250-4-STD</option>\
                                            <option value="PM250-4-專案">PM250-4-專案</option>\
                                            <option value="PM250-S-A">PM250-S-A</option>\
                                            <option value="PM250-S-B">PM250-S-B</option>\
                                            <option value="PM250-S-C">PM250-S-C</option>\
                                            <option value="PM250-S-STD">PM250-S-STD</option>\
                                            <option value="PM250-S-專案">PM250-S-專案</option>\
                                            <option value="PM250-X-A">PM250-X-A</option>\
                                            <option value="PM250-X-B">PM250-X-B</option>\
                                            <option value="PM250-X-C">PM250-X-C</option>\
                                            <option value="PM250-X-STD">PM250-X-STD</option>\
                                            <option value="PM250-X-專案">PM250-X-專案</option>\
                                            <option value="保留">保留</option>\
                                            <option value="Polaris-120-A">Polaris-120-A</option>\
                                            <option value="Polaris-120-B">Polaris-120-B</option>\
                                            <option value="Polaris-120-C">Polaris-120-C</option>\
                                            <option value="Polaris-240-A">Polaris-240-A</option>\
                                            <option value="Polaris-240-B">Polaris-240-B</option>\
                                            <option value="Polaris-240-C">Polaris-240-C</option>\
                                            <option value="Polaris-P103">Polaris-P103</option>\
                                            <option value="Polaris-P153">Polaris-P153</option>\
                                            <option value="Polaris-P202">Polaris-P202</option>\
                                            <option value="Polaris-P204">Polaris-P204</option>\
                                            <option value="Polaris-P205">Polaris-P205</option>\
                                            <option value="Polaris-P206">Polaris-P206</option>\
                                            <option value="Polaris-P252">Polaris-P252</option>\
                                            <option value="Polaris-P254">Polaris-P254</option>\
                                            <option value="Polaris-P255">Polaris-P255</option>\
                                            <option value="Polaris-P256">Polaris-P256</option>\
                                            <option value="Polaris-P302">Polaris-P302</option>\
                                            <option value="Polaris-P304">Polaris-P304</option>\
                                            <option value="Polaris-P305">Polaris-P305</option>\
                                            <option value="Polaris-P306">Polaris-P306</option>\
                                            <option value="SMB350-4-A">SMB350-4-A</option>\
                                            <option value="SMB350-4-B">SMB350-4-B</option>\
                                            <option value="SMB350-4-C">SMB350-4-C</option>\
                                            <option value="SMB350-8-A">SMB350-8-A</option>\
                                            <option value="SMB350-8-B">SMB350-8-B</option>\
                                            <option value="SMB350-8-C">SMB350-8-C</option>\
                                            <option value="SMB350-8-S">SMB350-8-S</option>\
                                            <option value="SMB350-8-專案型">SMB350-8-專案型</option>\
                                        </select>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>位址:</strong>\
                                        <input placeholder="1~255" class="meter_address form-control" name="address" type="text" value="1">\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>頻道:</strong>\
                                        <input placeholder="1~15" class="meter_channel form-control" name="ch" type="text" value="1">\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>傳送速率:</strong>\
                                        <select class="form-control meter_speed" name="speed"><option value="1200">1200</option><option value="2400">2400</option><option value="4800">4800</option><option value="9600" selected="selected">9600</option></select>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>迴路:</strong>\
                                        <input placeholder="1~72" class="meter_circuit form-control" name="circuit" type="text" value="1">\
                                        <em>(不能重複)</em>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-12 col-sm-12 col-md-4 text-left">\
                                    <div class="btn btn-primary btn_updateMeter">更新</div>\
                                </div>\
                            </div>\
                        </form>\
                    </div>\
                </div>\
            </div>\*/').appendTo('page_meterList');
}

//開機設定Box-frame(Cloud)
function meter(meterData) {
    var meter_box = $('<div  class="col-lg-3 col-md-3 col-sm-12 col-xs-12 ' + meterData["address"] + '_' + meterData["ch"] + '"> \
                        <div class="info-box red-bg">\
                        <div class="count">' + meterData["model"] + " " + meterData["address"] + '/' + meterData["ch"] + '</div><br>\
                        <button type="button" class="btn btn-info col-md-12" style="border-radius:10px;">\
                            <div style="font-size: 18px ; font-family:Microsoft JhengHei;">用電資訊</div>\
                        </button> \
                        </div>\
                    </div>').appendTo(".list_meters");
    var dialog =
        $('<div class="dialog dialog_model" style="display:none;" meter_channel="' + meterData["ch"] + '"meter_address=' + meterData["address"] + '" title="用電資訊" role="dialog">\
                <!--用電資訊-->\
                <div class="page_demandAnalysis">\
                    <!-- Modal content-->\
                    <!-- 目前時間與即時需量值 header-->\
                    <div class="container-fluid">\
                        <div class="row">\
                            <font>\
                                <h4 style="font-size: 15px; font-weight:bold; float:left;"><span class="nowDateTimeSpan-demend"></span>\
                            </font>\
                        </div>\
                        <div class="row" style="display:block">\
                            <div class="real_power" >\
                                <h4 class="real_demandtext">\
                                    即時需量值：<span class="realtime_power"></span>KW(每分鐘更新)</h4>\
                            </div>\
                        </div>\
                        <div class="dateframe">\
                            <input type="text" style="width :0; height: 0; border:none;">\
                            <input type="text" class="datetime" placeholder="請選擇年、月份、日">\
                            <input type="button" class="btn_loadGraph" value="確定">\
                        </div>\
                    </div>\
                    <div class="col-sm-12">\
                        <div class="tabpane_dailyPeak" id="tabpane_dailyPeak_' + meterData["address"] + '_' + meterData["ch"] + '">\
                        </div>\
                        <div class="tabpane_dailyPeak_page">\
                            <div><i class="fa fa-reply btn_todaily_demand pull-right" aria-hidden="true"></i></div>\
                            <div class="tabpane_dailyPeak1" id="tabpane_dailyPeak1_' + meterData["address"] + '_' + meterData["ch"] + '"></div>\
                        </div>\
                    </div>\
                </div>\
        ').appendTo($("#page-wrapper"));
    dialog.parents(".ui-dialog-title").css("background", "blue");
    var button = meter_box.find("button");
    button.click(function () {
        var timer = null;
        dialog.dialog({
            dialogClass: "dlg-no-close",
            width: 1000,
            height: 600,
            resizeStop: function () {
                $(this).height($(this).parent().height() - $(this).prev('.ui-dialog-titlebar').height() - $(this).prev('.ui-dialog-buttonpane').height() - 34);
                $(this).width($(this).prev('.ui-dialog-titlebar').width() + 2);
            },
            open: function () {
                // 定時讀取即時需量值
                timer = setInterval(function () {
                    realtime_demand(dialog, meterData);
                }, pause);
                drawdiagram(dialog, meterData);
                $(this).find('.page_meterSetting').hide();
                $(this).find('.page_demandAnalysis').show();
                $(this).find('.page_meterSetting').hide();
            },
            close: function () {
                $(this).find('.page_demandAnalysis').hide();
                $(this).find('.page_meterSetting').show();
                $(this).find('.realtime_power').empty();
                clearInterval(timer);
            },
        });
    });


    //輸入時間設定
    dialog.find('.datetime').datepicker({
        changeMonth: true,
        changeYear: true,
        dateFormat: 'yy-MM',
        showButtonPanel: true,
        maxDate: 0,
        minDate: "-23m",
        onClose: function (dateText, inst) {
            $(this).datepicker('setDate', new Date(inst.selectedYear, inst.selectedMonth, inst.selectedDay));
        }
    }, ).datepicker('setDate', new Date());
    $(".datetime").focus(function () {
        $(".ui-datepicker-calendar").hide();
    });

    //一般反應設定頁面
    dialog.find('.btn_toSettingPage').click(function (e) {
        $(this).parents("div.dialog").find('.page_demandAnalysis').hide();
        $(this).parents("div.dialog").find('.page_meterSetting').show();
    });
    //每日最大需量區間折線圖
    dialog.find('.btn_todaily_demand').click(function (e) {
        $(this).parents("div.dialog").find('.tabpane_dailyPeak_page').hide();
        $(this).parents("div.dialog").find('.tabpane_dailyPeak').show();
    });
    dialog.find('.btn_loadGraph').click(function () {
        drawdiagram(dialog, meterData);
    });
    $('.datetime.hasDatepicker > .ui-datepicker-calendar').css("display", "none");
}

//開機設定Box-frame(Gateway)
function meter_gateway(meterData) {
    var meter_box = $('<div  class="col-lg-3 col-md-3 col-sm-12 col-xs-12"> \
                        <div class="info-box red-bg">\
                        <div class="count">' + meterData["model"] + " " + meterData["address"] + '/' + meterData["ch"] + '</div><br>\
                        <button type="button" class="btn btn-info col-md-12" style="border-radius:10px;">\
                            <div style="font-size: 18px ; font-family:Microsoft JhengHei;">用電資訊</div>\
                        </button> \
                        </div>\
                    </div>').appendTo(".list_meters");

    var meter_circuit = meterData["circuit"];

    var button = meter_box.find("button");
    button.click(function () {
        var timer = null;
        var ctx = document.getElementById('myChart');
        var i = 0;
        let x = new Array(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
        let y = new Array(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);

        function a() {
            var time = new Date();
            for (i = 0; i < 30; i++) {
                x[i] = x[i + 1];
                y[i] = y[i + 1];
            }
            console.log(1);
            x[30] = time;
            $.ajax({
                type: "GET",
                url: "/api/v1.0/getnew/record",

                dataType: 'json',
                data: {
                    "circuit": meter_circuit.toString(),
                },
                beforeSend: function (response) {},
                success: function (response) {
                    console.log(response);
                    if (response) {
                        y[30] = response[0]['demand_value'];
                    } else {
                        y[30] = 0;
                    }
                },
                error: function (response) {
                    swal('error', response['state'], 'error');
                }
            });
            console.log(2);
            var myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13], x[14], x[15], x[16], x[17], x[18], x[19], x[20], x[21], x[22], x[23], x[24], x[25], x[26], x[27], x[28], x[29]],
                    datasets: [{
                        label: '需量即時監控圖 (單位: Watt)',
                        data: [y[0], y[1], y[2], y[3], y[4], y[5], y[6], y[7], y[8], y[9], y[10], y[11], y[12], y[13], y[14], y[15], y[16], y[17], y[18], y[19], y[20], y[21], y[22], y[23], y[24], y[25], y[26], y[27], y[28], y[29]]
                    }]
                }
            });
            console.log(3);
        }
        $(".dialog_meterChart").dialog({
            title: "需量即時監控圖",
            dialogClass: "dlg-no-close",
            width: 1000,
            height: 700,
            open: function () {
                timer = setInterval(a, 3000);
                $('.page_meterChart').show();
            },
            close: function () {
                clearInterval(timer);
                $('.page_meterChart').hide();
            },
        });
    });
}