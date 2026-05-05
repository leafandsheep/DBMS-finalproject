from general_gateway.apps.fleet.models.enum.task_type import CMDStatus, CMDType, CMDLayer
from datetime import datetime

class CMD:
    def __init__(
        self,
        cmd_type,
        cmd_sn: int = 0,
        cmd_status: CMDStatus =  CMDStatus.CREATED,
        need_to_return = True,
        content: dict = None,
        cmd_timeout: int = 20,
        cmd_priority: int = 3,
        created_time: datetime = None,
        updated_time: datetime = None,
        source: str = "",
        destination: str = ""
    ):
        if content is None:
            content = {}

        self.cmd_sn = cmd_sn
        self.cmd_status = cmd_status
        self.need_to_return = need_to_return
        self.content = content
        self.cmd_timeout = cmd_timeout
        self.cmd_priority = cmd_priority
        self.created_time = datetime.now().astimezone() if created_time is None else created_time
        self.updated_time = updated_time
        # 20240123 調整
        # self.source = source
        # self.destination = destination

        if isinstance(cmd_type, CMDType):
            self.cmd_type = cmd_type
        else:
            self.cmd_type = CMDType(cmd_type)
        
        #20240123 增加 cmd_layer 設定
        if isinstance(source, CMDLayer):
            self.source = source
        else:
            self.source = CMDLayer(source)
        
        if isinstance(destination, CMDLayer):
            self.destination = destination
        else:
            self.destination = CMDLayer(destination)