import json


def transfer_payload_type(payload, to_type):
    if to_type == type(payload):
        return payload
    else:
        if to_type == dict:
            # 從 str 型態轉 dict 型態
            return json.loads(payload)
        elif to_type == str:
            # 從 dict 型態轉 str 型態
            return json.dumps(payload)
        else:
            raise Exception("Fail message, payload type error (transfer_payload_type)")


def check_topic(topic):
        try:
            server_id, direct, gateway_id = topic.split("/")
            return True
        except BaseException as n:
            print("---(check_topic)---")
            print("Log Fail:", n)

def check_payload(payload: dict):
    try:
        check_dict = {
            'header': [
                'message_id', 'message_type',
                # 'message_status',
                'message_timestamp',
                'is_need_ack',
                'task_sn', 'task_id', 'task_type',
                'task_timeout', 'task_priority',
                'task_status',
                'task_created_time','task_updated_time'
            ],
            'content': []
        }

        for key in payload:
            if key not in check_dict:
                raise Exception("Payload Format Error")

        for element in payload.get('header'):
            if element not in check_dict.get('header'):
                raise Exception("Payload_Header Format Error")

        return True
    except BaseException as n:
        print("(check_payload)")
        print("Log Fail:", n)

def check_content(payload):
    payload = transfer_payload_type(payload, to_type=dict)

    content = payload.get('content')

    if content:
        content_result = True
    else:
        content_result = False

    return content_result
