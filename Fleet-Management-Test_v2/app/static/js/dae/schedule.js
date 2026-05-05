$(document).ready(function () {
    //今天狀態
    show_today_state();
    // 上下次控制時間
    show_current_control_time();
    // 排程資訊
    control_time_initset();
    // 群組排程群組資訊
    show_group_information();
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
        console.log("onMessageArrived destinationName:" + message.destinationName);
        console.log("onMessageArrived payloadString:" + message.payloadString);
        var response = message.destinationName.split("/");
        var state_color = '';
        var data = JSON.parse(message.payloadString);
        if (response[2] == 'schedule') {
            if (response[3] == "insert") {
                sort_by_time(data['festival'], data['control_time']);
            }

            if (response[3] == "update") {
                origin_control_time = data['origin_control_time'].split(":")[0] + '_' + data['origin_control_time'].split(":")[1];
                $('.' + data['festival'] + '_control_time.' + origin_control_time).remove();
                sort_by_time(data['festival'], data['control_time']);
            }

            if (response[3] == "delete") {
                control_time = data['control_time'].split(":")[0] + '_' + data['control_time'].split(":")[1];
                $('.' + data['festival'] + '_control_time.' + control_time).remove();
            }
        }
    }
    //修改排程資訊並重整時間排序
    function sort_by_time(festival, control_time) {
        $('#control_time_group_list_' + festival).append(schedule_frame(festival, control_time));
        var ScheduleFrame = $('.' + festival + '_control_time').sort(compare_by_time);
        $('#control_time_group_list_' + festival).empty();
        $('#control_time_group_list_' + festival).append(ScheduleFrame);

    }
    // 重整上下次控制時間狀態
    $('#control_time_event').click(function () {
        show_current_control_time();
    });
    // 新增時間-展開箭頭
    $('#button_for_new_time').click(function () {
        if ($('#new_control_time_table').hasClass('collapse show')) {
            $('#button_for_new_time').find("i").removeClass('fa fa-angle-down')
            $('#button_for_new_time').find("i").addClass('fa fa-angle-left')
        } else {
            $('#button_for_new_time').find("i").removeClass('fa fa-angle-left')
            $('#button_for_new_time').find("i").addClass('fa fa-angle-down')
        }
    });
});

// 控制時間現有設定
function control_time_initset() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/schedule_setting/initset",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            insert_time_initset(response);
        },
        error: function (response) {
            swal({
                title: '排程資訊初始化失敗',
                type: 'error'
            })
        }
    });
}

//排程--插入每個時段資訊
function insert_time_initset(schedule_data) {
    festivals = ['weekday', 'holiday']
    for (festival in festivals) {
        for (item in schedule_data[festivals[festival]]) {
            var control_time = schedule_data[festivals[festival]][item].toString();
            schedule_frame(festivals[festival], control_time);
        }
    }
}

// 控制時間資料框
function schedule_frame(festival, control_time) {
    key_control_time = control_time.split(":")[0] + '_' + control_time.split(":")[1];
    $("#control_time_group_list_" + festival).append('<div class="input-group col-xl-1 col-md-2  col-sm-6 ' + festival + '_control_time ' + key_control_time + '" style="display:inline;margin-top:5px;" id="' + festival + '"><button type="button" onclick="control_time_group_state(this)" data-target="#schedule_group_information_modal" class="btn btn-primary  schedule_group_information" id="' + control_time + '" style="width:140px;border-radius:0px;margin-top: 5px;" >' + control_time + '</button>' + '<button type="button" class="btn btn-danger" style="border-left:0;border-radius:0px;margin-top: 5px;"id="' + control_time + '"  onclick="delete_schedule(this)">x</button></div>');
}

// 控制時間排序
function compare_by_time(a, b) {
    // 排序時間
    return $(a).find('.schedule_group_information').attr('id') > $(b).find('.schedule_group_information').attr('id')
}

// 今天的排程狀態
function show_today_state() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/schedule_setting/today_state",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            $('.festival_state').text(response['today_state'])
            $('.festival_bind').text(response['bind_table'])
        },
        error: function (response) {
            swal('今日特別節日資訊讀取失敗', response['state'], 'error')
        }
    });
}

// 當下的上下次控制時間
function show_current_control_time() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/schedule_setting/prev_next_control_time",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response)
            show_control_time(response);
        },
        error: function (response) {
            swal({
                title: '控制時間顯示失敗',
                type: 'error'
            })
        }
    });
}

//目前群組資訊(顯示在新增控制時間群組表格)
function show_group_information() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/schedule_setting/information",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            schedule_group_information(response);
        },
        error: function (response) {
            swal('排程資訊讀取失敗', response['state'], 'error')
        }
    });
}

//顯示新增群組資訊
function schedule_group_information(schedule_data) {
    for (item in schedule_data) {
        var row = $('<thead class="group_state_id" id="' + schedule_data[item]['group_id'] + '">\
        <tr>' + '<th>' + schedule_data[item]['group_name'] + '</th>\
        <th><input id="state_change ' + schedule_data[item]['group_id'] + '" data-group="" class="cmn-toggle cmn-toggle-round group_state_change" type="checkbox"  >\
        <label id="' + schedule_data[item]['group_id'] + '"for="state_change ' + schedule_data[item]['group_id'] + '"></label> \
        </th><th><input id="no_setting_' + schedule_data[item]['group_id'] + '" data-group="" class="cmn-toggle cmn-toggle-round no_setting" type="checkbox"  >\
        <label id="' + schedule_data[item]['group_id'] + '"for="no_setting_' + schedule_data[item]['group_id'] + '"></label> \
        </th></tr></thead>').appendTo(".schedule");
    }
}

//新增排程
function new_schedule_insert(this_schedule) {
    var bind_festival = document.getElementById("festival");
    var festival = bind_festival.options[bind_festival.selectedIndex].id;

    // 你所選擇的控制時間
    var control_time_checked = $('#control_time input:radio:checked[name="control_time"]').val();

    if (typeof (control_time_checked) == "undefined") {
        return swal({
            title: '請選擇時間',
            type: 'warning'
        })
    } else if (control_time_checked == "control_time") {
        control_time = $('#new_control_time').val();
        if (control_time.length == 0) {
            return swal({
                title: '請正確設定時間',
                type: 'warning'
            })
        }
    } else {
        control_time = control_time_checked.toString();
    }
    // 群組設定資訊
    var Schedule_group_statelist = $(".cmn-toggle.cmn-toggle-round.group_state_change");
    var Schedule_group_setting = $(".cmn-toggle.cmn-toggle-round.no_setting");
    var Schedule_group_list = []
    var Schedule_group_setting_state = "";
    var Schedule_group_id = "";
    // 包裝成物件
    for (var item = 0; item < Schedule_group_statelist.length; item++) {
        Schedule_group_name = $(Schedule_group_statelist[item]).parent().parent().children('th').text();
        // 群組開關
        if (Schedule_group_statelist[item].checked == true)
            Schedule_group_state = "ON"
        else {
            Schedule_group_state = "OFF"
        }
        //群組ID
        Schedule_group_id = $(Schedule_group_statelist[item]).parent().children('label').attr('id');
        // 是否設定
        Schedule_group_setting_state = Schedule_group_setting[item].checked;
        Schedule_group_list.push({
            'group_name': Schedule_group_name,
            'group_state': Schedule_group_state,
            'group_id': Schedule_group_id,
            'group_setting': Schedule_group_setting_state.toString()
        });
    }
    $.ajax({
        type: "POST",
        url: "/api/v1.0/schedule_setting/insert",
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({
            'gateway_uid': gateway_uid,
            'festival': festival,
            'length': length,
            'control_time': control_time,
            'Schedule_group_list': Schedule_group_list
        }),
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response['state'] == "overcount") {
                swal({
                    title: '已設置超過12個時間點',
                    type: 'error'
                })
            } else if (response['state'] == "repeat") {
                swal({
                    title: '時程設置重複',
                    type: 'warning'
                })
            } else {
                swal({
                    title: '時程已設置成功',
                    type: 'success'
                })
            }
        },
        error: function (response) {
            swal('時程設置失敗', response['state'], 'error')
        }
    });
}

//排程--刪除排程
function delete_schedule(this_schedule) {
    var festival = $(this_schedule).parent().attr('id');
    var control_time = $(this_schedule).attr('id');
    swal({
        title: '確定刪除此時程?',
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '刪除!',
        cancelButtonText: '取消',
    }).then((result) => {
        if (result) {
            $.ajax({
                type: "GET",
                url: "/api/v1.0/schedule_setting/delete",
                dataType: 'json',
                data: {
                    'gateway_uid': gateway_uid,
                    'festival': festival,
                    'control_time': control_time
                },
                success: function (response) {
                    if (role == "Cloud")
                        response = JSON.parse(response);
                    if (response["state"] == "ok") {
                        swal({
                            title: '時程刪除成功',
                            type: 'success'
                        })
                    } else {
                        swal('時程刪除失敗', response['state'], 'error')
                    }
                },
                error: function (response) {
                    swal('時程刪除失敗', response['state'], 'error')
                }
            });
        }
    })
}

//排程--更新時程控制
function update_schedule_insert(update_button) {
    // 原本控制時間
    origin_control_time = update_button.id;
    festival = update_button.value;
    var group = "";
    var update_control_time = "";
    update_control_time_checked = $('#update_control_time_selection input:radio:checked[name="update_control_time"]').val();
    // 取得選擇的控制時間update_control_time
    if (update_control_time_checked == "update_control_time") {
        update_control_time = $('#update_control_time_insert').val();
        if (update_control_time.length == 0) {
            return swal({
                title: '請正確設定時間',
                type: 'warning'
            })
        }
    } else
        update_control_time = update_control_time_checked;

    group = $('.cmn-toggle.cmn-toggle-round.state_change.' + festival);
    group_setting = $('.cmn-toggle.cmn-toggle-round.no_setting_' + festival);
    Schedule_group_list = []
    for (var i = 0; i < group.length; i++) {
        group_id = $(group[i]).parent().children('label').attr('id');
        if ($(group[i]).prop('checked') == true) {
            group_state = 'ON'
        } else {
            group_state = 'OFF'
        }
        setting = group_setting[i].checked
        Schedule_group_list.push({
            'group_id': group_id,
            'group_state': group_state,
            'group_setting': setting.toString()
        })
    }
    $.ajax({
        type: "POST",
        url: "/api/v1.0/schedule_setting/update",
        dataType: 'json',
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({
            'gateway_uid': gateway_uid,
            'length': group.length,
            'origin_control_time': origin_control_time,
            'update_control_time': update_control_time,
            'festival': festival,
            'Schedule_group_list': Schedule_group_list
        }),
        async: false,
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            $("#schedule_group_information_modal").modal("hide");
            if (response['state'] == "repeat") {
                swal({
                    title: '時程設置重複',
                    type: 'warning'
                })
            } else {
                swal({
                    title: '時程設置更新成功',
                    type: 'success'
                })
            }
        },
        error: function () {
            swal('時程更新失敗', 'error')
        }
    });
}

// 排程更新資訊
function control_time_group_state(this_time) {
    control_time = this_time.id;
    festival = $(this_time).parent().attr('id');
    $.ajax({
        type: "POST",
        url: "/api/v1.0/schedule_setting/initset",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            'control_time': control_time,
            'festival': festival
        },
        success: function (schedule_data) {
            if (role == "Cloud")
                schedule_data = JSON.parse(schedule_data);
            $("#schedule_group_information_modal").modal();
            $(".schedule_group_state_weekday").remove();
            $(".schedule_group_state_holiday").remove();
            check_update_selection(control_time);
            $('.schedule_update').attr('id', control_time);
            $('.schedule_update').val(festival);
            for (var i = 0; i < schedule_data[festival][control_time.toString()].length; i++) {
                if (schedule_data[festival][control_time.toString()][i]['setting'] == "true")
                    setting = 'checked'
                else
                    setting = ''
                if (schedule_data[festival][control_time.toString()][i]['schedule_group_state'] == "ON")
                    state_setting = "checked";
                else
                    state_setting = '';
                $(".update_schedule_group_title").after('<thead class="schedule_group_state_' + festival + '"><tr>' +
                    '<th>' + schedule_data[festival][control_time.toString()][i]['group_name'] + '</th>\
                    <th>' + schedule_data[festival][control_time.toString()][i]['schedule_group_state'] + '</th>\
                    <th>' + '<input type="checkbox" ' + state_setting + ' class="cmn-toggle cmn-toggle-round state_change ' + festival + '" id="' + schedule_data[festival][control_time.toString()][i]['group_number'] + '_' + control_time.toString() + '"' + '>\
                    <label id="' + schedule_data[festival][control_time.toString()][i]['group_id'] + '" for="' + schedule_data[festival][control_time.toString()][i]['group_number'] + '_' + control_time.toString() + '"></label>\
                    </th>\
                    <th>' + '<input type="checkbox" ' + setting + ' class="cmn-toggle cmn-toggle-round no_setting_' + festival + '" id="' + schedule_data[festival][control_time.toString()][i]['group_number'] + 'setting_' + control_time.toString() + '"' + '>\
                    <label id="' + schedule_data[festival][control_time.toString()][i]['group_id'] + '" for="' + schedule_data[festival][control_time.toString()][i]['group_number'] + 'setting_' + control_time.toString() + '"></label>\
                    </th>\
                    </tr></thead>');
            }
        },
        error: function (response) {
            swal({
                title: '更新群組資訊初始化失敗',
                type: 'error'
            })
        }
    });
}

//星期轉換
function transformUpper(weekday) {
    weeknumber = {
        '0': '星期一',
        '1': '星期二',
        '2': '星期三',
        '3': '星期四',
        '4': '星期五',
        '5': '星期六',
        '6': '星期日'
    }
    if (weekday in Object.keys(weeknumber)) {
        weekday = weeknumber[weekday];
    } else {
        return ""
    }
    return weekday
}

//顯示控制時間
function show_control_time(response) {
    control_time_frame = []
    if (response[0]['state'] == "ok") {
        for (var id = 1; id < 3; id++) {
            if (response[id]['date'] == "")
                control_time_frame[id] = response[id]['control_time'];
            else {
                control_time = (response[id]['control_time']).split(':');
                response[id]['weekday'] = transformUpper(response[id]['weekday']);
                control_time_frame[id] = '<span>' + response[id]['date'].toString().replace(/-/g, '/') + ' ' + response[id]['weekday'] + ' </sapn>' + '&nbsp&nbsp&nbsp&nbsp' + control_time[0] + ':' + control_time[1]
            }
        }
        $('#prev_control_time').html(control_time_frame[1]);
        $('#next_control_time').html(control_time_frame[2]);
    }
}

// 檢查所插入更新頁面的按鈕狀態
function check_update_selection(time_state) {
    if (time_state == "sunset" || time_state == "sunrise") {
        $('#update_control_time_' + time_state).prop('checked', true);
        $('#update_control_time_insert').val(" ");
        $('#update_control_time_insert').hide();
    } else {
        $('#update_control_time_insert').val(time_state);
        $('#update_control_time').prop('checked', true);
        $('#update_control_time_sunset').prop('checked', false);
        $('#update_control_time_sunrise').prop('checked', false);
        $('#update_control_time_insert').show();
    }
}