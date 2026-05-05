var restDays = [];
month_30 = [2, 4, 7, 9];

var week_statement = {};
var weekdate_list = [];

var monthdate_list = [];
var month_statement = {};

var everyMonthWeek_thisday = {};
console.log(everyMonthWeek_thisday);
var everyMonthWeek_statement = {};
var everyMonthWeek_number = [];
var temp_delete = []

$(document).ready(function () {
    festival_information();
    $.ajax({
        type: "GET",
        url: "/api/v1.0/festival_setting/rest_days",
        dataType: "json",
        async: false,
        data: {
            "gateway_uid": gateway_uid
        },
        success: function (data, textStatus, jqXHR) {
            console.log(role);
            if (role == "Cloud")
                data = JSON.parse(data);
            $.each(data, function (index, value) {
                var dateString = formatDate(new Date(value));
                restDays.push(dateString);
            });
        }
    });
    var date_statement = {};
    $("#festival_date").datepicker({
        numberOfMonths: [4, 3],
        dateFormat: 'yy-mm-dd',
        stepMonths: 12,
        showCurrentAtPos: new Date().getMonth(),
        onSelect: function (dateText, datePicker) {
            datePicker.drawMonth += $("#festival_date").datepicker("option", "showCurrentAtPos");
            if (jQuery.inArray(dateText, restDays) == -1) {
                swal({
                    title: '請輸入該節日說明',
                    html: '<input id="date_statement" class="swal2-input">',
                    input: 'select',
                    inputOptions: {
                        'no_repeat': '不重複',
                        'every_week': '每週 星期' + numbertoUpper(new Date(dateText).getDay()),
                        'month_numberweek_date': '每月 第 ' + getMonthWeek(dateText) + ' 個星期' + numbertoUpper(new Date(dateText).getDay()),
                        'every_month': '每月  ' + new Date(dateText).getDate() + ' 號',
                    },
                    showCancelButton: true,
                    confirmButtonText: '確定',
                    cancelButtonText: '取消',
                    showLoaderOnConfirm: true,
                    allowOutsideClick: false,
                }).then(function (value) {
                    var this_date = new Date(dateText);
                    var text = $('#date_statement').val();
                    year = this_date.getFullYear();
                    weekday = this_date.getDay();
                    console.log(this_date, value, text);
                    if (value == "no_repeat") {
                        //日期與說明 date_statement={'2018-05-09:'開幕日','2018-05-10':'閉幕日'}
                        date_statement[dateText.toString()] = $('#date_statement').val();
                        addOrRemoveDate(dateText, value, "");
                    }
                    //  每週這一天
                    else if (value == "every_week") {
                        // 放置說明的文字 week_statement=['2':'國定假日']
                        // 得到周次並將日期填入陣列中型式為 week_list=['2':['2018-05-08']]
                        getWeek_date(this_date, value, weekday, text);
                        addOrRemoveDate(weekdate_list, value);
                    }
                    //  每月這一天
                    else if (value == "every_month") {
                        // 插入每月這一天說日期與說明
                        getMonth_date(this_date, value, text)
                        addOrRemoveDate(monthdate_list, value);
                    } //每月第幾周星期幾
                    else if (value == 'month_numberweek_date') {
                        number_week = getMonthWeek(dateText); // 得到第幾周
                        weekday = new Date(dateText).getDay(); // 星期幾
                        temp_obj = {}
                        temp_obj[number_week.toString()] = weekday.toString(); // 創建第幾周、星期幾
                        // 紀錄第幾周星期幾 everyMonthWeek_number=[{5:4}{1:6}]
                        everyMonthWeek_number.push(temp_obj);
                        // everyMonthWeek_statement=[5:{4:['發薪放假日']}]
                        if (number_week.toString() in everyMonthWeek_statement) {
                            if (weekday.toString() in (everyMonthWeek_statement[number_week.toString()]))
                                return;
                            else
                                everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                        } else {
                            everyMonthWeek_statement[number_week.toString()] = {}
                            everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                        }
                        // everyMonthWeek_statement[number_week.toString()] = {};
                        // everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                        console.log('103', everyMonthWeek_thisday);
                        getMonth_NumberWeek_date(this_date, number_week, weekday);
                        console.log(everyMonthWeek_thisday);
                        addOrRemoveDate(everyMonthWeek_thisday, value)
                    }
                    // 重整日曆
                    datePicker.drawMonth = new Date().getMonth();
                    $("#festival_date").datepicker("refresh");
                })
            } else if (jQuery.inArray(dateText, restDays) != -1) {
                addOrRemoveDate(dateText, "")
            }
        },
        beforeShowDay: function (date) {
            var dateString = formatDate(date)
            var inRestDays = jQuery.inArray(dateString, restDays);
            if (inRestDays != -1)
                return [true, "ui-selected-highlight "];
            return [true, ""];
        },
    });
    $("#btn_festival_save").click(function () {
        // UID
        console.log('#1 gateway_uid', gateway_uid);
        // 所有有選取得日期
        console.log('#4 restDays', restDays);
        // (每周星期幾)說明
        console.log('#9 week_statement', week_statement);
        // (每月幾號的日期)說明
        console.log('#10 month_statement', month_statement);
        // (每月第幾個星期幾)日期
        console.log('#11 everyMonthWeek_thisday', everyMonthWeek_thisday);
        // (每月第幾個星期幾)說明
        console.log('#12 everyMonthWeek_statement', everyMonthWeek_statement);
        // (每月第幾個星期幾)紀錄有哪些第幾周星期幾
        console.log('#13 everyMonthWeek_number', everyMonthWeek_number);

        $.ajax({
            type: "POST",
            url: "/api/v1.0/festival_setting/rest_days",
            data: {
                "gateway_uid": gateway_uid,
                restDays: restDays,
                date_statement: JSON.stringify(date_statement),
                week_statement: JSON.stringify(week_statement),
                month_statement: JSON.stringify(month_statement),
                everyMonthWeek_thisday: JSON.stringify(everyMonthWeek_thisday),
                everyMonthWeek_statement: JSON.stringify(everyMonthWeek_statement),
                everyMonthWeek_number: JSON.stringify(everyMonthWeek_number),
            },
            dataType: "json",
            success: function (data, textStatus, jqXHR) {
                swal({
                    title: '特別節日設定成功',
                    type: 'success'
                })
                window.history.go(0);
                $('.table-bordered.festival').text("");
                $('.table-bordered.festival').html('<thead class="tablerow_festival_setting_list">\
                                    <tr>\
                                        <th>節日</th>\
                                        <th>說明</th>\
                                    </tr>\
                                </thead>');
                festival_information();

            }
        });
    });
});


$("#festival_date").datepicker({
    numberOfMonths: [4, 3],
    dateFormat: 'yy-mm-dd',
    stepMonths: 12,
    showCurrentAtPos: new Date().getMonth(),
    onSelect: function (dateText, datePicker) {
        datePicker.drawMonth += $("#festival_date").datepicker("option", "showCurrentAtPos");
        if (jQuery.inArray(dateText, restDays) == -1) {
            swal({
                title: '請輸入該節日說明',
                html: '<input id="date_statement" class="swal2-input">',
                input: 'select',
                inputOptions: {
                    'no_repeat': '不重複',
                    'every_week': '每週 星期' + numbertoUpper(new Date(dateText).getDay()),
                    'month_numberweek_date': '每月 第 ' + getMonthWeek(dateText) + ' 個星期' + numbertoUpper(new Date(dateText).getDay()),
                    'every_month': '每月  ' + new Date(dateText).getDate() + ' 號',
                },
                showCancelButton: true,
                confirmButtonText: '確定',
                cancelButtonText: '取消',
                showLoaderOnConfirm: true,
                allowOutsideClick: false,
            }).then(function (value) {
                var this_date = new Date(dateText);
                var text = $('#date_statement').val();
                year = this_date.getFullYear();
                weekday = this_date.getDay();
                console.log(this_date, value, text);
                if (value == "no_repeat") {
                    //日期與說明 date_statement={'2018-05-09:'開幕日','2018-05-10':'閉幕日'}
                    date_statement[dateText.toString()] = $('#date_statement').val();
                    addOrRemoveDate(dateText, value, "");
                }
                //  每週這一天
                else if (value == "every_week") {
                    // 放置說明的文字 week_statement=['2':'國定假日']
                    // 得到周次並將日期填入陣列中型式為 week_list=['2':['2018-05-08']]
                    getWeek_date(this_date, value, weekday, text);
                    addOrRemoveDate(weekdate_list, value);
                }
                //  每月這一天
                else if (value == "every_month") {
                    // 插入每月這一天說日期與說明
                    getMonth_date(this_date, value, text)
                    addOrRemoveDate(monthdate_list, value);
                } //每月第幾周星期幾
                else if (value == 'month_numberweek_date') {
                    number_week = getMonthWeek(dateText); // 得到第幾周
                    weekday = new Date(dateText).getDay(); // 星期幾
                    temp_obj = {}
                    temp_obj[number_week.toString()] = weekday.toString(); // 創建第幾周、星期幾
                    // 紀錄第幾周星期幾 everyMonthWeek_number=[{5:4}{1:6}]
                    everyMonthWeek_number.push(temp_obj);
                    // everyMonthWeek_statement=[5:{4:['發薪放假日']}]
                    if (number_week.toString() in everyMonthWeek_statement) {
                        if (weekday.toString() in (everyMonthWeek_statement[number_week.toString()]))
                            return;
                        else
                            everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                    } else {
                        everyMonthWeek_statement[number_week.toString()] = {}
                        everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                    }
                    // everyMonthWeek_statement[number_week.toString()] = {};
                    // everyMonthWeek_statement[number_week.toString()][weekday.toString()] = text
                    console.log('103', everyMonthWeek_thisday);
                    getMonth_NumberWeek_date(this_date, number_week, weekday);
                    console.log(everyMonthWeek_thisday);
                    addOrRemoveDate(everyMonthWeek_thisday, value)
                }
                // 重整日曆
                datePicker.drawMonth = new Date().getMonth();
                $("#festival_date").datepicker("refresh");
            })
        } else if (jQuery.inArray(dateText, restDays) != -1) {
            addOrRemoveDate(dateText, "")
        }
    },
    beforeShowDay: function (date) {
        var dateString = formatDate(date)
        var inRestDays = jQuery.inArray(dateString, restDays);
        if (inRestDays != -1)
            return [true, "ui-selected-highlight "];
        return [true, ""];
    },
});


function addOrRemoveDate(dates, selection) {

    if (selection == "no_repeat" || selection == "") {
        var index = jQuery.inArray(dates, restDays);
        if (index != -1) {
            restDays.splice(index, 1);
        } else {
            restDays.push(dates);
        }
    } else if (selection == "every_week") {
        for (i in dates) {
            var index = jQuery.inArray(dates[i], restDays);
            if (index != -1) {
                delete week_statement[dates[i]];
            } else {
                restDays.push(dates[i]);
            }
        }
    } else if (selection == "every_month") {
        for (i in dates) {
            var index = jQuery.inArray(dates[i], restDays);
            if (index != -1) {
                delete month_statement[dates[i]];
            } else {
                restDays.push(dates[i]);
            }

        }
    } else if (selection == "month_numberweek_date") {
        length = everyMonthWeek_thisday[number_week.toString()][weekday.toString()].length
        console.log('202', everyMonthWeek_thisday[number_week.toString()][weekday.toString()], length);
        for (i = 0; i < length; i++) {
            var index = jQuery.inArray(everyMonthWeek_thisday[number_week.toString()][weekday.toString()][i], restDays);
            if (index != -1) {
                date_index = everyMonthWeek_thisday[number_week.toString()][weekday.toString()].indexOf(everyMonthWeek_thisday[number_week.toString()][weekday.toString()][i]);
                temp_delete.push(date_index);
            } else
                restDays.push(everyMonthWeek_thisday[number_week.toString()][weekday.toString()][i]);
        }
        console.log('211', restDays);
        // 刪除已有被選擇日期
        for (date_index in temp_delete) {
            temp_delete.sort();
            temp_delete.reverse();
            everyMonthWeek_thisday[number_week.toString()][weekday.toString()].splice(temp_delete[date_index], 1);

        }
    }
}

// 格式轉換
function formatDate(date) {
    var year = date.getFullYear();
    var month = pad(date.getMonth() + 1, 2);
    var day = pad(date.getDate(), 2);
    var dateString = year + "-" + month + "-" + day;
    return dateString;
}

// 加0
function pad(num, size) {
    var s = num + "";
    while (s.length < size) s = "0" + s;
    return s;
}

//往下個月日期設定
function month_setting(this_date) {
    var pushDate = new Date(this_date.getTime());
    // 二月
    if (pushDate.getMonth() == 0) {
        var days = new Date(pushDate.getFullYear(), 2, 0).getDate();
        var next_days = new Date(pushDate.getFullYear(), 2, 0).getDate();
        if (pushDate.getDate() > days)
            this_date.setMonth(2);
        else
            this_date.setMonth(pushDate.getMonth() + 1);
    }
    // 四、六、九、十一月
    else if (jQuery.inArray((pushDate.getMonth() + 1), month_30) == -1 && pushDate.getDate() == 31) {
        var month_index = jQuery.inArray((pushDate.getMonth() + 1), month_30);
        this_date.setMonth((pushDate.getMonth()) + 2);
    } else
        this_date.setMonth((pushDate.getMonth()) + 1);
    return this_date
}

// 得到點擊為每周星期幾日期與插入說明
function getWeek_date(this_date, value, weekday, text) {
    // 從今年一月開始處理ex:2018-01-01
    year = this_date.getFullYear();
    this_date.setMonth(0);
    this_date.setDate(1);
    while (this_date.getDay() !== weekday) {
        this_date.setDate(this_date.getDate() + 1);
    }
    while (this_date.getFullYear() === year) {
        var pushDate = new Date(this_date.getTime());
        weekdate_list.push(pushDate.getFullYear() + '-' + pad(pushDate.getMonth() + 1, 2) + '-' + pad(pushDate.getDate(), 2));
        week_statement[(pushDate.getFullYear() + '-' + pad(pushDate.getMonth() + 1, 2) + '-' + pad(pushDate.getDate(), 2)).toString()] = text;
        this_date.setDate(pushDate.getDate() + 7);
    }
}

// 得到點擊為當月幾號日期與插入說明
function getMonth_date(this_date, value, text) {
    year = this_date.getFullYear();
    this_date.setMonth(0);
    //month_statement=['2018-05-11':'生日',2018-05-12'':'他的生日']
    while (this_date.getFullYear() == year) {
        var pushDate = this_date;
        monthdate_list.push(pushDate.getFullYear() + '-' + pad(pushDate.getMonth() + 1, 2) + '-' + pad(pushDate.getDate(), 2));
        month_statement[(pushDate.getFullYear() + '-' + pad(pushDate.getMonth() + 1, 2) + '-' + pad(pushDate.getDate(), 2)).toString()] = text
        this_date == month_setting(pushDate);
    }
}

// 得到點擊為當月第幾周的日期
function getMonth_NumberWeek_date(this_date, number_week, weekday) {
    // 初始化第幾周星期幾
    this_date.setMonth(0);
    this_date.setDate(1);
    year = this_date.getFullYear();
    if (number_week.toString() in everyMonthWeek_thisday) {
        if (weekday.toString() in (everyMonthWeek_thisday[number_week.toString()]))
            return;
        else
            everyMonthWeek_thisday[number_week.toString()][weekday.toString()] = []
    } else {
        everyMonthWeek_thisday[number_week.toString()] = {}
        everyMonthWeek_thisday[number_week.toString()][weekday.toString()] = []
    }
    var pushDate = this_date;
    while (pushDate.getFullYear() == year) {
        if (pushDate.getDay() == weekday && getMonthWeek(pushDate) == number_week) {
            date_string = pushDate.getFullYear() + '-' + pad(pushDate.getMonth() + 1, 2) + '-' + pad(pushDate.getDate(), 2);
            everyMonthWeek_thisday[number_week.toString()][weekday.toString()].push(date_string);
            pushDate.setDate(1);
            pushDate.setMonth(pushDate.getMonth() + 1);
        } else
            pushDate.setDate(pushDate.getDate() + 1);
    }
}

// 得到點擊為當月第幾周
function getMonthWeek(date) {
    /*
        a = d =當前日期
        b = 6 - w =當前週的還有幾天過完（不算今天）
        a + b的和在除以7就是當天是當前月份的第二週
        */
    var date = new Date(date),
        w = date.getDay(),
        d = date.getDate();
    return Math.ceil((d + 6 - w) / 7);
};

// 轉換日期
function numbertoUpper(number) {
    Number_transfer = {
        '1': '一',
        '2': '二',
        '3': '三',
        '4': '四',
        '5': '五',
        '6': '六',
        '0': '日'
    }
    if (number in Number_transfer) {
        return Number_transfer[number.toString()]
    }
}


function initset_festival(response) {
    var date = $.datepicker.formatDate('yy / mm / dd', new Date(response['date']));
    row = $('<thead class="' + response['id'] + '">\
        < tr >\
        <th>' + date + '</th>\
        <th>' + response['statement'] + '</th>\
        </tr >\
        </thead >').appendTo('.table.table-bordered.festival')
}

// //特別節日設定
//特別節日設定
function festival_information() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/festival_setting/information",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            for (item in response)
                initset_festival(response[item]);
        },
        error: function (response) {
            swal('特別節日資訊初始化失敗', response['state'], 'error')
        }
    });
}