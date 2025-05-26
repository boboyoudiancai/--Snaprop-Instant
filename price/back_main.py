import re
import pandas as pd
from price.careful_selection import careful_selection
from price.RealEstateValuation import RealEstateValuation
from record.record import Record
from database.mysql_manager import MySQLManager


#感觉写的很丑陋，后续可以统一成一个函数
#工具函数
def trans_type():
    #TODO：数据库表的属性添加了交易类型后增加
    return 1


def trans_fitment(str):
    if "精装" in str:
        return 1
    elif "毛坯" in str:
        return 0
    return 0


def trans_floor(str) -> int:
    f = re.findall(r'\d+', str)
    if "低" in str:
        return int(f[0]) // 6
    elif "中" in str:
        return int(f[0]) // 2
    elif "高" in str:
        return 5 * int(f[0]) // 6
    return 0


def trans_green_rate(str) -> float:
    f = re.findall(r'\d+', str)
    if "%" in str:
        return int(f[0]) / 100
    return 0


def back_main(city, house_floor, house_area, house_type, house_decoration, house_year, house_structure,
              house_loc, selection_weights=None):  #TODO：入参数未设置，待粗筛加入后可以只设置前端传来的待估价房屋具体信息
    selction_example = careful_selection(username=MySQLManager()._username, password=MySQLManager()._password,
                                         host=MySQLManager()._host, port=MySQLManager()._port,
                                         database=MySQLManager()._db, table=MySQLManager().get_table(city),
                                         house_floor=house_floor, house_area=house_area, house_type=house_type,
                                         house_decoration=house_decoration, house_year=house_year,
                                         house_structure=house_structure, house_loc=house_loc)
    df = selction_example.selction()
    if not df:
        return [], 0.0
    # print("精筛结果：")
    # # 实例精筛结果直接导入（debug和演示使用）：
    # print(df)
    # 市场比较法：
    # 目标房产信息（这个应该直接从前端/用户传过来，不用从精筛处传过来）
    target_property = {
        "transaction_type": trans_type(),
        "transaction_time": df[0]["transaction_time"],  # 因为默认挂牌，后续还要根据交易类型判断读取哪个时间
        "green_rate": trans_green_rate(df[0]["green_rate"]),
        "built_time": f"{df[0]['house_year']}-1-1",
        "size": float(df[0]['house_area']),
        "fitment": trans_fitment(df[0]['house_decoration']),
        "floor": trans_floor(df[0]['house_floor']),
    }
    # print(target_property)
    # 比较房产信息
    compare_cases = []
    for i in df[1:]:
        tmp = {
            "price": i["u_price"],
            "transaction_type": trans_type(),
            "transaction_time": i["transaction_time"],  # 因为默认挂牌，后续还要根据交易类型判断读取哪个时间
            "green_rate": trans_green_rate(i["green_rate"]),
            "built_time": f"{i['house_year']}-1-1",
            "size": float(i['house_area']),
            "fitment": trans_fitment(i['house_decoration']),
            "floor": trans_floor(i['house_floor']),
        }
        compare_cases.append(tmp)
    valuation_example = RealEstateValuation(weights=selection_weights)
    # 调用方法计算估价
    estimated_price = valuation_example.evaluate(compare_cases, target_property)
    print(estimated_price)
    # 打印结果
    #print(f'估计房价: {int(estimated_price)}元/平米')
    return df, estimated_price  #返回精筛结果和估计房价


# 实例
# if __name__ == "__main__":
#     # 示例权重
#     selection_weights = {
#         'floor': 0.05,
#         'area': 0.05,
#         'type': 0.05,
#         'decoration': 0.05,
#         'year': 0.05,
#         'transaction_time': 0.05
#     }
#     u_id = 17
#     u_record = Record(u_id)
#     u_record.house_location = "兰谷路2777弄1号202室"
#     u_record.city = "上海"
#     u_record.house_area = 136.79
#     u_record.house_type = "2室1厅1厨2卫"
#     u_record.house_year = 2013
#     u_record.house_floor = "低楼层"
#     u_record.house_decorating = "精装"
#     u_record.house_structure = "平层"
#     u_record.green_rate = 0.35
#     df, price = back_main(u_record.city,  u_record.house_floor, u_record.house_area, u_record.house_type, u_record.house_decorating, u_record.house_year, u_record.house_structure, u_record.house_location)
#     print(df)
#     print(price)
