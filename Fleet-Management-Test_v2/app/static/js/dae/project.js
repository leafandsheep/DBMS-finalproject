$(document).ready(function () {
  $.ajax({
    type: 'GET',
    url: '/api/v1.0/project/query',
    dataType: 'json',
    data: {
      account: $('#account').text()
    },
    success: function (response) {
      for (index in response) project_initset(response[index]);
    },
    error: function (response) {
      swal('專案資料取得失敗', response['state'], 'error');
    }
  });
});

//現有專案
function project_initset(response) {
  var row = $('<div class="card project ">\
                <div class="card-header " style="background-color:lightblue" >\
                <i class="fa fa-times fa-2x  float-right" onclick="delete_project(this)" style="cursor: pointer;" aria-hidden="true" title="刪除此專案" id="' + response['project_id'] + '"></i>\
                    <div><div style="overflow:hidden;white-space: nowrap;text-overflow: ellipsis;width:150px" ><h2 class="h5 display project_title_' + response['project_id'] + '" title="' + response['project_name'] + '"style="display: inline;">' + response['project_name'] + '</h2></div></div>\
                </div>\
                <div class="card-block text-center">\
                <div class="img-center">\
                <img class="float:center"data-src="example" alt="100%x280" style="height: 150px; width: 70%; display: block;" src="/static/img/project.png" data-holder-rendered="true">\
                </div>\
                <form action="/gateway_setting" method="POST" style="display:inline">\
                <div class="form-group"  >\
                <input type="text" id="pid" name="pid" placeholder="專案ID" value="' + response['project_id'] + '" style="display:none"> </div>\
                    <button type="submit" class="btn btn-primary"style="cursor: pointer">專案頁面</button>\
                </form>\
                <button type="button" data-toggle="modal" data-target="#update_project" id="' + response['project_id'] + '" onclick="update_project_info(this)" class="btn btn-warning update_project float-right">編輯</button>\
            </div>\
        </div>').prependTo('#project_info');
}

// 新增專案
function new_project(this_project) {
  project_name = $('.project_name_insert').val();
  account = $('#account').text();
  if (checkisEmpty(project_name)) {
    return swal({
      title: '專案名稱不可為空',
      type: 'error'
    });
  }
  $.ajax({
    type: 'GET',
    url: '/api/v1.0/project/insert',
    dataType: 'json',
    data: {
      project_name: project_name,
      account: account
    },
    success: function (response) {
      if (response['status'] == 'ok') {
        $('#new_project').modal('hide');
        swal('專案新增成功', response['status'], 'success');
        project_initset(response);
      } else if (response['status'] == 'repeat') {
        swal('專案名稱重複', response['status'], 'error');
      }
    },
    error: function (response) {
      swal('專案新增失敗', response['state'], 'error');
    }
  });
}

//刪除專案
function delete_project(this_button) {
  p_id = $(this_button).attr('id');
  console.log(p_id);
  swal({
    title: '確定刪除此專案?',
    type: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: '刪除!',
    cancelButtonText: '取消'
  }).then(result => {
    if (result) {
      $.ajax({
        type: 'GET',
        url: '/api/v1.0/project/delete',
        dataType: 'json',
        data: {
          p_id: p_id
        },
        success: function (response) {
          if (response['status'] == 'ok') {
            swal('專案刪除成功', response['status'], 'success');
            $('.card.project.' + p_id).remove();
          }
        },
        error: function (response) {
          swal('專案刪除失敗', response['state'], 'error');
        }
      });
    }
  });
}

// 編輯專案名稱頁面
function update_project_info(this_button) {
  var p_id = $(this_button).attr('id');
  var project_name = $('.project_title_' + p_id).text();
  $('.project_name_update').val(project_name);
  $('.project_name_update').attr('id', p_id);
}

// 更新專案名稱
function update_project(this_button) {
  var update_project_name = $('.project_name_update').val();
  var p_id = $('.project_name_update').attr('id');
  var account = $('#account').text();
  $.ajax({
    type: 'GET',
    url: '/api/v1.0/project/update',
    dataType: 'json',
    data: {
      update_project_name: update_project_name,
      p_id: p_id,
      account: account
    },
    success: function (response) {
      if (response['status'] == 'ok') {
        swal('專案更新成功', response['status'], 'success');
        $('.project_title_' + p_id).attr('title', update_project_name);
        $('.project_title_' + p_id).text(update_project_name);
        $('#update_project').modal('hide');
      } else if (response['status'] == 'repeat') swal('專案名稱重複', response['status'], 'error');
    },
    error: function (response) {
      swal('專案更新失敗', response['state'], 'error');
    }
  });
}

//空值檢查
function checkisEmpty(value) {
  if (value == '') return true;
  else return false;
}


