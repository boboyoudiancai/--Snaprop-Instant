"""
本模块包含 消息类型 枚举类
"""
from enum import Enum


class MessageType(Enum):
    """
    消息类型 枚举类
    """
    null = 0
    info = 1
    price = 2
    report = 3
    yep = 4
    ask_info = 5

    def what(self) -> str:
        """
        取得详细含义
        :return: 消息类型的字符串解释
        """
        match self:
            case MessageType.null:
                return "无效信息"
            case MessageType.info:
                return "提取信息"
            case MessageType.price:
                return "房屋估价"
            case MessageType.report:
                return "评估报告"
            case MessageType.yep:
                return "确认信息"
            case MessageType.ask_info:
                return "请求信息"
            case _:
                return str(self)
