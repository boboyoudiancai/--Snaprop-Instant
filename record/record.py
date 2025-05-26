"""
本模块包含 用户记录 类
"""

from record.save_map import map_main
from pathlib import Path


class Record:
    """
    用户记录类
    """
    expected_keys = [
        'house_location', 'city', 'house_area', 'house_type','house_year',
        'house_structure', 'house_floor', 'house_decorating', 'green_rate'
    ]

    def __init__(self, uid: int):
        self.uid = uid
        self.house_location: str = ""
        self.city: str = ""
        self.house_area: float = 0.0
        self.house_type: str = ""  # 房型，格式为*室*厅*厨*卫，其中*表示数字
        self.house_year: int = 0  # 房屋建成年份
        self.house_structure = ""  # 房屋结构，有平层/复式
        self.house_floor: str = ""  # 房屋楼层，有低楼层/中楼层/高楼层可选
        self.house_decorating: str = ""  # 房屋装修情况，有精装/简装/毛坯可选
        self.green_rate: float = 0.0  # 小区绿化率
        self.price: float = 0.0  # 房屋单价
        self.map: str = ""  # 位置图
        self.production_cert_img: list[str] = []  # 产证图片，可能多张
        self.production_ocr: str = ""  # OCR识别表格
        self.field_img: list[str] = []  # 实地图片，可能多张

    def clear(self):
        self.house_location = ""
        self.city = ""
        self.house_area = 0.0
        self.house_type = ""
        self.house_year = 0
        self.house_structure = ""
        self.house_floor = ""
        self.house_decorating = ""
        self.green_rate = 0.0
        #把文件删了
        self._clean_file(self.map)  # 清理地图文件
        self._clean_files(self.production_cert_img)  # 清理产权证明图片
        self._clean_file(self.production_ocr)  # 清理OCR文件
        self._clean_files(self.field_img)  # 清理实地照片
        self.map = ""
        self.production_cert_img.clear()
        self.production_ocr = ""
        self.field_img.clear()
    
    def _clean_file(self, file_path: str):
        """安全删除单个文件"""
        try:
            if file_path:
                path = Path(file_path).resolve()  # 转换为绝对路径
                if path.exists() and path.is_file():
                    path.unlink()  # 删除文件
                    print(f"已删除文件: {path}")
        except Exception as e:
            print(f"删除文件失败 {file_path}: {str(e)}")

    def _clean_files(self, file_list: list):
        """批量删除文件"""
        for file_path in file_list:
            self._clean_file(file_path)

    def get_record(self):
        result = ""
        for key in self.expected_keys:
            try:
                if key == 'house_location' and self.house_location != "":
                    result += f"-小区名称：{self.house_location}\n"
                elif key == 'city' and self.city != "":
                    result += f"-所在城市：{self.city}\n"
                elif key == 'house_area' and self.house_area != 0.0:
                    result += f"-房屋面积：{self.house_area}平方米\n"
                elif key == 'house_type' and self.house_type != "":
                    result += f"-房型：{self.house_type}\n"
                elif key == 'house_structure' and self.house_structure != "":
                    result += f"-房屋结构：{self.house_structure}\n"
                elif key == 'house_year' and self.house_year != 0:
                    result += f"-建成年份：{self.house_year}年\n"
                elif key == 'house_floor' and self.house_floor != "":
                    result += f"-楼层：{self.house_floor}\n"
                elif key == 'house_decorating' and self.house_decorating != "":
                    result += f"-装修情况：{self.house_decorating}\n"
                elif key == 'green_rate' and self.green_rate != 0.0:
                    result += f"-小区绿化率：{self.green_rate * 100}%\n"
                else:
                    print("未期待的参数")
            except (ValueError, TypeError) as e:
                print(f"数据转换错误: {key}= {str(e)}")
                result += f"数据转换错误: {key}= {str(e)}"
        # if self.production_cert_img:
        #     result += f"-产证图片：{self.production_cert_img}\n"
        # if self.production_ocr:
        #     result += f"-OCR结果：{self.production_ocr}\n"
        # if self.field_img:
        #     result += f"-实地图片：{self.field_img}\n"
        return result

    def get_map(self):
        img_path = map_main(self.house_location, self.city)
        if img_path:
            self.map = img_path

    def add_property(self, img_url: str):
        self.production_cert_img.append(img_url)

    def add_property_ocr(self, file_path: str):
        self.production_ocr = file_path

    def add_field(self, img_url: str):
        self.field_img.append(img_url)

    def get_null(self):
        missing_value = []
        if self.house_location == "":
            missing_value.append("house_location")
        if self.city == "":
            missing_value.append("city")
        if self.house_area == 0.0:
            missing_value.append("house_area")
        if self.house_type == "":
            missing_value.append("house_type")
        if self.house_structure == "":
            missing_value.append("house_structure")
        if self.house_year == 0:
            # TODO：内存库中先搜素该小区，若无该小区案例，询问用户
            missing_value.append("house_year")
        if self.house_floor == "":
            missing_value.append("house_floor")
        if self.house_decorating == "":
            missing_value.append("house_decorating")
        if self.green_rate == 0.0:
            # TODO：内存库中先搜素该小区，若无该小区案例，询问用户
            missing_value.append("green_rate")
        return missing_value

    def add_green_rate(self, green_rate: float):  # 数据库搜索
        self.green_rate = green_rate

    def add_price(self, price: float):  # 市场比较法估算
        self.price = price

    def add_data(self, data: list):  # 根据llm返回的Python二维列表补充数据
        input = ""
        error = False
        for item in data:
            if len(item) != 2:
                continue
            key, value = item[0], item[1]
            if key in self.expected_keys:
                # 类型转换处理
                try:
                    if key == 'house_location':
                        self.house_location = value
                        input += f"-小区名称：{self.house_location}\n"
                    elif key == 'city':
                        self.city = value
                        input += f"-所在城市：{self.city}\n"
                    elif key == 'house_area':
                        self.house_area = float(value)
                        input += f"-房屋面积：{self.house_area}平方米\n"
                    elif key == 'house_type':
                        self.house_type = value
                        input += f"-房型：{self.house_type}\n"
                    elif key == 'house_structure':
                        self.house_structure = value
                        input += f"-房屋结构：{self.house_structure}\n"
                    elif key == 'house_year':
                        self.house_year = int(value)
                        input += f"-建成年份：{self.house_year}年\n"
                    elif key == 'house_floor':
                        self.house_floor = value
                        input += f"-楼层：{self.house_floor}\n"
                    elif key == 'house_decorating':
                        self.house_decorating = value
                        input += f"-装修情况：{self.house_decorating}\n"
                    elif key == 'green_rate':
                        self.green_rate = float(value)
                        input += f"-小区绿化率：{self.green_rate * 100}%\n"
                    else:
                        setattr(self, key, value)
                except (ValueError, TypeError) as e:
                    error = True
                    print(f"数据转换错误: {key}={value} - {str(e)}")
                    input += f"数据转换错误: {key}={value} - {str(e)}"
        return error, input
