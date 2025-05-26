"""
本模块包含 MySQL管理 类
"""
import mysql.connector
import pandas as pd
import datetime
from config.mysql_config import mysql_host, mysql_db, mysql_port, mysql_username, mysql_password


class MySQLManager():
    """
    MySQL数据库管理 类
    """
    city_tables = {"上海": "shanghai",
                   "北京": "beijing"
                   }

    def __init__(self):
        self._host = mysql_host
        self._port = mysql_port
        self._username = mysql_username
        self._password = mysql_password
        self._db = mysql_db
        self._connection = mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._username,
            password=self._password,
            database=self._db
        )
        self._cursor = self._connection.cursor()

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()

    def get_cursor(self):
        self._connection = mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._username,
            password=self._password,
            database=self._db
        )
        self._cursor = self._connection.cursor()
        return self._cursor

    def get_table(self, city):
        table_name = self.city_tables[city]
        return table_name

    def insert(self, city, filepath):
        table_name = self.get_table(city)
        df = pd.read_excel(filepath)
        insert_query = f"""
        INSERT INTO {table_name} (house_type,house_floor,house_direction,house_area,house_structure,transaction_type,transaction_time,house_decoration,is_elevator,house_year,green_rate,house_loc,house_position,u_price,t_price,detail_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s)
        """
        df['transaction_time'] = pd.to_datetime(df['transaction_time']).dt.strftime('%Y-%m-%d')
        for _, row in df.iterrows():
            try:
                house_year = row['house_year']
                if pd.isna(house_year) or str(house_year).strip() in ['未知', '']:
                    house_year = None

                self._cursor.execute(insert_query, (
                    row['house_type'], row['house_floor'], row['house_direction'], row['house_area'],
                    row['house_structure'], row['transaction_type'], row['transaction_time'], row['house_decoration'],
                    row['is_elevator'], house_year, row['green_rate'], row['house_loc'], row['house_position'],
                    row['u_price'], row['t_price'], row['detail_url']))
                self._connection.commit()  # 提交事务
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                self._connection.rollback()  # 回滚事务
        print("数据插入完成！")

    def get_city_info(self, city):
        try:
            introduction_query="SELECT city_introduction FROM city WHERE city_name=%s"
            self._cursor.execute(introduction_query, (city,))
            introduction = self._cursor.fetchone()
            detail_query="SELECT detail FROM city WHERE city_name=%s"
            self._cursor.execute(detail_query, (city,))
            detail = self._cursor.fetchone()
            return introduction[0], detail[0]
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    @property
    def host(self):
        return self._host


if __name__ == '__main__':
    mysql_manager = MySQLManager()

    # print(mysql_manager.get_table("上海"))

    filepath = "D:/sitp_work/data/森兰明轩.xlsx"
    mysql_manager.insert("上海", filepath)

    # mysql_manager.get_city_info("上海")
