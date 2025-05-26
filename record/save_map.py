import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from datetime import datetime
from config.path_config import MAP_PATH
from llm.llm_manager import QianwenManager
import json


def get_origin_place(place_name, city, status):  #定位函数
    url = f"https://api.map.baidu.com/place/v2/search?query={place_name}&region={city}&output=json&ak=EbkD3DWCB5Ev9HfZkMwTJymCxxgc28nr"
    response = requests.get(url)
    result = response.json()

    if result.get('status') == 0 and result.get('results'):
        location = result['results'][0]['location']
        if status == 0:
            return f'{location["lng"]},{location["lat"]}'
        elif status == 1:
            return f'{location["lat"]},{location["lng"]}', [r['name'] for r in result['results']]
        else:
            return None
    else:
        return None


def get_nearby_places(location, search_place_name, radius=2000):  #搜索函数
    url = f"https://api.map.baidu.com/place/v2/search?location={location}&radius={radius}&query={search_place_name}&output=json&ak=EbkD3DWCB5Ev9HfZkMwTJymCxxgc28nr"
    response = requests.get(url)
    result = response.json()

    if result.get('status') == 0 and result.get('results'):
        return [r['name'] for r in result['results']]
    else:
        return None


def map_location(location):
    url = f"https://api.map.baidu.com/staticimage/v2?ak=EbkD3DWCB5Ev9HfZkMwTJymCxxgc28nr&width=512&height=400&zoom=16&scale=2&center={location}&markers={location}"
    # print(url)
    # 发送HTTP GET请求获取图片
    response = requests.get(url)
    # 检查请求是否成功
    if response.status_code == 200:
        # 将响应内容转换为二进制流
        image_data = BytesIO(response.content)
        # 打开二进制流中的图片
        image = Image.open(image_data)
        # 保存图片到本地
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        # 使用pathlib处理路径
        image_path = Path(MAP_PATH) / filename
        image.save(image_path)
        print(f"位置图下载成功")
        return image_path
    else:
        print(f"位置图下载失败，状态码: {response.status_code}")
        return None


def map_main(place_name, city):
    location = get_origin_place(place_name, city, 0)
    # print(location)
    return map_location(location)


def nearby_list(loc, city):
    location, origin_places = get_origin_place(loc, city, 1)
    if location:
        nearby_places = get_nearby_places(location, "住宅区")
        # nearby_places.append(loc)
        nearby_list = QianwenManager().get_near_loc(str(nearby_places))
        try:
            list = json.loads(json.dumps(eval(nearby_list)))
            return list
        except:
            print(f"预期为二维列表，实际为{nearby_list}")
            return None
    else:
        print("百度地图api出错")
        return None


def environment_main(place_name, city):
    search_place_name = '住宅区'
    search_hospital = '医院'
    search_school = '学校'
    search_transportation = '交通设施'
    location, origin_places = get_origin_place(place_name, city, 1)
    if location:
        nearby_places = get_nearby_places(location, search_place_name)
        hospital = get_nearby_places(location, search_hospital)
        school = get_nearby_places(location, search_school)
        transportation = get_nearby_places(location, search_transportation)
        result = QianwenManager().get_environment(nearby_places, hospital, school)
        print(result)
        return result
    else:
        print('未定位到小区')
        return ""


if __name__ == '__main__':
    # print(nearby_list("世茂滨江花园", "上海"))
    environment_main("世茂滨江花园", "上海")
