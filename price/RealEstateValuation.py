import datetime


class RealEstateValuation:
    def __init__(self, weights=None):
        """
        初始化类，并添加初始的比较房产信息。
        成员:
        key_table(list):房产信息key表
        unit_adjust_table（dict）：默认的因子调整幅度
        time_str_model(str):时间字符串的格式
        target_case（dict）：目标房产的信息
        comparable_case (list): 初始的比较房产信息列表，每个元素为一个字典。
        adjust_price_table(list):修正后的比较房产价格表
        字典中的key：
        price (float): 房产价格（）
        transaction_type(bool):成交类型（0表示成交，1表示挂牌）
        transaction_time(str):成交时间（格式：time_str_model）
        green_rate(float):绿化率
        built_time(str):建成时间（格式：time_str_model）
        floor(int):楼层
        size(float):面积
        fitment(bool):装修情况（0表示毛胚，1表示精装）
        """
        self.key_table = ["price", "transaction_type", "transaction_time", "green_rate", "built_time",
                          "floor", "size", "fitment"]
        self.unit_adjust_table = {
            "transaction_type": 0.05,
            "transaction_time": 0.02,
            "green_rate": 0.05,
            "built_time": 0.03,
            "floor": 0.05,
            "size": 0.05,
            "fitment": 0.05
        }
        self.time_str_model = '%Y-%m-%d'
        self.comparable_cases = []
        self.target_case = {}
        self.adjust_price_table = []
        if weights:
            self.unit_adjust_table.update(weights)

    def update_unit_table(self, unit_table: dict = None):
        """
        更新单位因子调整幅度
        """
        if unit_table == None: return
        for k in unit_table:
            self.unit_adjust_table[k] = unit_table[k]
        return

    def add_comparable_case(self, case: dict):
        """
        添加一个比较房产的信息。
        TODO:或许可以添加缺省赋予默认值（概率最大？），不然就是默认和目标房产相同
        """
        self.comparable_cases.append(case)

    def add_target_case(self, case: dict):
        """
        添加目标房产的信息。
        TODO:或许可以添加缺省赋予默认值
        """
        self.target_case = case

    def adjust(self):
        self.adjust_price_table = []
        for case in self.comparable_cases:
            factor = 1
            for key in case.keys():
                if key not in self.target_case.keys() or self.target_case[key] == None:
                    continue
                elif key == 'transaction_type':
                    diff = -(case[key] - self.target_case[key])
                elif key == 'transaction_time':
                    date_case = datetime.datetime.strptime(case[key], self.time_str_model)
                    date_target = datetime.datetime.strptime(self.target_case[key], self.time_str_model)
                    date_diff = abs((date_case - date_target).days) // 365
                    if date_diff < 1:
                        diff = 0
                    elif date_diff <= 2:
                        diff = 1
                    else:
                        diff = 2
                    if date_case > date_target: diff = -diff  #这里有疑问，房价总趋势不是涨吗，越近交易越贵吧？
                elif key == 'green_rate':
                    green_diff = abs(case[key] - self.target_case[key])
                    if green_diff < 0.3:
                        diff = 0
                    elif green_diff <= 0.5:
                        diff = 1
                    else:
                        diff = 2
                    if case[key] > self.target_case[key]: diff = -diff
                elif key == 'built_time':
                    date_case = datetime.datetime.strptime(case[key], self.time_str_model)
                    date_target = datetime.datetime.strptime(self.target_case[key], self.time_str_model)
                    diff = abs((date_case - date_target).days) // 365 // 5
                    if date_case > date_target: diff = -diff
                elif key == 'floor':
                    diff = abs(case[key] - self.target_case[key]) // 5
                    if case[key] > self.target_case[key]: diff = -diff
                elif key == 'size':
                    size_diff = abs(case[key] - self.target_case[key]) / self.target_case[key]
                    if size_diff < 0.2:
                        diff = 0
                    elif size_diff <= 0.5:
                        diff = 1
                    else:
                        diff = 2
                    if case[key] < self.target_case[key]: diff = -diff
                elif key == 'fitment':
                    diff = -(case[key] - self.target_case[key])
                else:
                    diff = 0
                factor *= (1.00 + diff * self.unit_adjust_table[key])
            try:
                self.adjust_price_table.append(case['price'] * factor)
            except:
                if ("price" not in case.keys()):
                    print(f"第{self.comparable_cases.index(case) + 1}个比较房产缺失价格信息")
                    print(f"该房产信息：{case}")
                pass
            # print(factor,end=' ')
        # print('\n')
        # print(self.adjust_price_table)
        return

    def evaluate(self, com_cases: list, target_case: dict, unit_table: dict = None):
        """
        评估价格
        """
        for case in com_cases:
            self.add_comparable_case(case)
        self.add_target_case(target_case)
        self.update_unit_table(unit_table)
        self.adjust()
        estimated_price = sum(self.adjust_price_table) / len(self.adjust_price_table)
        return estimated_price

#示例
# if __name__ == '__main__':
#     #比较房产信息
#     compare_cases = [
#         {           "price": 77944,
#          "transaction_type": 1,
#          "transaction_time": "2024-05-04",
#                "green_rate": 0.35,
#                "built_time": "1986-1-1",
#                      "size": 36.95,
#                   "fitment": 1,
#                     "floor": 1,
#         },
#         {           "price": 92109,
#          "transaction_type": 1,
#          "transaction_time": "2024-06-04",
#                "green_rate": 0.35,
#                "built_time": "1987-1-1",
#                      "size": 36.37,
#                   "fitment": 1,
#                     "floor": 1,
#         },
#         {           "price": 75897,
#          "transaction_type": 1,
#          "transaction_time": "2024-07-17",
#                "green_rate": 0.35,
#                "built_time": "1984-1-1",
#                      "size": 43.48,
#                   "fitment": 1,
#                     "floor": 1,
#         },
#     ]
#
#     #目标房产信息
#     target_property = {
#          "transaction_type": 1,
#          "transaction_time": "2024-06-24",
#                "green_rate": 0.35,
#                "built_time": "1984-1-1",
#                      "size": 33.08,
#                   "fitment": 1,
#                     "floor": 1,
#     }
#     valuation_example = RealEstateValuation()
#     #调用方法计算估价
#     estimated_price = valuation_example.evaluate(compare_cases, target_property)
#     #打印结果
#     print(f'估计房价: {int(estimated_price)}元/平米')
