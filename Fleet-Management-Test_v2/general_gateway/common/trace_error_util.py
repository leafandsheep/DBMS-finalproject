import sys
import traceback
import colorama
from termcolor import cprint

colorama.init()


def get_function_name():
    return sys._getframe(1).f_code.co_name


def trace_error(error):
    # 取得錯誤類型
    error_class = error.__class__.__name__

    # 取得詳細內容
    error_content = error.args[0]

    # 取得 Call Stack
    cl, exc, tb = sys.exc_info()

    if len(traceback.extract_tb(tb)) > 1:
        for i in enumerate(traceback.extract_tb(tb)):
            print(i)

    # 取得 Call Stack 的最後一筆資料
    last_call_stack = traceback.extract_tb(tb)[-1]

    # 取得發生的檔案名稱
    file_name = last_call_stack[0]

    # 取得發生的行號
    line_num = last_call_stack[1]

    # 取得發生的函數名稱
    function_name = last_call_stack[2]

    error_message = (
        "File: {} \n"
        "Line: {} \n"
        "Function: {} \n"
        "Error Class: [{}] \n"
        "Error Content: {} \n"
    ).format(file_name,
             line_num,
             function_name,
             error_class,
             error_content)

    cprint("-" * 10, "red")
    cprint("Error:", "red", 'on_yellow')
    print(error_message)
    cprint("-" * 10, "red")
