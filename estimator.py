"""
本模块包含 房产估价 类
"""
import json
import pandas as pd
from record.record import Record
from llm.llm_manager import QianwenManager
from llm.message import MessageType
# from report.report_trans import PDFReport
from report.report_gen import property_report
from datetime import datetime
from config.path_config import REPORT_PATH
from price.back_main import back_main


class Estimator:
    """
    房产估价 类
    """
    HELP_TIP = (
        "您好，我是一个基于大语言模型的房产估价师，\n请告诉我您的目标住宅信息或上传产证信息，\n我可以估计房产单价，并生成一份对应的评估报告。"
    )

    def __init__(self, uid: int, record: Record, lm: QianwenManager):
        """
        :param uid: UID
        :param record:Record
        :param lm: 大模型模块
        """
        self._uid = uid
        self._record = record
        self._lm = lm

        self._missing = None  # 缺失值
        self._isYep: bool = False  # 是否确认
        self._message: str = ""  # 用户消息
        self._result: list[str] = []  # 分析结果（可能有多条）
        self._report: list[str] = []  # 生成报告

    def set_user_message(self, message: str):
        """
        置用户消息
        :param message: 用户消息
        """
        self._message = message

    def get_analyst_result(self) -> list[str]:
        """
        取分析结果
        :return: 分析结果
        """
        return self._result

    def get_report(self) -> list[str]:
        """
        取评估报告
        :return: 评估报告
        """
        return self._report

    def is_report(self) -> bool:
        """
        判断有无评估报告
        :return: 判断结果
        """
        if not self._report:
            return False
        else:
            return True

    def initialize_estimator(self):
        """
        初始化
        :return: 返回状态
        """
        self._result.append(self.HELP_TIP)

    def finalize_estimator(self):
        """
        终止
        """
        self._lm.disconnect_llm()

    def clear_estimator(self):
        """
        清理先前的投资计划
        """
        self._result.clear()

        self._record.clear()

        self._report.clear()

        self._result.append("已清理先前的房屋信息记录")

    def interact_estimator(self):
        """
        一次交互
        :return: 返回状态
        """
        self._result.clear()

        st = self._handel_message()
        if st is False:
            self._result.append("响应错误，请重试")

    def interact_table(self, table_path):
        """
        表格一次交互
        :return: 返回状态
        """
        self._result.clear()
        # 读取所有工作表
        sheets = pd.read_excel(table_path, sheet_name=None)
        user_input = ""
        # 显示每个工作表的数据
        for sheet_name, df in sheets.items():
            # print(f'Sheet: {sheet_name}')
            info = df.to_csv()
            # print(info)
            user_input += info
            # print(df.head())
        st = self.handel_table(user_input)
        if st is False:
            self._result.append("响应错误，请重试")

    def handel_table(self, user_input):
        """
        处理表格
        :return: 返回状态
        """
        llm_result = self._lm.respond_table(user_input, self._record.expected_keys)
        try:
            val_list = json.loads(json.dumps(eval(llm_result)))
        except:
            print(f"预期为二维列表，实际为{llm_result}")
            return False

        error, inputs = self._record.add_data(val_list)
        if not inputs:
            self._result.append("噢哦，提取不到信息~")
            return True
        self._missing = self._record.get_null()
        if not self._missing:
            self._result.append(
                "好的，根据您提供的产证内容，我已经得到了目标住宅的以下信息:\n{info}\n请确认这些信息是否准确无误。如果有任何需要修改或补充的地方，请告诉我。".format(
                    info=inputs))
            return True
        missing_response = self._lm.respond_value(self._missing)
        if error:
            self._result.append("抱歉，出现错误了:\n{info}\n{null}".format(info=inputs, null=missing_response))
            return True
        else:
            self._result.append(
                "好的，根据您提供的产证内容，我已经得到好了目标住宅的以下信息:\n{info}\n{null}".format(info=inputs,
                                                                                                     null=missing_response))
        return True

    def _handel_message(self):
        """（类内调用）
        处理 用户消息
        :return: 返回状态
        """
        llm_class_result = self._lm.classify_message(self._message)
        try:
            message_type = MessageType(int(llm_class_result))
        except ValueError:
            print(f"预期为数字，实际为{llm_class_result}")
            return False

        match message_type:
            case MessageType.null:
                return self._handel_null()

            case MessageType.info:
                return self._handel_info()

            case MessageType.price:
                return self._handel_price()

            case MessageType.report:
                return self._handel_report()

            case MessageType.yep:
                return self._handel_yep()

            case MessageType.ask_info:
                return self._handel_ask_info()

            case _:
                print(f"意外的消息类型{message_type}")
                return False

    def _handel_null(self):
        """（类内调用）
        处理 无效信息
        :return: 返回状态
        """
        self._missing = self._record.get_null()
        llm_result = self._lm.respond_null(self._message)
        self._result.append(llm_result)
        return True

    def _handel_info(self):
        """（类内调用）
        处理 提取信息
        :return: 返回状态
        """
        llm_result = self._lm.respond_info(self._message, self._record.expected_keys)
        try:
            val_list = json.loads(json.dumps(eval(llm_result)))
        except:
            print(f"预期为二维列表，实际为{llm_result}")
            return False

        error, inputs = self._record.add_data(val_list)
        if not inputs:
            self._result.append("噢哦，提取不到信息~")
            return True
        self._missing = self._record.get_null()
        if not self._missing:
            self._result.append(
                "好的，根据您提供的信息，我已经得到了目标住宅的以下信息:\n{info}\n请确认这些信息是否准确无误。如果有任何需要修改或补充的地方，请告诉我。".format(
                    info=inputs))
            return True
        missing_response = self._lm.respond_value(self._missing)
        if error:
            self._result.append("抱歉，出现错误了:\n{info}\n{null}".format(info=inputs, null=missing_response))
            return True
        else:
            self._result.append(
                "好的，根据您提供的信息，我已经得到好了目标住宅的以下信息:\n{info}\n{null}".format(info=inputs,
                                                                                                 null=missing_response))
        return True

    def _handel_price(self):
        """（类内调用）
        处理 房屋估价
        :return: 返回状态
        """
        if (not self._missing) & self._isYep is True:
            df, price = back_main(self._record.city, self._record.house_floor, self._record.house_area,
                                  self._record.house_type,
                                  self._record.house_decorating, self._record.house_year, self._record.house_structure,
                                  self._record.house_location)
            print(df)
            print(price)
            self._record.add_price(price)
            select_result = ""
            index = 0
            for item in df:
                index += 1
                select_result += f"案例{index}: \n"
                select_result += f"户型: {item['house_type']}\n"
                select_result += f"面积: {item['house_area']} 平方米\n"
                select_result += f"楼层: {item['house_floor']}\n"
                select_result += f"朝向: {item['house_direction']}\n"
                select_result += f"装修情况: {item['house_decoration']}\n"
                select_result += f"单价: {item['u_price']} 元/平方米\n"
                select_result += f"总价: {item['t_price']} 万元\n"
                select_result += f"详情链接: {item['detail_url']}\n"
                select_result += "-" * 70
                select_result += "\n"
            self._result.append(
                f"通过筛选得到如下相似案例:\n{select_result}经市场比较法估计，该住宅的单价约为{self._record.price}元/平方米。")
            return True
        return False

    def _handel_report(self):
        """（类内调用）
        处理 评估报告
        :return: 返回状态
        """

        # 有没有缺少图片
        if self._record.map == "":
            self._record.get_map()
        # 产证图片等等
        if not self._record.production_cert_img:
            self._result.append("噢哦，检测到您还没有上传产证图片~")
            return True
        if not self._record.field_img:
            self._result.append("噢哦，检测到您还没有上传实地图片~")
            return True

        if (not self._missing) & self._isYep is True:
            if self._record.price == 0.0:
                df, price = back_main(self._record.city, self._record.house_floor, self._record.house_area,
                                      self._record.house_type,
                                      self._record.house_decorating, self._record.house_year,
                                      self._record.house_structure,
                                      self._record.house_location)
                print(price)
                self._record.add_price(price)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_report.pdf"
            file_path = f"{REPORT_PATH}/{filename}"
            case = property_report(file_path, self._record.house_location)
            case.save_report(self._uid, self._record)
            # 调用生成报告
            self._result.append(f"已为您生成对应的评估报告:")
            # 发送pdf消息
            self._report.clear()
            self._report.append(filename)

            return True
        return False

    def _handel_yep(self):
        """（类内调用）
        处理 确认信息
        :return: 返回状态
        """
        if not self._missing:
            self._isYep = True
            info = self._record.get_record()
            self._result.append(
                f"好的，已确认目标住宅信息如下：\n{info}那接下来您需要我做些什么？我可以估计房产单价，也可以生成一份对应的评估报告^v^")
            return True
        else:
            self._isYep = False
            return False

    def _handel_ask_info(self):
        """（类内调用）
        处理 询问信息
        :return: 返回状态
        """
        try:
            info = self._record.get_record()
            if info is "":
                self._result.append(f"噢哦，目前还没有获得目标住宅信息~")
            else:
                self._result.append(f"好的，已获得目标住宅信息如下：\n{info}")
            return True
        except:
            return False
