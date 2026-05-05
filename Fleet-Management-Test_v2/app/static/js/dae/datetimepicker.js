$(document).ready(function () {
  var opt = {
    //以下為日期選擇器部分
    dayNames: ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
    dayNamesMin: ["日", "一", "二", "三", "四", "五", "六"],
    monthNames: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
    monthNamesShort: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
    prevText: "上月",
    nextText: "次月",
    weekHeader: "週",
    showMonthAfterYear: true,
    dateFormat: "yy-mm-dd",
    //以下為時間選擇器部分
    timeOnlyTitle: "選擇時分秒",
    timeText: "時間",
    hourText: "時",
    minuteText: "分",
    timezoneText: "時區",
    currentText: "現在時間",
    closeText: "確定",
    amNames: ["上午", "AM", "A"],
    pmNames: ["下午", "PM", "P"],
    timeFormat: "HH:mm:ss"
  };
  var opt = {
    //以下為日期選擇器部分
    dayNames: ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
    dayNamesMin: ["日", "一", "二", "三", "四", "五", "六"],
    monthNames: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
    monthNamesShort: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
    prevText: "上月",
    nextText: "次月",
    weekHeader: "週",
    showMonthAfterYear: true,
    dateFormat: "yy-mm-dd",
    //以下為時間選擇器部分
    timeOnlyTitle: "選擇時分秒",
    timeText: "時間",
    hourText: "時",
    minuteText: "分",
    timezoneText: "時區",
    currentText: "現在時間",
    closeText: "確定",
    amNames: ["上午", "AM", "A"],
    pmNames: ["下午", "PM", "P"],
    timeFormat: "HH:mm:ss"
  };
  $('#datetimepicker1').datetimepicker(opt);
  $('#datetimepicker2').datetimepicker(opt);
  $('#datetimepicker3').datetimepicker({
    format: 'LT'
  });

});