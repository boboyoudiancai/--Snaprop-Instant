"""
本模块包含多模态编码器类，用于处理房产估值的多模态信息
"""
import os
import re
import json
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime
from config.path_config import MAP_PATH

class VisualEncoder:
    """
    视觉编码器类，用于处理房产证OCR识别和房屋外观特征提取
    """
    def __init__(self):
        """初始化视觉编码器"""
        pass
    
    def process_property_cert(self, image_path):
        """
        处理房产证图片，提取关键信息
        
        Args:
            image_path: 房产证图片路径
            
        Returns:
            dict: 提取的结构化信息
        """
        # 实际项目中应使用OCR API，这里简化处理
        try:
            # 打开并预处理图像
            image = Image.open(image_path)
            # 模拟OCR处理结果
            ocr_result = {
                "house_location": "提取的房屋地址",
                "house_area": 0.0,
                "house_type": "",
                "house_year": 0,
                "house_structure": "",
            }
            return ocr_result
        except Exception as e:
            print(f"处理房产证图片出错: {str(e)}")
            return {}
    
    def extract_property_features(self, image_path):
        """
        提取房屋外观特征
        
        Args:
            image_path: 房屋外观图片路径
            
        Returns:
            dict: 提取的特征
        """
        try:
            # 打开并预处理图像
            image = Image.open(image_path)
            # 模拟特征提取
            features = {
                "building_style": "现代",
                "condition": "良好",
                "environment": "整洁",
                "visual_features": np.random.rand(512).tolist()  # 模拟视觉特征向量
            }
            return features
        except Exception as e:
            print(f"提取房屋外观特征出错: {str(e)}")
            return {}
    
    def align_visual_semantic(self, visual_features, text_features):
        """
        视觉-语义对齐机制
        
        Args:
            visual_features: 视觉特征
            text_features: 文本特征
            
        Returns:
            dict: 对齐后的特征
        """
        # 实际项目中应实现复杂的对齐算法，这里简化处理
        aligned_features = {
            "combined_features": np.mean([
                np.array(visual_features.get("visual_features", [])), 
                np.array(text_features.get("text_vector", []))
            ], axis=0).tolist() if visual_features.get("visual_features") and text_features.get("text_vector") else []
        }
        return aligned_features


class TextEncoder:
    """
    文本编码器类，用于处理房产描述文本
    """
    def __init__(self):
        """初始化文本编码器"""
        pass
    
    def extract_structured_info(self, text):
        """
        提取结构化信息
        
        Args:
            text: 输入文本
            
        Returns:
            dict: 提取的结构化信息
        """
        # 使用正则表达式提取关键信息
        info = {}
        
        # 提取房屋面积
        area_match = re.search(r'(\d+(\.\d+)?)\s*平(方米)?', text)
        if area_match:
            info['house_area'] = float(area_match.group(1))
        
        # 提取房型
        room_match = re.search(r'(\d+)\s*室\s*(\d+)\s*厅', text)
        if room_match:
            info['house_type'] = f"{room_match.group(1)}室{room_match.group(2)}厅"
        
        # 提取建成年份
        year_match = re.search(r'(\d{4})\s*年(建成|建造|竣工)', text)
        if year_match:
            info['house_year'] = int(year_match.group(1))
        
        # 提取装修情况
        if '精装' in text:
            info['house_decorating'] = '精装'
        elif '简装' in text:
            info['house_decorating'] = '简装'
        elif '毛坯' in text:
            info['house_decorating'] = '毛坯'
        
        # 提取楼层信息
        floor_match = re.search(r'(低|中|高)\s*楼层', text)
        if floor_match:
            info['house_floor'] = f"{floor_match.group(1)}楼层"
        
        return info
    
    def encode_semantic_features(self, text):
        """
        编码语义特征
        
        Args:
            text: 输入文本
            
        Returns:
            dict: 语义特征
        """
        # 实际项目中应使用词嵌入或语言模型，这里简化处理
        text_vector = np.random.rand(512).tolist()  # 模拟文本向量
        return {"text": text, "text_vector": text_vector}


class SpatialEncoder:
    """
    空间编码器类，用于处理地理位置信息
    """
    def __init__(self):
        """初始化空间编码器"""
        self.api_key = "EbkD3DWCB5Ev9HfZkMwTJymCxxgc28nr"  # 百度地图API密钥
    
    def geocode(self, address, city):
        """
        地理编码，将地址转换为经纬度
        
        Args:
            address: 地址
            city: 城市
            
        Returns:
            tuple: (经度, 纬度)
        """
        url = f"https://api.map.baidu.com/geocoding/v3/?address={address}&city={city}&output=json&ak={self.api_key}"
        try:
            response = requests.get(url)
            result = response.json()
            if result.get('status') == 0:
                location = result['result']['location']
                return location['lng'], location['lat']
            else:
                print(f"地理编码失败: {result.get('message')}")
                return None, None
        except Exception as e:
            print(f"地理编码请求出错: {str(e)}")
            return None, None
    
    def reverse_geocode(self, lng, lat):
        """
        反向地理编码，将经纬度转换为地址
        
        Args:
            lng: 经度
            lat: 纬度
            
        Returns:
            dict: 地址信息
        """
        url = f"https://api.map.baidu.com/reverse_geocoding/v3/?location={lat},{lng}&output=json&ak={self.api_key}"
        try:
            response = requests.get(url)
            result = response.json()
            if result.get('status') == 0:
                return result['result']
            else:
                print(f"反向地理编码失败: {result.get('message')}")
                return {}
        except Exception as e:
            print(f"反向地理编码请求出错: {str(e)}")
            return {}
    
    def get_poi_info(self, lng, lat, radius=2000):
        """
        获取POI信息
        
        Args:
            lng: 经度
            lat: 纬度
            radius: 搜索半径（米）
            
        Returns:
            dict: POI信息
        """
        poi_types = {
            "education": ["学校", "幼儿园", "培训机构"],
            "medical": ["医院", "诊所", "药店"],
            "shopping": ["商场", "超市", "便利店"],
            "transportation": ["地铁站", "公交站", "火车站"],
            "leisure": ["公园", "健身房", "电影院"]
        }
        
        poi_results = {}
        
        for category, keywords in poi_types.items():
            poi_results[category] = []
            for keyword in keywords:
                url = f"https://api.map.baidu.com/place/v2/search?query={keyword}&location={lat},{lng}&radius={radius}&output=json&ak={self.api_key}"
                try:
                    response = requests.get(url)
                    result = response.json()
                    if result.get('status') == 0:
                        poi_results[category].extend([
                            {
                                "name": poi["name"],
                                "distance": poi["detail_info"]["distance"] if "detail_info" in poi else None,
                                "address": poi["address"]
                            }
                            for poi in result["results"][:5]  # 每类最多取5个
                        ])
                except Exception as e:
                    print(f"获取POI信息出错: {str(e)}")
        
        return poi_results
    
    def calculate_poi_scores(self, poi_info):
        """
        计算POI评分
        
        Args:
            poi_info: POI信息
            
        Returns:
            dict: POI评分
        """
        # 设置各类设施的权重
        weights = {
            "education": 0.25,
            "medical": 0.2,
            "shopping": 0.15,
            "transportation": 0.3,
            "leisure": 0.1
        }
        
        scores = {}
        
        for category, pois in poi_info.items():
            if not pois:
                scores[category] = 0
                continue
                
            # 计算距离评分，距离越近分数越高
            distances = [poi["distance"] for poi in pois if poi["distance"] is not None]
            if not distances:
                scores[category] = 0
                continue
                
            # 距离评分转换：1000米内满分，5000米外零分，线性递减
            distance_scores = [max(0, 1 - (d - 1000) / 4000) if d > 1000 else 1 for d in distances]
            
            # 计算加权平均分
            scores[category] = sum(distance_scores) / len(distance_scores) * weights[category]
        
        # 总分
        total_score = sum(scores.values()) / sum(weights.values())
        
        return {"category_scores": scores, "total_score": total_score}
    
    def generate_map_image(self, lng, lat):
        """
        生成地图图片
        
        Args:
            lng: 经度
            lat: 纬度
            
        Returns:
            str: 图片路径
        """
        url = f"https://api.map.baidu.com/staticimage/v2?ak={self.api_key}&width=512&height=400&zoom=16&center={lng},{lat}&markers={lng},{lat}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # 将响应内容转换为二进制流
                image_data = BytesIO(response.content)
                # 打开二进制流中的图片
                image = Image.open(image_data)
                # 保存图片到本地
                filename = f"map_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                # 使用pathlib处理路径
                image_path = os.path.join(MAP_PATH, filename)
                image.save(image_path)
                print(f"地图图片生成成功: {image_path}")
                return image_path
            else:
                print(f"地图图片生成失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"地图图片生成出错: {str(e)}")
            return None


class MultimodalEncoder:
    """
    多模态编码器，整合视觉、文本和空间编码器
    """
    def __init__(self):
        """初始化多模态编码器"""
        self.visual_encoder = VisualEncoder()
        self.text_encoder = TextEncoder()
        self.spatial_encoder = SpatialEncoder()
    
    def process_property_data(self, property_cert_image=None, property_photo=None, property_text=None, address=None, city=None):
        """
        处理房产数据
        
        Args:
            property_cert_image: 房产证图片路径
            property_photo: 房屋外观图片路径
            property_text: 房产描述文本
            address: 房产地址
            city: 所在城市
            
        Returns:
            dict: 处理结果
        """
        result = {}
        
        # 处理房产证图片
        if property_cert_image:
            cert_info = self.visual_encoder.process_property_cert(property_cert_image)
            result["cert_info"] = cert_info
        
        # 处理房屋外观图片
        if property_photo:
            visual_features = self.visual_encoder.extract_property_features(property_photo)
            result["visual_features"] = visual_features
        
        # 处理文本描述
        if property_text:
            structured_info = self.text_encoder.extract_structured_info(property_text)
            semantic_features = self.text_encoder.encode_semantic_features(property_text)
            result["structured_info"] = structured_info
            result["semantic_features"] = semantic_features
        
        # 处理地理位置
        if address and city:
            lng, lat = self.spatial_encoder.geocode(address, city)
            if lng and lat:
                result["location"] = {"lng": lng, "lat": lat}
                
                # 获取POI信息
                poi_info = self.spatial_encoder.get_poi_info(lng, lat)
                result["poi_info"] = poi_info
                
                # 计算POI评分
                poi_scores = self.spatial_encoder.calculate_poi_scores(poi_info)
                result["poi_scores"] = poi_scores
                
                # 生成地图图片
                map_image = self.spatial_encoder.generate_map_image(lng, lat)
                if map_image:
                    result["map_image"] = map_image
        
        # 视觉-语义对齐
        if "visual_features" in result and "semantic_features" in result:
            aligned_features = self.visual_encoder.align_visual_semantic(
                result["visual_features"], 
                result["semantic_features"]
            )
            result["aligned_features"] = aligned_features
        
        return result 