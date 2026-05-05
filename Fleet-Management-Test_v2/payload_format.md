### Message_type (訊息種類)

```
REQUEST 	= 　0	(請求)
RESPONSE 	= 　1	(回覆)
ACK		= 　2	(回傳通知)
```

### task_type (任務種類)

```
NO_TASK = None
SWITCH_NODE  = 	0
SWITCH_GROUP = 	1
SWITCH_SCENE = 	2
ADD_DEMAND   = 	3
```

### task_status (任務狀態)
```
CREATED    =    0 	(未執行)
DISPATCHED =    1 	(已派發)
DOING      =    2   (執行中)
SUCCEEDED  =    3 	(任務成功)
FAILED     =    4 	(任務失敗)
TERMINATED =    5 	(任務中止)
```

### SWITCH_NODE
> Server (請求)
```
{
	"header": {
		"message_id": "[encode_id]",
		"message_type": 0,
		"message_timestamp": "2021-02-20T23:13:32.810511+08:00",
		"need_ack": 1,
		"task_sn": 1,
    	"task_type": 0,
		"task_timeout": 1800,
		"task_priority": 0,
		"task_status": 1,
	    "task_created_time": "2021-02-20T23:13:28.810511+08:00"
	},
	"content": {
        "node_sn": 1,
        "node_status": 100,
	}
}
```

>ACK (Gateway 回傳)

```
{
	"header": {
		"message_id": "[encode_id]",
		"message_type": 2,
		"message_timestamp": "2021-02-20T23:30:32.810511+08:00",
		"is_need_ack": 0
		"task_sn": 1,
		"task_status": 1,
		"task_timeout": 1800,
		"task_priority": 0,
		"task_status": 0,
    	"task_type": 2,
	    "task_updated_time": "2021-02-20T23:30:28.810511+08:00"
	},
	"content": {}
}
```

> Gateway (回覆)

```
{
	"header": {
		"message_id": "[encode_id]",
		"message_type": 1,
		"message_timestamp": "2021-02-20T23:30:32.810511+08:00",
		"is_need_ack": 1,
		"task_sn": 1,
    	"task_type": 2,
		"task_timeout": 1800,
		"task_priority": 0,
		"task_status": 3,
	    "task_updated_time": "2021-02-20T23:30:28.810511+08:00"
	},
	"content": {}
}
```

### SWITCH_GROUP
