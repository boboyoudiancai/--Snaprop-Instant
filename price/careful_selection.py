from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pandas as pd
import re
import time
from sklearn.preprocessing import MinMaxScaler
import numpy as np


class careful_selection:
    def __init__(self, username, password, host, port, database, table, house_floor, house_area, house_type,
                 house_decoration, house_year, house_structure, house_loc):
        self.table = table
        # self.id = id
        self.house_floor = house_floor
        self.house_area = house_area
        self.house_type = house_type
        self.house_decoration = house_decoration
        self.house_year = house_year
        self.house_structure = house_structure  # 新增：产品形态
        self.house_loc = house_loc  # 新增：小区
        self.today = time.strftime("%Y-%m-%d", time.localtime())
        #print(self.today)

        uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(uri)

    def house_floor_distinction(self, floor1, floor2):
        if "低" in floor1:
            floor1 = "低"
        elif "中" in floor1:
            floor1 = "中"
        elif "高" in floor1:
            floor1 = "高"
        if "低" in floor2:
            floor2 = "低"
        elif "中" in floor2:
            floor2 = "中"
        elif "高" in floor2:
            floor2 = "高"

        if (floor1 == "低" and floor2 == "低") or (floor1 == "中" and floor2 == "中") or (
                floor1 == "高" and floor2 == "高"):
            return 0
        elif (floor1 == "低" and floor2 == "中") or (floor1 == "中" and floor2 == "低") or (
                floor1 == "中" and floor2 == "高") or (floor1 == "高" and floor2 == "中"):
            return 1
        elif (floor1 == "低" and floor2 == "高") or (floor1 == "高" and floor2 == "低"):
            return 2
        return 3

    def house_area_distinction(self, area1, area2):
        return abs(area1 - area2)

    def house_type_distinction(self, type1, type2):
        w_room = 1
        w_hall = 1
        w_bathroom = 1
        w_kitchen = 1

        pattern = r'(\d+)室(\d+)厅(\d+)厨(\d+)卫'
        match1 = re.search(pattern, type1)
        match2 = re.search(pattern, type2)
        room1, hall1, kitchen1, bathroom1 = int(match1.group(1)), int(match1.group(2)), int(match1.group(3)), int(
            match1.group(4))
        room2, hall2, kitchen2, bathroom2 = int(match2.group(1)), int(match2.group(2)), int(match2.group(3)), int(
            match2.group(4))
        return w_room * abs(room1 - room2) + w_hall * abs(hall1 - hall2) + w_bathroom * abs(
            bathroom1 - bathroom2) + w_kitchen * abs(kitchen1 - kitchen2)

    def house_decorating_distinction(self, decoration1, decoration2):
        if (decoration1 == "毛坯" and decoration2 == "毛坯") or (decoration1 == "简装" and decoration2 == "简装") or (
                decoration1 == "精装" and decoration2 == "精装"):
            return 0
        elif (decoration1 == "毛坯" and decoration2 == "简装") or (decoration1 == "简装" and decoration2 == "毛坯") or (
                decoration1 == "简装" and decoration2 == "精装") or (decoration1 == "精装" and decoration2 == "简装"):
            return 1
        elif (decoration1 == "毛坯" and decoration2 == "精装") or (decoration1 == "精装" and decoration2 == "毛坯"):
            return 2
        return 3

    def house_year_distinction(self, year1, year2):
        return abs(int(year1) - int(year2))

    def transaction_time_distinction(self, date1, date2):
        date1 = datetime.strptime(date1, "%Y-%m-%d")
        date2 = datetime.strptime(date2, "%Y-%m-%d")
        return abs(date1 - date2).days

    def selction(self) -> list:
        # 加入粗筛
        two_years_ago = (datetime.now() - timedelta(days=2 * 365)).strftime('%Y-%m-%d')

        query = (
            "SELECT *"
            f" FROM {self.table}"
            f" WHERE house_loc LIKE '仁恒森兰雅苑%'"  # 同一小区
            f" AND ABS(CAST(house_year AS SIGNED) - {self.house_year}) <= 5"  # 建成年份相差5年内
            f" AND house_structure = '{self.house_structure}'"  # 产品形态一致
            f" AND STR_TO_DATE(transaction_time, '%Y-%m-%d') >= STR_TO_DATE('{two_years_ago}', '%Y-%m-%d')"  # 近2年的交易记录
        )
        # TODO:粗筛有点问题
        print(query)

        df = pd.read_sql(query, self.engine)
        # print("粗筛：")
        # print(df)
        features = ['house_floor', 'house_area', 'house_type', 'house_decoration', 'house_year',
                    'transaction_time']
        df = df[~df[features].apply(lambda row: row.astype(str).str.contains('暂无数据')).any(axis=1)]
        df['house_year'] = df['house_year'].replace('未知', np.nan)
        mean_value = int(df['house_year'].dropna().astype(int).mean())
        df['house_year'] = df['house_year'].replace(np.nan, mean_value)
        df['house_year'] = df['house_year'].astype(int)
        # df = df.dropna()
        df['house_floor_distinction'] = df['house_floor'].apply(
            lambda x: self.house_floor_distinction(x, self.house_floor))
        df['house_area_distinction'] = df['house_area'].apply(
            lambda x: self.house_area_distinction(x, float(self.house_area)))
        df['house_type_distinction'] = df['house_type'].apply(
            lambda x: self.house_type_distinction(x, self.house_type))
        df['house_decorating_distinction'] = df['house_decoration'].apply(
            lambda x: self.house_decorating_distinction(x, self.house_decoration))
        df['house_year_distinction'] = df['house_year'].apply(
            lambda x: self.house_year_distinction(x, int(self.house_year)))
        df['transaction_time_distinction'] = df['transaction_time'].apply(
            lambda x: self.transaction_time_distinction(x, self.today))

        scaler = MinMaxScaler()

        columns_to_scale = ['house_floor_distinction', 'house_area_distinction', 'house_type_distinction',
                            'house_decorating_distinction', 'house_year_distinction',
                            'transaction_time_distinction']
        scaled_data = scaler.fit_transform(df[columns_to_scale])
        df[columns_to_scale] = scaled_data
        df['distinction'] = df['house_floor_distinction'] + df['house_area_distinction'] + df[
            'house_type_distinction'] + \
                            df['house_decorating_distinction'] + df['house_year_distinction'] + df[
                                'transaction_time_distinction']
        df = df.sort_values(by='distinction')

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', 1000)
        # print(df)
        # df[:3].to_csv('1.csv', index=False, encoding='utf_8_sig')
        # print(df[:3])
        return df[:3].to_dict(orient='records')
        # df[:4].to_csv(f'{table}.csv', index=False,encoding='utf_8_sig')

# username = 'root'
# password = '123456'
# host = '127.0.0.1'
# port = '3306'
# database = 'sitp'
# uri = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
# engine = create_engine(uri)
#
# table='test3'
# id=1
#
# w_floor=1
# w_area=1
# w_type=1
# w_decoration=1
# w_year=1
# w_transaction=1
#
# if __name__ == '__main__':
#     selction_example = careful_selection(username='root',
#                                          password='122111',
#                                          host='127.0.0.1',
#                                          port='3306',
#                                          database='test',
#                                          table='test3',
#                                          id=1)
#     df = selction_example.selction()
#     print(df)

# query = (#"SELECT id,house_floor,house_area,house_type,house_decorating,house_year,last_transaction_time,green_rate"
#          "SELECT *"
#          f" FROM {table}"
#          f" WHERE house_loc = (SELECT house_loc FROM {table} WHERE id = {id}) AND house_structure = (SELECT house_structure FROM {table} WHERE id = {id});")
# df = pd.read_sql(query, engine)
# features = ['house_floor', 'house_area','house_type','house_decorating','house_year','last_transaction_time']
# df = df[~df[features].apply(lambda row: row.astype(str).str.contains('暂无数据')).any(axis=1)]
# #df = df.dropna()
# df['house_floor_distinction'] = df['house_floor'].apply(
#     lambda x: house_floor_distinction(x, df.loc[df['id'] == id, 'house_floor'].values[0]))
# df['house_area_distinction'] = df['house_area'].apply(
#     lambda x: house_area_distinction(x, df.loc[df['id'] == id, 'house_area'].values[0]))
# df['house_type_distinction'] = df['house_type'].apply(
#     lambda x: house_type_distinction(x, df.loc[df['id'] == id, 'house_type'].values[0]))
# df['house_decorating_distinction'] = df['house_decorating'].apply(
#     lambda x: house_decorating_distinction(x, df.loc[df['id'] == id, 'house_decorating'].values[0]))
# df['house_year_distinction'] = df['house_year'].apply(
#     lambda x: house_year_distinction(x, df.loc[df['id'] == id, 'house_year'].values[0]))
# df['last_transaction_time_distinction'] = df['last_transaction_time'].apply(
#     lambda x: last_transaction_time_distinction(x, df.loc[df['id'] == id, 'last_transaction_time'].values[0]))
#
# scaler = MinMaxScaler()
#
# columns_to_scale = ['house_floor_distinction', 'house_area_distinction', 'house_type_distinction',
#                     'house_decorating_distinction', 'house_year_distinction', 'last_transaction_time_distinction']
# scaled_data = scaler.fit_transform(df[columns_to_scale])
# df[columns_to_scale] = scaled_data
# df['distinction'] = df['house_floor_distinction'] + df['house_area_distinction'] + df['house_type_distinction'] + \
#                     df['house_decorating_distinction'] + df['house_year_distinction'] + df[
#                         'last_transaction_time_distinction']
# df = df.sort_values(by='distinction')
#
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.width', 1000)
# print(df)
# df[:4].to_csv(f'{table}.csv', index=False,encoding='utf_8_sig')
