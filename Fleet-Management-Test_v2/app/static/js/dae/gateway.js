$(document).ready(function () {
    $.ajax({
        type: "GET",
        url: "/api/v1.0/gateway_setting/query",
        dataType: 'json',
        data: {
            'p_id': $('.project_id').attr('id'),
        },
        success: function (response) {
            for (index in response)
                gateway_initset(response[index]);
        },
        error: function (response) {
            swal('Gateway資訊初始化失敗', response['state'], 'error')
        }
    });
    // 下拉式地址
    var conutrys = ['台灣'];
    var conutrySelect = document.getElementById("country-list");
    var update_conutrySelect = document.getElementById("update_country-list");
    var inner = "";
    var update_inner = "";
    for (i in conutrys) {
        inner = inner + '<option id="country-list" value=' + conutrys[i] + '>' + conutrys[i] + '</option>';
    }
    for (i in conutrys) {
        update_inner = update_inner + '<option id="update_country-list" value=' + conutrys[i] + '>' + conutrys[i] + '</option>';
    }
    conutrySelect.innerHTML = inner;
    update_conutrySelect.innerHTML = update_inner;

    var citys = new Array();
    citys[0] = ['臺北市', '基隆市', '新北市', '宜蘭縣', '桃園市', '新竹市', '新竹縣', '苗栗縣', '臺中市', '彰化縣', '南投縣', '嘉義市', '嘉義縣', '雲林縣', '臺南市', '高雄市', '澎湖縣', '金門縣', '屏東縣', '臺東縣', '花蓮縣', '連江縣'];

    function changeCity(index) {
        var Sinner = "";
        var update_Sinner = "";
        for (i in citys[index]) {
            Sinner = Sinner + '<option id="city-list" value=' + citys[index][i] + '>' + citys[index][i] + '</option>';
        }
        for (i in citys[index]) {
            update_Sinner = update_Sinner + '<option id="update_city-list" value=' + citys[index][i] + '>' + citys[index][i] + '</option>';
        }
        var citysSelect = document.getElementById("city-list");
        citysSelect.innerHTML = Sinner;

        var update_citysSelect = document.getElementById("update_city-list");
        update_citysSelect.innerHTML = update_Sinner;

    }
    changeCity(document.getElementById("country-list").selectedIndex);
    changeCity(document.getElementById("update_country-list").selectedIndex);

});
// 現有Gateway
function gateway_initset(response) {
    var row = $('<div class="card gateway ' + response['gateway_id'] + '">\
                <input id="hide_country" style="display:none" value="' + response['country'] + '">\
                <input id="hide_city" style="display:none" value="' + response['city'] + '">\
                <input id="hide_physical_address" style="display:none" value="' + response['physical_address'] + '">\
            <div class="card-header " style="background-color:lightgreen" >\
                <div><h2 class="h5 display" style="display: inline;" id="gateway_name">' + response['gateway_name'] + '</h2><i class="fa fa-times fa-2x  float-right" id="' + response['gateway_id']+'" onclick="delete_gateway(this)" style="cursor: pointer;" aria-hidden="true" title="刪除此Gateway"></i></div>\
            </div>\
            <div class="card-block text-center" id="' + response['gateway_id'] + '">\
            <div class="img-center">\
            <img class="float:center"data-src="example" alt="100%x280" style="height: 150px; width: 70%; display: block;" src="/static/img/gateway.png" data-holder-rendered="true">\
            </div>\
            <form action="/device" method="POST" style="display:inline" >\
        <div class="form-group"  >\
            <input type="text" id="uid" name="uid"  placeholder="閘道uid" value="' + response['uid'] + '" style="display:none"> </div>\
                <button type="submit" class="btn btn-primary"style="cursor: pointer">電錶頁面</button>\
            </form>\
                <button type="button" data-toggle="modal" data-target="#update_gateway" id="' + response['uid'] + '"onclick="update_gateway_info(this)" class="btn btn-warning update_gateway float-right">編輯</button>\
            </div>\
        </div>').prependTo("#gateway_info");
}
//新增Gateway
function new_gateway(this_button) {
    uid = $('#gateway_uid').val();
    name = $('#name').val();
    country = $('#country-list').val();
    city = $('#city-list').val();
    physical_address = $('#physical_address').val();
    console.log(uid, name, country, city, physical_address);
    if (checkisEmpty(name)) {
        return swal({
            title: '電錶名稱不可為空',
            type: 'error',
        });
    } else if (checkisEmpty(uid)) {
        return swal({
            title: '電錶uid不可為空',
            type: 'error',
        });
    }
    $.ajax({
        type: "GET",
        url: "/api/v1.0/gateway_setting/insert",
        dataType: 'json',
        data: {
            'p_id': $('.project_id').attr('id'),
            'uid': uid,
            'name': name,
            'country': country,
            'city': city,
            'physical_address': physical_address
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            response = JSON.parse(response);
            if (response["status"] == "ok") {
                swal({
                    title: 'Gateway新增成功',
                    type: 'success',
                })
                gateway_initset(response);
            } else if (response["status"] == "repeat") {
                swal({
                    title: 'Gateway資訊重複',
                    type: 'error',
                })
            }
            $('#new_gateway').modal('hide');
        },
        error: function (response) {
            swal('Gateway資訊初始化失敗', response['state'], 'error')
        }
    });
}
// 刪除Gatew刪除
function delete_gateway(this_button) {
    gateway_id = $(this_button).attr('id')
    gateway_uid = $('.card.gateway.' + gateway_id).find('.update_gateway').attr('id');
    swal({
        title: '確定刪除此Gateway?',
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
                url: "/api/v1.0/gateway_setting/delete",
                dataType: 'json',
                data: {
                    'gateway_id': gateway_id,
                    'gateway_uid': gateway_uid
                },
                success: function (response) {
                    console.log(response);
                    if (response["status"] == "ok") {
                        swal('Gateway刪除成功', response['status'], 'success')
                        $('.card.gateway.' + gateway_id).remove();
                    }
                },
                error: function (response) {
                    swal('Gateway設定初始化失敗', response['state'], 'error')
                }
            });
        }
    })
}
// Gateway資訊更新頁面
function update_gateway_info(this_button) {
    uid = $(this_button).attr('id');
    id = $(this_button).parent().attr('id');
    name = $('.card.gateway.' + id).find('#gateway_name').text();
    country = $('.card.gateway.' + id).find('#hide_country').val();
    city = $('.card.gateway.' + id).find('#hide_city').val();
    physical_address = $('.card.gateway.' + id).find('#hide_physical_address').val();
    $('#update_gateway_uid').val(uid);
    $('#update_gateway_name').val(name);
    $('.update_gateway_insert').attr('id', id);
    $('#update_country-list').val(country).toString();
    $('#update_city-list').val(city);
    $('#update_physcial_address').val(physical_address);
}
// 更新Gateway
function update_gateway(this_button) {
    uid = $('#update_gateway_uid').val();
    name = $('#update_gateway_name').val();
    id = $('.update_gateway_insert').attr('id')
    country = $('#update_country-list').val().toString();
    city = $('#update_city-list').val();
    physical_address = $('#update_physcial_address').val();
    $.ajax({
        type: "GET",
        url: "/api/v1.0/gateway_setting/update",
        dataType: 'json',
        data: {
            'uid': uid,
            'id': id,
            'name': name,
            'country': country,
            'city': city,
            'physical_address': physical_address
        },
        beforeSend: function () {
            swal({
                title: 'Wait...',
                showConfirmButton: false,
                allowOutsideClick: false
            });
        },
        success: function (response) {
            if (response["status"] == "ok") {
                $('#update_gateway').modal('hide');
                swal('Gateway更新成功', response['status'], 'success')
                $('.card.gateway.' + id).find('#hide_country').val(country);
                $('.card.gateway.' + id).find('#hide_city').val(city);
                $('.card.gateway.' + id).find('#hide_physical_address').val(physical_address);
                $('.card.gateway.' + id).find('#gateway_name').text(name);
                $('.card.gateway.' + id).find('.update_gateway').attr('id', uid);
            } else if (response["status"] == "repeat") {
                swal('專案uid重複', 'repeat', 'error')
            }
            $('#update_gateway').modal('hide');
        },
        error: function (response) {
            swal('Gateway更新失敗', response['status'], 'error')
        }
    });
}
// 空值檢查
function checkisEmpty(value) {
    if (value == "")
        return true
    else
        return false
}