var role="";
var gateway_uid
$(document).ready(function () {
    gateway_uid = $('.h5.text-uppercase').attr('id');
    $.ajax({
        type: "GET",
        url: "/api/v1.0/role",
        dataType: 'json',
        async: false,
        success: function (response) {
            role = response;
        },
        error: function () {
            swal({
                title: '角色設定',
                type: 'error'
            });
        }
    })
});