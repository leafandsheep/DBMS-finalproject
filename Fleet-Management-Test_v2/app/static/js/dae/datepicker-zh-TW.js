/* Chinese initialisation for the jQuery UI date picker plugin. */
/* Written by Ressol (ressol@gmail.com). */
(function (factory) {
      if (typeof define === "function" && define.amd) {

            // AMD. Register as an anonymous module.
            define(["../widgets/datepicker"], factory);
      } else {

            // Browser globals
            factory(jQuery.datepicker);
      }
}(function (datepicker) {

      datepicker.regional["zh-TW"] = {
            dayNames: ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
            dayNamesMin: ["日", "一", "二", "三", "四", "五", "六"],
            monthNames: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
            monthNamesShort: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
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
            currentText: "今天",
            closeText: "確定",
            amNames: ["上午", "AM", "A"],
            pmNames: ["下午", "PM", "P"],
            timeFormat: "HH:mm:ss"
      };
      datepicker.setDefaults(datepicker.regional["zh-TW"]);

      return datepicker.regional["zh-TW"];

}));