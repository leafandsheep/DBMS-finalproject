var file_data = "";
var MODEL_TYPE_SWITCH = "1"
var MODEL_TYPE_DIM = "0"

$(document).ready(function () {
    console.log(gateway_uid);

    get_init_node();
    get_init_group();
    get_init_scene();
    node_update_modal();
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
        var rs = message.destinationName.split("/");
        var state_color = '';
        var data = JSON.parse(message.payloadString);
        if (rs[2] == 'node') {
            if (rs[3] == "insert") {
                for (i in data) {
                    ((data[i]['node_state'] > 0) || (data[i]['node_state'] == "ON")) ? (state_color = 'rgb(100, 250, 65)') : (state_color = 'gray');
                    $(".row.node_list").append(node_frame(data[i], state_color));
                    var NodeElement = $('.row.node_list').find('.card.text-center.node_frame').sort(node_frame_sort);
                    $(".card.text-center.node_frame").remove();
                    $(".row.node_list").prepend(NodeElement);
                }
            } else if (rs[3] == "update") {
                for (i in data) {
                    ((data[i]['node_state'] > 0) || (data[i]['node_state'] == "ON")) ? (state_color = 'rgb(100, 250, 65)') : (state_color = 'gray');
                    $(".card.text-center.node_frame_" + data[i]['id']).remove();
                    $(".row.node_list").append(node_frame(data[i], state_color));
                    var NodeElement = $('.row.node_list').find('.card.text-center.node_frame').sort(node_frame_sort);
                    $(".card.text-center.node_frame").remove();
                    $(".row.node_list").prepend(NodeElement);
                }
            } else if (rs[3] == "delete") {
                $('.node_frame_' + data[0]['id']).remove();
            }
        } else if (rs[2] == 'group') {
            if (rs[3] == "insert") {
                (data['group_state'] == "ON") ? (state_color = 'steelblue') : (state_color = 'gray');
                $(".row.group_list").prepend(group_frame(data[0], state_color));
                var GroupElement = $('.row.group_list').find('.card.text-center.group_frame').sort(group_frame_sort);
                $(".card.text-center.group_frame").remove();
                $(".row.group_list").prepend(GroupElement);
            } else if (rs[3] == "update") {
                (data[0]['group_state'] == "ON") ? (state_color = 'steelblue') : (state_color = 'gray');
                $(".card.text-center.group_frame_" + data[0]['id']).remove();
                $(".row.group_list").prepend(group_frame(data[0], state_color));
                var GroupElement = $('.row.group_list').find('.card.text-center.group_frame').sort(group_frame_sort);
                $(".card.text-center.group_frame").remove();
                $(".row.group_list").prepend(GroupElement);
            } else if (rs[3] == "delete") {
                $('.group_frame_' + data[0]['id']).remove();
            }
        } else if (rs[2] == 'scene') {
            if (rs[3] == "insert") {
                $(".row.scene_list").append(scene_frame(data[0], state_color));
                var SceneElement = $('.row.scene_list').find('.card.text-center.scene_frame').sort(scene_frame_sort);
                $(".card.text-center.scene_frame").remove()
                $(".row.scene_list").prepend(SceneElement);
            } else if (rs[3] == "update") {
                $(".row.scene_list").append(scene_frame(data[0], state_color));
                $(".card.text-center.scene_frame_" + data[0]['scene_number']).remove()
                var SceneElement = $('.row.scene_list').find('.card.text-center.scene_frame').sort(scene_frame_sort);
                $(".card.text-center.scene_frame").remove()
                $(".row.scene_list").prepend(SceneElement);
            } else if (rs[3] == "delete") {
                $('.scene_frame_' + data[0]['scene_number']).remove();
            }
        }
    }
});
//燈控設定頁面--資料排序------------------------------------------------------------------------------------------------------------------------
function node_frame_sort(a, b) {
    a_address = parseInt($(a).attr('id').split("/")[0]);
    a_node = parseInt($(a).attr('id').split("/")[1]);
    b_address = parseInt($(b).attr('id').split("/")[0]);
    b_node = parseInt($(b).attr('id').split("/")[1]);
    return (a_address * 100 + a_node * 10) > (b_address * 100 + b_node * 10);
}

function scene_frame_sort(a, b) {

    return a.className.match(/scene_frame_\d/)[0] > b.className.match(/scene_frame_\d/)[0];
}

function group_frame_sort(a, b) {

    return $(a).find('.number').text() > $(b).find('.number').text();
}
//燈控設定頁面--資料插入------------------------------------------------------------------------------------------------------------------------
function get_init_node() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/node/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        async: false,
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            response = response.sort(function (a, b) {
                return a.gateway_address * 100 + a.node * 10 > b.gateway_address * 100 + b.node * 10 ? 1 : -1;
            });
            for (item in response) {
                insert_device_initset('node', response[item]);
            }
            $(".row.node_list").append('\
                        <a  data-toggle="modal" data-target="#node_insert" title="新增點位"style="cursor:pointer;" >\
                        <div class="card text-center" style="border: 5px solid lightgray;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;">\
                        <div class="card-body">\
                            <div  align="center" class="">\
                                <i class="fa fa-plus-square-o fa-4x" style="align-items: center; display: flex;height: 160px;justify-content: center;width: 100%;cursor:pointer;"  aria-hidden="true"></i>\
                                <div class = "count-number"style="font-weight: bold;font-size:20px" ></div>\
                        </div></div></div></a>\
                                ');
        },
        error: function () {
            swal({
                title: '點位設定',
                type: 'error'
            });
        }
    })
}

function get_init_group() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/group/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        async: false,
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            response = response.sort(function (a, b) {
                return a.group_num > b.group_num ? 1 : -1;
            });
            for (item in response) {
                insert_device_initset('group', response[item]);
            }
            $(".row.group_list").append('<a  data-toggle="modal" onclick="insert_group_node_initset()" data-target="#group_insert" title="新增群組" style="cursor:pointer;">\
                        <div class="card text-center" style="border: 5px solid lightgray;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;">\
                        <div class="card-body">\
                            <div  align="center" class="" >\
                                <i class="fa fa-plus-square-o fa-4x" style="align-items: center; display: flex;height: 160px;justify-content: center;width: 100%;cursor:pointer;" aria-hidden="true"></i>\
                                <div class = "count-number"style="font-weight: bold;font-size:20px" ></div>\
                        </div></div></div></a>\
                                ');
        },
        error: function () {
            swal({
                title: '群組設定',
                type: 'error'
            });
        }
    })
}

function get_init_scene() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/scene/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        async: false,
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            for (item in response) {
                insert_device_initset('scene', response[item]);
            }
            $(".row.scene_list").append('\
                        <a data-toggle="modal" onclick="insert_scene_node_initset()"data-target="#scene_insert" title="新增場景">\
                        <div class="card text-center" style="cursor:pointer;border: 5px solid lightgray;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;">\
                        <div class="card-body">\
                            <div align="center" class="">\
                                <i class="fa fa-plus-square-o fa-4x" style="align-items: center; display: flex;height: 168px;justify-content: center;width: 100%;cursor:pointer;" aria-hidden="true"></i>\
                                <div class = "count-number"style="font-weight: bold;font-size:20px" ></div>\
                        </div></div></div></a>\
                                ');
        },
        error: function () {
            swal({
                title: '場景設定',
                type: 'error'

            });
        }
    })
}
//燈控設定頁面--點位、群組、場景框----------------------------------------------------------------------------------------------------------------
function insert_device_initset(value, data) {
    if (value == "node") {
        ((data['node_state'] > 0) || (data['node_state'] == "ON")) ? (state_color = 'rgb(100, 250, 65)') : (state_color = 'gray');
        $(".row.node_list").append(node_frame(data, state_color));
    } else if (value == "group") {
        (data['group_state'] == "ON") ? (state_color = 'steelblue') : (state_color = 'gray');
        $(".row.group_list").append(group_frame(data, state_color));
    } else if (value == "scene") {
        $(".row.scene_list").append(scene_frame(data));
    }
}

function node_frame(data, state_color) {
    node_frame_content = '<div class="card text-center node_frame node_frame_' + data['id'] + '" style="border: 5px solid #e69393;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;" id="' + data['gateway_address'] + '/' + data['node'] + '">\
                            <div><i class="fa  fa-times fa-2x  float-right" onclick="node_delete(this)" ' + 'id="' + data['id'] + '"value="' + data['node'] + '" style="cursor: pointer;" aria-hidden="true" title="刪除此點位"></i></div>\
                            <div class="card-body">\
                                <div id="' + data['node_state'] + '" align="center" class="" ">\
                                    <button type="button"  style="background-color:' + state_color + ';" ' + 'id="' + data['id'] + '" onclick="realtime_node_state(this)"  class="rounded' + ' node_realtime_' + data['id'] + '" value="' + data['node_state'] + '">' + data['node_state'] + '</button>\
                                    <div class = "node_name count-number"style="font-weight: bold;font-size:20px" >' + '<span>' + data['node_name'] + '<br>' + data['model'] + ' : ' + data['gateway_address'] + '/' + data['node'] + '</span>' + '</div>\
                                <div id="' + data['gateway'] + '">\
                                    <button class="btn btn-warning" data-target="#node_update" onclick="node_update_initset(this)" value="' + data['id'] + '"  id="update" href="#node">點位更新</button>\
                                </div>\
                            </div>\
                            </div>\
                        </div>';
    return node_frame_content
}

function group_frame(data, state_color) {
    group_frame_content = '<div class="card text-center group_frame group_frame_' + data['id'] + '" style="border: 5px solid #e69393;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;">\
                                <div><i class="fa  fa-times fa-2x  float-right" onclick="group_delete(this)" ' + 'id="' + data['id'] + '" style="cursor: pointer;" aria-hidden="true" title="刪除此群組"></i></div>\
                                <div class="card-body">\
                                    <div class="group_number" id="' + data['group_state'] + '" align="center" ">\
                                        <span class="number">' + data['group_num'] + '</span><br>\
                                        <button type="button" style="background-color:' + state_color + ';" ' + 'id="' + data['id'] + '" onclick="realtime_group_state(this)" value="' + data['group_state'] + '"  class="rounded-group group_realtime_' + data['id'] + '">' + data['group_state'] + '</button>\
                                        <div class="count-number" style="font-weight: bold;font-size:20px" >' + '<span class="group_name">' + data['group_name'] + '</div>\
                                    <div><button class="btn btn-warning" type="button" onclick="group_update_modal(this)" data-target="#group_update" id="update" value="' + data['id'] + '"  id="update" href="#group">群組更新</button></div>\
                                    </div>\
                                </div>\
                            </div>';
    return group_frame_content
}

function scene_frame(data) {
    scene_frame_content = '<div class="card text-center scene_frame scene_frame_' + data['scene_number'] + '" style="border: 5px solid #e69393;padding: 7px;border-radius: 25px;margin:1px;width: 9.5rem;">\
                        <div><i class="fa  fa-times fa-2x  float-right" onclick="scene_delete(this)" ' + 'id="' + data['scene_number'] + '" style="cursor: pointer;" aria-hidden="true" title="刪除此場景"></i></div>\
                        <div class="card-body">\
                            <div  align="center" >\
                                      <span class="number">' + data['scene_number'] + '</span><br>\
                                <button type="button" style="background-color:gray;" ' + 'id="' + data['scene_number'] + '" onclick="realtime_scene_state(this)"  class="rounded-scene"></button>\
                            <div class="count-number" style="font-weight: bold;font-size:20px" >' + '<span class="scene_name">' + data['scene_name'] + '</div>\
                            <div>\
                                <button class="btn btn-warning" type="button" onclick="scene_update_modal(this)" data-target="#scene_update" id="update" value="' + data['scene_number'] + '" id="update" href="#scene">場景更新</button>\
                            </div>\
                        </div></div></div>';
    return scene_frame_content
}
//燈控設定頁面---------------------------------------即時控制--------------------------------------------------------------------------
function realtime_group_state(this_group) {
    group_id = $(this_group).attr('id');
    group_state = $(this_group).val();
    $.ajax({
        type: "GET",
        url: "/api/v1.0/device/realtime_group_state",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            'group_id': group_id,
            'group_state': group_state
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            swal('設定成功', "ok", 'success')
        },
        error: function (response) {
            swal('失敗', "failed", 'error')
        }
    });
}

function realtime_node_state(this_node) {
    node_id = $(this_node).attr('id');
    node_state = $(this_node).val();
    console.log(node_id, node_state);
    if (node_state == "OFF" || node_state == "ON") {
        $.ajax({
            type: "GET",
            url: "/api/v1.0/device/realtime_node_state",
            dataType: 'json',
            data: {
                'gateway_uid': gateway_uid,
                'node_id': node_id,
                'node_state': node_state
            },
            beforeSend: function () {
                swal({
                    title: 'Wait...',
                    showConfirmButton: false,
                    allowOutsideClick: false
                });
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                swal('設定成功', "ok", 'success')
            },
            error: function (response) {
                swal('失敗', "failed", 'error')
            }
        });
    } else {
        swal({
            title: '設定此點位燈光強度',
            html: '<input style="width:30%"  min="0" max="100" step="1" value="' + node_state + '" class="light swal2-input" placeholder="" type="text" maxlength="3" onkeyup="value=value.replace(/[^\\d]/g,\'\')",style="display: block;">',
            showCancelButton: true,
            confirmButtonText: 'Submit',
            allowOutsideClick: false,

        }).then(function (result) {
            value = $('.light.swal2-input').val()
            if (value < 0 || value > 100)
                return swal('數值輸入範圍錯誤', "failed", 'error')
            $.ajax({
                type: "GET",
                url: "/api/v1.0/device/realtime_node_state",
                dataType: 'json',
                data: {
                    'gateway_uid': gateway_uid,
                    'node_id': node_id,
                    'node_state': node_state,
                    'node_state_value': value
                },
                beforeSend: function () {
                    swal({
                        title: 'Wait...',
                        showConfirmButton: false,
                        allowOutsideClick: false
                    });
                },
                success: function (response) {
                    swal('設定成功', "ok", 'success')
                    if (role == "Cloud")
                        response = JSON.parse(response);
                    if (response['state_change'] == 0) {
                        $(this_node).parent().attr('id', response['state_change']);
                        $(this_node).css('background-color', 'gray');
                        $(this_node).text(response['state_change']);
                        $(this_node).val(response['state_change']);
                    } else if (response['state_change'] >= 0) {
                        $(this_node).parent().attr('id', response['state_change']);
                        $(this_node).css('background-color', '#64fa41');
                        $(this_node).text(response['state_change']);
                        $(this_node).val(response['state_change']);
                    }
                },
                error: function (response) {
                    swal('失敗', "failed", 'error')
                }
            });

        })
    }
}

function realtime_scene_state(this_scene) {
    scene_number = $(this_scene).attr('id');
    console.log(scene_number);
    $.ajax({
        type: "GET",
        url: "/api/v1.0/device/realtime_scene_state",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            'scene_number': scene_number,
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response['state'] == "ok") {
                blink(this_scene, 3, 250);
            }
        },
        error: function (response) {
            swal('失敗', "failed", 'error')
        }
    });
}
// 場景閃爍效果
function blink(this_scene, times, speed) {
    if (times > 0 || times < 0) {
        if ($(this_scene).hasClass("blink")) {
            $(this_scene).css('background-color', 'gray');
            $(this_scene).removeClass("blink");
        } else {
            $(this_scene).addClass("blink");
            $(this_scene).css('background-color', '#f88708');
        }
    }
    if (times > 0 || times < 0) {
        setTimeout(function () {
            blink(this_scene, times, speed);
        }, speed);
        times -= .5;
    }
}
//---------------------------------------------------點位--------------------------------------------------------------------------
//點位新增
function node_insert() {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/node_setting/insert",
        dataType: 'json',
        data: {
            "gateway_uid": gateway_uid,
            "node_gateway": $('.node_gateway_insert').val().toString(),
            "node_model": $('.node_model_insert').val().toString(),
            "node_gateway_address": $('.node_gateway_address_insert').val().toString(),
            "node_name": $('.node_name_insert').val().toString(),
            "node": $('.node_node_insert').val().toString()
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response[0]['status'] == "ok") {
                swal({
                    title: '點位設定資料新增成功',
                    type: 'success'
                })
                $("#node_insert").modal("hide");

            } else if (response[0]['status'] == "repeat error") {
                swal({
                    title: '點位設定資料新增失敗，已有相同點位或相同名稱',
                    type: 'error'
                });

                $("#node_insert").modal("hide");
            } else if (response[0]['status'] == "overcount") {
                swal({
                    title: '點位數量已超過256筆',
                    type: 'error'
                });
                $("#node_insert").modal("hide");
            }
        },
        error: function (response) {}
    });
}
//點位更新
function node_update(this_button) {
    node_id = $(this_button).attr('id');
    $.ajax({
        type: "GET",
        url: "/api/v1.0/node_setting/update",
        dataType: 'json',
        data: {
            "gateway_uid": gateway_uid,
            "node_id": node_id,
            "node_gateway": $('.node_gateway_update').val().toString(),
            "node_model": $('.node_model_update').val().toString(),
            "node_gateway_address": $('.node_gateway_address_update').val().toString(),
            "node_name": $('.node_name_update').val().toString(),
            "node": $('.node_node_update').val().toString()
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response['state'] == "repeat error") {
                swal({
                    title: '點位設定資料更新失敗，已有相同點位',
                    type: 'warning'
                })
            } else if (response['state'] == "ok") {
                swal({
                    title: '點位設定資料更新成功',
                    type: 'success'
                })
            }
            $('#node_update').modal("hide");
        },
        error: function (response) {
            swal({
                title: '點位設定資料更新失敗',
                type: 'error'
            })
        }
    });
}
//點位刪除
function node_delete(this_button) {
    swal({
        title: '確定刪除此點位?',
        // text: "You won't be able to revert this!",
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
                url: "/api/v1.0/node_setting/delete",
                dataType: 'json',
                data: {
                    'gateway_uid': gateway_uid,
                    id: this_button.id,
                    gateway: $(this_button).parent().attr('id'),
                    node: $(this_button).attr('value'),
                },
                success: function (response) {
                    if (role == "Cloud")
                        response = JSON.parse(response);
                    if (response["state"] == "ok") {
                        swal('點位刪除成功', response['state'], 'success')
                    } else {
                        swal('點位刪除失敗', response['state'], 'error')
                    }
                },
                error: function (response) {
                    swal('點位刪除失敗', response['state'], 'error')
                }
            });

        }
    })
    // row.remove();

}
//點位點位/更新畫面
function node_update_modal() {
    var row = $('\
        <div class="modal-dialog" role= "document" >\
        <div class="modal-content">\
            <div class="modal-header">\
                <h5 class="modal-title" id="exampleModalLabel">點位資訊</h5>\
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">\
                    <span aria-hidden="true">&times;</span>\
                </button>\
            </div>\
            <div class="modal-body">\
                <div class="dialog container-fluid">\
                    <form method="POST" accept-charset="UTF-8">\
                        <div class="row">\
                            <div class="col-xs-6 col-sm-6 col-md-10">\
                                <div class="form-group">\
                                    <strong>Gateway</strong>\
                                    <input placeholder=""  disabled="disabled" class="node_gateway_update form-control" name="ch" type="text" value="">\
                                                </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>機型:</strong>\
                                        <select class="form-control node_model_update" name="model" disabled="disabled">\
                                            <option value="LT3000">LT3000</option>\
                                            <option value="LT3070">LT3070</option>\
                                            <option value="LT4500">LT4500</option>\
                                        </select>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="row">\
                                <div class="col-xs-6 col-sm-6 col-md-4">\
                                    <div class="form-group">\
                                        <strong>名稱</strong>\
                                        <input placeholder="" class="node_name_update form-control" name="address" type="text" value="">\
                                                </div>\
                                    </div>\
                                </div>\
                                <div class="row">\
                                    <div class="col-xs-6 col-sm-6 col-md-4">\
                                        <div class="form-group">\
                                            <strong>位址</strong>\
                                            <input placeholder="" type="number" min="1" max="254"  maxlength="3"class="node_gateway_address_update form-control" name="ch"value="1" disabled="disabled">\
                                                </div>\
                                        </div>\
                                    </div>\
                                    <div class="row">\
                                        <div class="col-xs-6 col-sm-6 col-md-4">\
                                            <div class="form-group">\
                                                <strong>點位:</strong>\
                                                <input placeholder="" class="node_node_update form-control" min="1" max="64" maxlength="2" onkeyup="number_check(this)" name="ch" type="number" value="1">\
                                                </div>\
                                            </div>\
                                        </div>\
                                    </form>\
                                </div>\
                            </div>\
                            <div class="modal-footer">\
                                <button type="button" onclick="node_update(this)" class="btn btn-primary node_update_id">更新</button>\
                            </div>\
                        </div>\
                    </div>\
                ').appendTo('#node_update');

}
//點位更新/更新資訊
function node_update_initset(this_button) {
    $("#node_update").modal();
    node_id = $(this_button).attr('value');
    $.ajax({
        type: "POST",
        url: "/api/v1.0/node/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            'id': node_id
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            $('.node_gateway_update').val(response[0]['gateway']);
            $('.node_model_update').val(response[0]['model']);
            $('.node_name_update').val(response[0]['node_name']);
            $('.node_gateway_address_update').val(response[0]['gateway_address']);
            $('.node_node_update').val(response[0]['node']);
            $('.node_update_id').attr('id', node_id);
        },
        error: function () {
            swal({
                title: '點位設定',
                type: 'error'
            });
        }
    })
    $('.node_name_update').val("");
    $('.node_gateway_address_update').val("");
    $('.node_node_update').val("");
    $('.node_model_update').val("");
}
//---------------------------------------------------群組---------------------------------------------------
//群組新增
function group_insert() {
    var group = document.getElementsByClassName("alert-node_check");
    var group_data = {};
    if ($('#group_gateway_name').val().toString().length == 0 || $('#group_gateway_num').val().length == 0) {
        return swal({
            title: '群組名稱或編號不得為空',
            type: 'warning'
        })
    } else if (group.length == 0) {
        return swal({
            title: '你必需至少選擇一個點位',
            type: 'warning'
        })
    }
    for (item in group) {
        group_data['' + item + ''] = group[item].id;
    }
    $.ajax({
        type: "GET",
        url: "/api/v1.0/group_setting/insert",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            "group_name": $('#group_gateway_name').val().toString(),
            "group_num": $('#group_gateway_num').val().toString(),
            check_node: group_data,
            "length": group.length
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            console.log(response);
            if (response[1]['state'] == "ok") {
                swal({
                    title: '群組設定資料新增成功',
                    type: 'success'

                })
                var GroupElement = $('.row.group_list').find('.card.text-center.group_frame').sort(group_frame_sort);
                $(".card.text-center.group_frame").remove();
                $(".row.group_list").prepend(GroupElement);
            } else if (response[0]['status'] == "repeat error") {
                if (response[1]['state'] == "failed") {
                    swal({
                        title: '群組設定資料新增失敗，已有相同群組編號或相同名稱',
                        type: 'error'
                    });
                }
            } else if (response[1]['state'] == "overcount") {
                swal({
                    title: '群組數量已超過32筆',
                    type: 'error'
                });
            }
            // 清空
            $('#group_of_node').empty();
            $('#group_gateway_name').val("");
            $('#group_gateway_num').val("");
            $('#group_insert').modal('hide');
        },
        error: function (response) {
            console.log('error');
        }
    });
}
//群組更新
function group_update(this_group) {
    var group = document.getElementsByClassName("update_model_type");
    if ($('#update_group_gateway_name').val().toString().length == 0 || $('#update_group_gateway_num').val().length == 0) {
        return swal({
            title: '群組名稱或編號不得為空',
            type: 'warning'

        })
    } else if (group.length == 0) {
        return swal({
            title: '你必需至少選擇一個點位',
            type: 'warning'

        })
    }
    var group_data = {}
    for (i in group) {
        group_data['' + i + ''] = group[i].id;
    }
    $.ajax({
        type: "GET",
        url: "/api/v1.0/group_setting/update",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            "group_id": $('#update_group_id').val().toString(),
            "group_name": $('#update_group_gateway_name').val().toString(),
            "group_num": $('#update_group_gateway_num').val().toString(),
            check_node: group_data,
            "length": group.length
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response[1]['state'] == "ok") {
                swal({
                    title: '群組設定資料更新成功',
                    type: 'success'
                })
                $('.row.group_list').empty();
                get_init_group();
            } else if (response[0]['status'] == "repeat error") {
                if (response[1]['state'] == "model_type_repeat") {
                    swal({
                        title: '點位機型錯誤',
                        type: 'error'
                    });
                }
                if (response[1]['state'] == "name_number_repeat") {
                    swal({
                        title: '已有相同編號或名稱',
                        type: 'error'
                    });
                }
            }
            $('#update_group_gateway_name').val("");
            $('#update_group_gateway_num').val("");
            $('#update_group_node').empty();
            $('#group_update').modal("hide");
        },
        error: function (response) {
            console.log('error');
        }
    });
}
//群組刪除
function group_delete(this_group) {
    swal({
        title: '確定刪除此群組?',
        // text: "You won't be able to revert this!",
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
                url: "/api/v1.0/group_setting/delete",
                dataType: 'json',
                data: {
                    'gateway_uid': gateway_uid,
                    group_id: this_group.id,
                    // node: this_button.children('.node_node').text()
                },
                beforeSend: function () {
                    swal({
                        title: 'Wait...',
                        showConfirmButton: false,
                        allowOutsideClick: false
                    });
                },
                success: function (response) {
                    if (role == "Cloud")
                        response = JSON.parse(response);
                    if (response["state"] == "ok")
                        swal('群組刪除成功', response['state'], 'success')
                    else {
                        swal('群組刪除失敗', response['state'], 'error')
                    }
                },
                error: function (response) {
                    swal('群組刪除失敗', response['state'], 'error')
                }
            });
        }
    });

}
//群組新增--畫面的點位資訊
function insert_group_node_initset() {
    $('#group_insert').modal();
    $.ajax({
        type: "GET",
        url: "/api/v1.0/node/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (group_node_setting_data) {
            if (role == "Cloud")
                group_node_setting_data = JSON.parse(group_node_setting_data);

            var compare_model = [];
            for (i in group_node_setting_data) {
                compare_model[i] = group_node_setting_data[i]['model'];
            }
            var result_model = compare_model.filter(function (el, i, arr) {
                return arr.indexOf(el) === i;
            });
            $('.row.node_of_node_data_yet').html('');
            $('#group_of_node').html('');
            result_model.sort();
            for (j in result_model) {
                var row1 = $('<div class="card"><div class="card-header bg-light text-dark">' + result_model[j] + '</div>\
            <div class="card-body"><div class="card-block"><div class="row node_check_body_' + result_model[j] + '"></div></div><div><br>').appendTo(".node_of_node_data_yet");
                for (i in group_node_setting_data) {
                    if (result_model[j] == group_node_setting_data[i]['model'] && !group_node_setting_data[i]['group_id']) {
                        var row = $('<div class="col-sm-3 col-6" id="' + group_node_setting_data[i]['id'] + '">\
                  <input type="checkbox" onclick="check_group_of_node(this)" id="node_' + group_node_setting_data[i]['id'] + '"\
                  class = "form-control-custom form-check-input node' + group_node_setting_data[i]['id'] + '"\
                    value = "' + group_node_setting_data[i]['id'] + '" ><label for="node_' + group_node_setting_data[i]['id'] + '">' + group_node_setting_data[i]['node_name'] + '\
                </label></div>').appendTo(".node_check_body_" + result_model[j] + "");
                    }
                }
            }

        },
        error: function () {
            swal({
                title: '群組點位初始設定',
                type: 'error'
            });
        }
    })

}
//群組新增--按下點位
function check_group_of_node(check_node) {
    var node_id = check_node.value;
    var node_name = $(check_node).parent().text();
    document.getElementById("group_of_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 alert-node_check" style = "margin-left:5px;" id = "' + node_id + '">\
    <button type="button" onclick="choesn_group_node_release(this)" class="close alert_node" id = "' + node_id + '" data-dismiss="alert">&times;</button>\
    <span>' + node_name + '</span></div>';
    $("input.node" + node_id).attr("disabled", true);
}
//群組更新--畫面的點位資訊
function group_update_modal(this_button) {
    $('#group_update').modal();
    group_name = $(this_button).parent().parent().find(".group_name").text();
    group_num = $(this_button).parent().parent('.group_number').find('.number').text();
    group_id = $(this_button).attr('value');
    $.ajax({
        type: "GET",
        url: "/api/v1.0/node/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (response_node_data) {
            if (role == "Cloud")
                response_node_data = JSON.parse(response_node_data);
            document.getElementById("update_group_gateway_name").value = group_name.toString();
            document.getElementById("update_group_id").value = group_id.toString();
            document.getElementById("update_group_gateway_num").value = group_num.toString();
            document.getElementById("update_group_node").innerHTML = "";
            document.getElementById("update_group_of_node_data_yet").innerHTML = "";
            var compare_model = [];
            for (var i = 0; i < response_node_data.length; i++) {
                compare_model[i] = response_node_data[i]['model'];
            }
            var result_model = compare_model.filter(function (el, i, arr) {
                return arr.indexOf(el) === i;
            });
            result_model.sort();
            for (var i = 0; i < response_node_data.length; i++) {
                if (response_node_data[i]["group_id"] == group_id)
                    document.getElementById("update_group_node").innerHTML += "<div class='alert alert-success alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type\
                'style = 'margin-left:5px;' id = '" + response_node_data[i]["id"] + "'>\
                " + '<span>' + response_node_data[i]["node_name"] + '</span>' + "<button type='button'  value='" + response_node_data[i]["model"] + "' id = '" + response_node_data[i]["id"] + "'onclick='choesn_group_node_release(this)' class='close choesn_node" + response_node_data[i]["node"] + "' data-dismiss='alert'>&times;</button></div>";
            }
            for (j in result_model) {
                $('<div class="card"><div class="card-header bg-light text-dark">' + result_model[j] + '</div>\
                <div class="card-body"><div class="card-block"><div class="row update_node_check_body_' + result_model[j] + '"></div></div><div><br>').appendTo("#update_group_of_node_data_yet");
                for (var i = 0; i < response_node_data.length; i++) {
                    if (result_model[j] == response_node_data[i]['model']) {
                        $('<div class="col-sm-3 col-6 id="' + response_node_data[i]['id'] + '">\
                      <input type="checkbox" onclick="check_update_group_of_node(this)" id="update_node_' + response_node_data[i]['id'] + '"\
                      class = "form-control-custom form-check-input update_node' + response_node_data[i]['id'] + '"\
                        value="' + response_node_data[i]['id'] + '">' + '<label for="update_node_' + response_node_data[i]['id'] + '">' + response_node_data[i]['node_name'] + '</span>\
                    </label></div>').appendTo(".update_node_check_body_" + result_model[j] + "");
                    }
                    if (result_model[j] == response_node_data[i]['model'] && response_node_data[i]['group_id']) {
                        $('input.update_node' + response_node_data[i]['id']).attr('checked', true);
                        $('input.update_node' + response_node_data[i]['id']).attr('disabled', true);
                    }
                }
            }
        },
        error: function () {
            swal({
                title: '群組更新頁面設定',
                type: 'error'
            });
        }
    })
    $('#update_group_gateway_name').val("");
    $('#update_group_gateway_num').val("");
    $('#update_group_node').empty();
}
//群組更新--按下點位
function check_update_group_of_node(check_node) {
    var node_id = $(check_node).val();
    var node_name = $(check_node).parent().text();
    document.getElementById("update_group_node").innerHTML += '<div class="alert alert-success alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type" style = "margin-left:5px;" id = "' + node_id + '">\
    <button type="button" onclick="choesn_group_node_release(this)" id="' + node_id + '"' + 'class="close update_alert_node" data-dismiss="alert">&times;</button>\
    <span>' + node_name + '</span></div>';
    // 禁用Button
    $("input.update_node" + node_id).attr("disabled", true);
}
//群組更新--更新/新增/取消此群組點位
function choesn_group_node_release(this_node) {
    var node_id = this_node.id;
    $('input.node' + node_id).prop('disabled', false);
    $('input.node' + node_id).attr('checked', false);
    $('input.update_node' + node_id).prop('disabled', false);
    $('input.update_node' + node_id).attr('checked', false);
}
//---------------------------------------------------場景---------------------------------------------------

//場景新增
function scene_insert(this_scene) {
    if ($('#scene_gateway_name').val().toString().length == 0 || $('#scene_gateway_num').val().length == 0) {
        return swal({
            title: '場景名稱或編號不得為空',
            type: 'warning'

        })
    }
    var node_id = document.getElementsByClassName("scene_node_state");
    var state_value = document.getElementsByClassName("node_state_value");
    var node_state = document.getElementsByClassName("alert-node_check");
    var node_state_value = {}
    var scene_node_state = {}
    var check_node_id = {};
    if (node_id.length == 0) {
        swal({
            title: '你必需至少選擇一個點位',
            type: 'warning'
        })
        return;
    }
    for (var i = 0; i < state_value.length; i++) {
        node_state_value['' + i + ''] = state_value[i].textContent.split('%')[0];
        scene_node_state['' + i + ''] = node_state[i].id;
        check_node_id['' + i + ''] = node_id[i].id;
    }
    $.ajax({
        type: "GET",
        url: "/api/v1.0/scene_setting/insert",
        dataType: 'json',
        data: {

            'gateway_uid': gateway_uid,
            'scene_name': $('#scene_gateway_name').val().toString(),
            'scene_number': $('#scene_gateway_num').val(),
            nodevalue: node_state_value,
            check_node_id: check_node_id,
            scene_node_state: scene_node_state,
            "length": node_id.length
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response[0]['state'] == "ok") {
                swal({
                    title: '場景設定資料新增成功',
                    type: 'success'
                })
                $('.row.scene_list').empty();
                get_init_scene();
                $("#check_scene_node").empty();

            } else if (response[0]['state'] == "repeat error") {
                swal({
                    title: '場景設定資料新增失敗，已有相同場景編號',
                    type: 'error'

                });
            } else if (response[0]['state'] == "overcount") {
                swal({
                    title: '場景數量已超過60筆',
                    type: 'error'

                });
            }

            $('#scene_insert').modal("hide");
        },
        error: function (response) {
            console.log('error');
        }
    });
}
//場景更新
function scene_update(this_scene) {
    if ($('#update_scene_gateway_name').val().toString().length == 0 || $('#update_scene_gateway_num').val().length == 0) {
        return swal({
            title: '場景名稱或編號不得為空',
            type: 'warning'

        })
    }
    var a = document.getElementsByClassName("update_scene_node_number");
    var b = document.getElementsByClassName("update_node_state_value");
    var c = document.getElementsByClassName("update_model_type");
    console.log(a, b, c);
    var node_number = {};
    var node_state_value = {}
    var model = {}
    if (c.length == 0) {
        swal({
            title: '你必需至少選擇一個點位',
            type: 'warning'
        })
        return;
    }
    for (var i = 0; i < a.length; i++) {
        node_number['' + i + ''] = a[i].id;
        node_state_value['' + i + ''] = b[i].textContent.split('%')[0];
        model['' + i + ''] = c[i].id;
    }
    console.log(node_number, node_state_value, model);

    $.ajax({
        type: "GET",
        url: "/api/v1.0/scene_setting/update",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            "scene_name": $('#update_scene_gateway_name').val().toString(),
            "scene_number": $('#update_scene_gateway_num').val().toString(),
            "origin_scene_number": $('.scene_update_submit').attr('id'),
            "origin_scene_name": $('.scene_update_submit').attr('value'),
            check_node: node_number,
            value: node_state_value,
            model_type: model,
            "length": a.length
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (role == "Cloud")
                response = JSON.parse(response);
            if (response['state'] == "ok") {
                swal({
                    title: '場景設定資料更新成功',
                    type: 'success'
                })
                $('.row.scene_list').empty();
                get_init_scene();
            } else if (response['state'] == "repeat error") {
                swal({
                    title: '場景設定資料更新失敗，已有相同點位或名稱',
                    type: 'error'

                });
            }
            $('#scene_update').modal("hide");
        },
        error: function (response) {
            console.log('error');
        }
    });
}
//場景-刪除
function scene_delete(this_scene) {
    scene_number = $(this_scene).attr('id');
    swal({
        title: '確定刪除此場景?',
        // text: "You won't be able to revert this!",
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
                url: "/api/v1.0/scene_setting/delete",
                dataType: 'json',
                data: {
                    'gateway_uid': gateway_uid,
                    'scene_num': scene_number,
                },
                beforeSend: function () {
                    swal({
                        title: 'Wait...',
                        showConfirmButton: false,
                        allowOutsideClick: false
                    });
                },
                success: function (response) {
                    if (role == "Cloud")
                        response = JSON.parse(response);
                    if (response["state"] == "ok") {
                        swal('場景刪除成功', response['state'], 'success')
                    } else {
                        swal('場景刪除失敗', response['state'], 'error');
                    }
                },
                error: function (response) {
                    swal('場景刪除失敗', response['state'], 'error')
                }
            });
        }
    })
}
//場景新增--畫面的點位資訊
function insert_scene_node_initset() {
    $('#scene_insert').modal();
    $('#scene_gateway_name').val("");
    $('#scene_gateway_num').val("");
    $.ajax({
        type: "GET",
        url: "/api/v1.0/scene_setting/setting",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (scene_node_setting_data) {
            if (role == "Cloud")
                scene_node_setting_data = JSON.parse(scene_node_setting_data);
            var compare_model = [];
            for (j in scene_node_setting_data[1]) {
                compare_model[j] = scene_node_setting_data[1][j]['model'];
            }
            var result_model = compare_model.filter(function (el, i, arr) {
                return arr.indexOf(el) === i;
            });
            $('.row.scene_node_of_node_data_yet').html('');
            $('#check_scene_node').html('');
            result_model.sort();

            for (j in result_model) {
                $('<div class="card"><div class="card-header bg-light text-dark">' + result_model[j] + '</div>\
                    <div class="card-body"><div class="card-block"><div class="row scene_node_check_body_' + result_model[j] + '"></div></div><div><br>').appendTo(".scene_node_of_node_data_yet");
                for (i in scene_node_setting_data[1]) {
                    if (result_model[j] == scene_node_setting_data[1][i]['model'] && scene_node_setting_data[1][i]['scene_node_state'] == MODEL_TYPE_SWITCH) {
                        $('<div class="col-sm-3 col-6" id="' + scene_node_setting_data[1][i]['scene_node_state'] + '">\
                        <input type="checkbox" onclick="check_scene_of_node(this)" id="scene_' + scene_node_setting_data[1][i]['id'] + '"\
                        class = "form-control-custom form-check-input node' + scene_node_setting_data[1][i]['id'] + '"\
                        value = "' + scene_node_setting_data[1][i]['id'] + '" ><label for="scene_' + scene_node_setting_data[1][i]['id'] + '">' + scene_node_setting_data[1][i]['node_name'] + '</label>\
                        </label><br>\
                        <div class="switch pull-left scene "  align="left" style="margin: 15px 5px 5px 5px;">\
                        <input id="scene_node_cmn-toggle-' + scene_node_setting_data[1][i]['id'] + '"data-group="" class="cmn-toggle cmn-toggle-round ' + 'scene_node_value_' + scene_node_setting_data[1][i]['id'] + '" type="checkbox">\
                        <label for="scene_node_cmn-toggle-' + scene_node_setting_data[1][i]['id'] + '"></label>\
                        </div>\
                        </div>').appendTo(".scene_node_check_body_" + result_model[j] + "");
                    } else if (result_model[j] == scene_node_setting_data[1][i]['model'] && scene_node_setting_data[1][i]['scene_node_state'] == MODEL_TYPE_DIM) {
                        $('<div class="col-sm-3 col-6" id="' + scene_node_setting_data[1][i]['scene_node_state'] + '">\
                        <input type="checkbox" onclick="check_scene_of_node(this)" id="scene_' + scene_node_setting_data[1][i]['id'] + '"\
                        class = "form-control-custom form-check-input node' + scene_node_setting_data[1][i]['id'] + '"\
                            value = "' + scene_node_setting_data[1][i]['id'] + '" ><label for="scene_' + scene_node_setting_data[1][i]['id'] + '">' + scene_node_setting_data[1][i]['node_name'] + '</label>\
                        </label>\
                        <input placeholder="0~100" id="' + scene_node_setting_data[1][i]['scene_node_state'] + '"style="width:50% ;margin: 15px 5px 5px 5px;" type="number" min="0" max="100" class="scene_node_value_' + scene_node_setting_data[1][i]['id'] + ' form-control" name="percent" value="0">\
                        </div>').appendTo(".scene_node_check_body_" + result_model[j] + "");
                    }
                }
            }
        },
        error: function () {
            swal({
                title: '場景設定',
                type: 'error'

            });
        }
    })

}
//場景新增--按下點位
function check_scene_of_node(check_node) {
    var node_id = check_node.value;
    var node_name = $(check_node).parent().children('label').text();
    var node_state = $(check_node).parent().attr('id');
    var percent = 0
    var state = ""
    if (node_state == MODEL_TYPE_DIM) {
        percent = $(check_node).parent().children('.scene_node_value_' + node_id).val()
        document.getElementById("check_scene_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 alert-node_check" style = "margin-left:0px;" id = "' + node_state + '">\
    <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node scene_node_state" id = "' + node_id + '"' + 'data-dismiss="alert">&times;</button>\
    <br><strong style="margin:25px">' + node_name + '</strong><br><strong class ="node_state_value"style="text-align:center">' + percent + '<span style="display:inline;">%</span></strong></div>';
        $("input.node" + node_id).prop("disabled", true);
        $(check_node).parent().children('.scene_node_value_' + node_id).prop("disabled", true)
    } else if (node_state == MODEL_TYPE_SWITCH) {
        state_checked = $(check_node).parent().children().children('#scene_node_cmn-toggle-' + node_id).prop('checked')
        if (state_checked)
            state = "ON", color = "green";
        else
            state = "OFF", color = "red"
        document.getElementById("check_scene_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 alert-node_check" style = "margin-left:0px;" id = "' + node_state + '">\
        <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node scene_node_state" id = "' + node_id + '"' + 'data-dismiss="alert">&times;</button>\
        <br><strong style="margin:25px">' + node_name + '</strong><br><strong class ="node_state_value" style="text-align:center;color:' + color + '">' + state + '</strong></div>';
        $(check_node).parent().children().children('#scene_node_cmn-toggle-' + node_id).prop('disabled', true)
        $("input.node" + node_id).prop("disabled", true);
    }
}
//場景更新--畫面的點位資訊
function scene_update_modal(this_scene) {
    $('#scene_update').modal();
    this_button_scene_name = $(this_scene).parent().parent().find('.scene_name').text();
    this_button_scene_number = $(this_scene).attr("value");
    console.log(this_button_scene_name);
    document.getElementById("update_scene_gateway_name").value = this_button_scene_name.toString();
    document.getElementById("update_scene_gateway_num").value = this_button_scene_number.toString();
    // 畫面清空
    document.getElementById("update_scene_check_node").innerHTML = "";
    document.getElementById("update_scene_node_of_node_data_yet").innerHTML = "";
    //
    $(".scene_update_submit").attr('id', this_button_scene_number);
    $(".scene_update_submit").attr('value', this_button_scene_name);
    $.ajax({
        type: "GET",
        url: "/api/v1.0/scene_setting/update_information",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid
        },
        success: function (response_scene_node_data) {
            if (role == "Cloud")
                response_scene_node_data = JSON.parse(response_scene_node_data);
            var compare_model = [];
            for (j in response_scene_node_data[3]) {
                compare_model[j] = response_scene_node_data[3][j.toString()];
            }
            // 取出現有model
            var result_model = compare_model.filter(function (el, i, arr) {
                return arr.indexOf(el) === i;
            });
            result_model.sort();
            scene_information = response_scene_node_data[2][this_button_scene_number]
            //已選取點位
            for (i in scene_information) {
                if (scene_information[i]["scene_number"] == this_button_scene_number) {
                    if (scene_information[i]['model_type'] == MODEL_TYPE_DIM && scene_information[i]['scene_name'] != "") {
                        document.getElementById("update_scene_check_node").innerHTML += "<div class='alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type\
                            'style = 'margin-left:0px;' id = '" + scene_information[i]['model_type'] + "'>\
                            <button type='button'  value='" + scene_information[i]["node_model"] + "' id = '" + scene_information[i]["node"] + "'onclick='choesn_scene_node_release(this)' class='close alert_node update_scene_node_number" + "' data-dismiss='alert'>&times;</button>\
                            " + '<br><strong style="margin: 25px;" >' + scene_information[i]["node_name"] + '</strong><br><strong class="update_node_state_value"' + " style=" + 'text-align:center' + ">" + scene_information[i]['node_state'] + '<span style="display:inline;">%</span></strong></div>';
                    } else if (scene_information[i]['model_type'] == MODEL_TYPE_SWITCH && scene_information[i]['scene_name'] != "") {
                        if (scene_information[i]['node_state'] == "ON") {
                            document.getElementById("update_scene_check_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type" style = "margin-left:0px;" id = "' + scene_information[i]["model_type"] + '">\
                            <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node update_scene_node_number" id = "' + scene_information[i]["node"] + '"data-dismiss="alert">&times;</button>\
                            <br><strong style="margin: 25px;">' + scene_information[i]["node_name"] + '</strong><br><strong class ="update_node_state_value" style="text-align:center;color:green" >ON</strong></div>';
                            $("input.update_node" + scene_information[i]["node"]).prop("disabled", true);
                            $("input.update_node" + scene_information[i]["node"]).attr("checked", true);
                        } else if (scene_information[i]['node_state'] == "OFF") {
                            document.getElementById("update_scene_check_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type" style = "margin-left:0px;" id = "' + scene_information[i]["model_type"] + '">\
                            <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node update_scene_node_number" id = "' + scene_information[i]["node"] + '"data-dismiss="alert">&times;</button>\
                            <br><strong style="margin: 25px;">' + scene_information[i]["node_name"] + '</strong><br><strong class ="update_node_state_value" style="text-align:center;color:red">OFF</strong></div>';
                            $("input.update_node" + scene_information[i]["node"]).prop("disabled", false);
                            $("input.update_node" + scene_information[i]["node"]).attr("checked", false);
                        }

                    }
                }
            }
            // 目前點位資訊
            for (j in result_model) {
                var row1 = $('<div class="card"><div class="card-header bg-light text-dark">' + result_model[j] + '</div>\
                <div class="card-body"><div class="card-block"><div class="row update_node_check_body_' + result_model[j] + '"></div></div><div><br>').appendTo(".update_scene_node_of_node_data_yet");
                for (i in scene_information) {
                    // 插入現有的場景並限定為disabled
                    if (result_model[j] == scene_information[i]['node_model']) {
                        // 點位型態為SWITCH且有設定此場景
                        if (scene_information[i]['model_type'] == MODEL_TYPE_SWITCH && scene_information[i]['scene_name'] != "") {
                            $('<div class="col-sm-3 col-6" id="' + scene_information[i]['model_type'] + '">\
                                        <input type="checkbox" checked onclick="check_update_scene_of_node(this)" id="update_scene_' + scene_information[i]['node'] + '"\
                                        class = "form-control-custom form-check-input update_node' + scene_information[i]['node'] + '"\
                                        value="' + scene_information[i]['node'] + '">' + '<label for="update_scene_' + scene_information[i]['node'] + '">' + scene_information[i]['node_name'] + '</label>\
                                        <br>\
                                        <div class="switch pull-left scene_update"  align="left" style= "margin: 15px 5px 5px 5px;">\
                                        <input id="scene_update_node_cmn-toggle-' + scene_information[i]['node'] + '"data-group="" class="cmn-toggle cmn-toggle-round ' + 'scene_node_value_' + scene_information[i]['node'] + '" type="checkbox">\
                                        <label for="scene_update_node_cmn-toggle-' + scene_information[i]['node'] + '"></label>\
                                        </div>\
                                        </div>').appendTo(".update_node_check_body_" + result_model[j] + "");
                            // 設定畫面上為開或關
                            if (scene_information[i]['node_state'] == "ON") {
                                $('#scene_update_node_cmn-toggle-' + scene_information[i]['node']).attr("checked", true);
                            } else if (scene_information[i]['node_state'] == "OFF") {
                                $('#scene_update_node_cmn-toggle-' + scene_information[i]['node']).attr("checked", false);
                            }
                            //設定按鈕可用不可用
                            $('input.update_node' + scene_information[i]['node']).prop('disabled', true);
                            $('#scene_update_node_cmn-toggle-' + scene_information[i]['node']).prop("disabled", true);
                            // 點位型態為SWITCH且無設定此場景
                        } else if (scene_information[i]['model_type'] == MODEL_TYPE_SWITCH && scene_information[i]['scene_name'] == "") {
                            $('<div class="col-sm-3 col-6" id="' + scene_information[i]['model_type'] + '">\
                                        <input type="checkbox" onclick="check_update_scene_of_node(this)" id="update_scene_' + scene_information[i]['node'] + '"\
                                        class = "form-control-custom form-check-input update_node' + scene_information[i]['node'] + '"\
                                        value="' + scene_information[i]['node'] + '">' + '<label for="update_scene_' + scene_information[i]['node'] + '">' + scene_information[i]['node_name'] + '</label>\
                                        <br>\
                                        <div class="switch pull-left scene_update"  align="left" style= "margin: 15px 5px 5px 5px;">\
                                        <input id="scene_update_node_cmn-toggle-' + scene_information[i]['node'] + '"data-group="" class="cmn-toggle cmn-toggle-round ' + 'scene_node_value_' + scene_information[i]['node'] + '" type="checkbox">\
                                        <label for="scene_update_node_cmn-toggle-' + scene_information[i]['node'] + '"></label>\
                                        </div>\
                                        </div>').appendTo(".update_node_check_body_" + result_model[j] + "");
                            // 點位型態為DIM且有設定此場景
                        } else if (scene_information[i]['model_type'] == MODEL_TYPE_DIM && scene_information[i]['scene_name'] != "") {
                            $('<div class="col-sm-3 col-6" id="' + scene_information[i]['model_type'] + '">\
                                        <input type="checkbox" checked onclick="check_update_scene_of_node(this)" id="update_scene_' + scene_information[i]['node'] + '"\
                                        class = "form-control-custom form-check-input update_node' + scene_information[i]['node'] + '"\
                                        value="' + scene_information[i]['node'] + '">' + '<label for="update_scene_' + scene_information[i]['node'] + '">' + scene_information[i]['node_name'] + '</label>\
                                        <input placeholder="0~100" id="' + scene_information[i]['scene_node_state'] + '"style="width:50% ;margin: 15px 5px 5px 5px;" type="number" min="0" max="100" class="scene_node_value_' + scene_information[i]['node'] + ' form-control" name="percent" value="' + scene_information[i]['node_state'] + '">\
                                        </div>').appendTo(".update_node_check_body_" + result_model[j] + "");
                            $('input.update_node' + scene_information[i]['node']).prop('disabled', true);
                            $('.scene_node_value_' + scene_information[i]['node']).prop("disabled", true);
                            // 點位型態為DIM且有設定此場景
                        } else if (scene_information[i]['model_type'] == MODEL_TYPE_DIM && scene_information[i]['scene_name'] == "") {
                            $('<div class="col-sm-3 col-6" id="' + scene_information[i]['model_type'] + '">\
                                        <input type="checkbox" onclick="check_update_scene_of_node(this)" id="update_scene_' + scene_information[i]['node'] + '"\
                                        class = "form-control-custom form-check-input update_node' + scene_information[i]['node'] + '"\
                                        value="' + scene_information[i]['node'] + '">' + '<label for="update_scene_' + scene_information[i]['node'] + '">' + scene_information[i]['node_name'] + '</label>\
                                        <input placeholder="0~100" id="' + scene_information[i]['scene_node_state'] + '"style="width:50% ;margin: 15px 5px 5px 5px;" type="number" min="0" max="100" class="scene_node_value_' + scene_information[i]['node'] + ' form-control" name="percent" value="0">\
                                        </div>').appendTo(".update_node_check_body_" + result_model[j] + "");
                            $('input.update_node' + scene_information[i]['node']).prop('disabled', false);
                            $('.scene_node_value_' + scene_information[i]['node']).prop("disabled", false);
                        }
                    }
                }
            }
        },
        error: function () {
            swal({
                title: '場景設定',
                type: 'error'
            });
        }
    })
}
//場景更新--按下點位
function check_update_scene_of_node(check_node) {
    var node_id = check_node.value;
    var model_type = $(check_node).parent().attr('id');
    var node_name = $(check_node).parent().children('label').text();
    if (model_type == MODEL_TYPE_DIM) {
        // 取得調燈數值
        percent_value = $(check_node).parent().children('.scene_node_value_' + node_id).val();
        document.getElementById("update_scene_check_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type" style = "margin-left:0px;" id = "' + model_type + '">\
        <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node update_scene_node_number" id = "' + node_id + '" data-dismiss="alert">&times;</button>\
        <br><strong style="margin: 25px;">' + node_name + '</strong><br><strong class ="update_node_state_value" style="text-align:center">' + percent_value + '<span style="display:inline;">%</span></strong></div>';
        //禁用Button
        $("input.update_node" + node_id).prop("disabled", true);
        $(check_node).parent().children('.scene_node_value_' + node_id).prop("disabled", true)
    }
    if (model_type == MODEL_TYPE_SWITCH) {
        // 狀態檢查
        state_checked = $(check_node).parent().children().children('#scene_update_node_cmn-toggle-' + node_id).prop('checked')
        if (state_checked)
            state = "ON", color = "green";
        else
            state = "OFF", color = "red";
        document.getElementById("update_scene_check_node").innerHTML += '<div class="alert alert-info alert-dismissable col-lg-3 col-md-6 col-sm-12 update_model_type" style = "margin-left:0px;" id = "' + model_type + '">\
            <button type="button" onclick="choesn_scene_node_release(this)" class="close alert_node update_scene_node_number" id = "' + node_id + '" data-dismiss="alert">&times;</button>\
            <br><strong style = "margin: 25px;">' + node_name + '</strong><br><strong class ="update_node_state_value" style="text-align:center;color:' + color + '">' + state + '</strong></div>';
        $(check_node).parent().children('.scene_update').children('#scene_update_node_cmn-toggle-' + node_id).prop('disabled', true)
        //禁用Button
        $("input.update_node" + node_id).prop("disabled", true);
    }
}
//場景更新--更新/新增/取消此場景點位
function choesn_scene_node_release(node) {
    var node_id = node.id;
    // 新增
    $('.node' + node_id).attr('checked', false);
    $('.node' + node_id).attr('disabled', false);
    $('.scene_node_value_' + node_id).prop("disabled", false);
    // 更新
    $("input.update_node" + node_id).attr("disabled", false);
    $("input.update_node" + node_id).attr("checked", false);
    $('#scene_update_node_cmn-toggle-' + node_id).attr("disabled", false);
}