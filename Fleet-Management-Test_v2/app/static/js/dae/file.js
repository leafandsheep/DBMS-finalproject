var file_data = "";
var FileNotMatch = -1
$(document).ready(function () {
    // 檔案上傳資料取得
    $("#file_upload").on('change', function () {
        // FileReader 物件
        var FReader = new FileReader();
        var file = document.getElementById('file_upload').files[0];
        //使用utf8邊碼讀取
        FReader.readAsText(file);
        // 檔案加載完成後執行此動作
        FReader.onloadend = function (event) {
            file_data = event.target.result;
        }
    })
});

// 可接受的附檔名
function checkfile(sender) {
    // 可接受的副檔名
    var ValidExists = [".json"];
    var FileName = sender.value;
    FileType = FileName.substring(FileName.lastIndexOf('.'));
    if (ValidExists.indexOf(FileType) == FileNotMatch) {
        swal("檔案類型錯誤，可接受的副檔名有：" + ValidExists.toString(), "", 'warning');
        sender.value = null;
    }
}

// 檔案資料上傳
function file_upload() {
    //判斷有無資料
    if (file_data == "") {
        return swal('請選擇要匯入的檔案', "", 'warning')
    }
    $.ajax({
        type: "GET",
        url: "/api/v1.0/file/upload",
        dataType: 'json',
        data: {
            'gateway_uid': gateway_uid,
            'file_data': file_data,
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
                swal('檔案匯入成功', response['state'], 'success');
            } else if (response["state"] == "file_error") {
                swal('檔案內容有誤', 'failed', 'warning')
            }
            $(".file_upload").val("");
        },
        error: function (response) {
            swal({
                title: '檔案匯入失敗',
                type: 'error'
            })
        }
    });
    $(".file_upload").val("");
}

function fileExport() {
    var file_list = document.getElementsByClassName('file_select');
    file_export = {}
    // 取得檔名清單
    for (var i = 0, j = 0; i < file_list.length; i++) {
        if (file_list[i].checked == true) {
            file_export[j] = file_list[i].value;
            j++;
        }
    }
    // 無選擇檔案
    if (Object.keys(file_export).length == 0) {
        swal('請勾選匯出檔案', "", 'warning')
        return 0;
    } else {
        $.ajax({
            type: "GET",
            url: "/api/v1.0/file/export",
            dataType: 'json',
            data: {
                'gateway_uid': gateway_uid,
                'file_length': Object.keys(file_export).length,
                file_export_list: file_export
            },
            success: function (response) {
                if (role == "Cloud")
                    response = JSON.parse(response);
                // 創建連結並下載
                var dataURL = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(response[0], null, 4));
                var downloadAnchorNode = document.createElement('a');
                downloadAnchorNode.setAttribute("href", dataURL);
                downloadAnchorNode.setAttribute("download", "data.json");
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
                swal('檔案匯出成功', response[1]["state"], 'success').then((result) => {
                    history.go(0);
                });
            },
            error: function (response) {
                swal('檔案匯出失敗', response['state'], 'error')
            }
        });
    }
}