"""
本模块包含LLM增强信息获取模块，用于处理和增强房产数据
"""
import json
import numpy as np
from llm.llm_manager import QianwenManager

class LLMEnhancer:
    """
    LLM增强信息获取模块，使用大语言模型增强房产数据
    """
    def __init__(self):
        """初始化LLM增强器"""
        self.llm_manager = QianwenManager()
    
    def preprocess_data(self, visual_data, text_data, geo_data, poi_data):
        """
        预处理数据，将多模态数据标准化为LLM可处理的格式
        
        Args:
            visual_data: 视觉数据
            text_data: 文本数据
            geo_data: 地理数据
            poi_data: POI数据
            
        Returns:
            dict: 预处理后的数据
        """
        # 标准化视觉特征
        v_vis_norm = {}
        if visual_data:
            for key, value in visual_data.items():
                if isinstance(value, list) and len(value) > 10:  # 处理特征向量
                    # 简化向量表示
                    v_vis_norm[key] = f"[向量，维度:{len(value)}]"
                else:
                    v_vis_norm[key] = value
        
        # 标准化文本特征
        v_text_norm = {}
        if text_data:
            for key, value in text_data.items():
                if isinstance(value, list) and len(value) > 10:  # 处理特征向量
                    # 简化向量表示
                    v_text_norm[key] = f"[向量，维度:{len(value)}]"
                else:
                    v_text_norm[key] = value
        
        # 标准化地理位置
        l_geo_std = {}
        if geo_data:
            l_geo_std = {
                "lng": geo_data.get("lng", ""),
                "lat": geo_data.get("lat", ""),
                "address": geo_data.get("address", ""),
                "city": geo_data.get("city", "")
            }
        
        # 结构化POI数据
        s_poi_struct = {}
        if poi_data:
            for category, pois in poi_data.items():
                s_poi_struct[category] = []
                for poi in pois:
                    s_poi_struct[category].append({
                        "name": poi.get("name", ""),
                        "distance": poi.get("distance", "")
                    })
        
        return {
            "v_vis_norm": v_vis_norm,
            "v_text_norm": v_text_norm,
            "l_geo_std": l_geo_std,
            "s_poi_struct": s_poi_struct
        }
    
    def enhance_with_llm(self, preprocessed_data):
        """
        使用LLM增强数据
        
        Args:
            preprocessed_data: 预处理后的数据
            
        Returns:
            dict: 增强后的数据
        """
        # 构建提示词
        prompt = self._build_chain_of_thought_prompt(preprocessed_data)
        
        # 调用LLM
        llm_response = self.llm_manager.interact_qwen(
            prompt=prompt,
            request=""  # 空请求，因为所有信息都在prompt中
        )
        
        # 解析LLM响应
        try:
            # 尝试提取JSON部分
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                enhanced_data = json.loads(json_str)
                return enhanced_data
            else:
                print("LLM响应中未找到JSON数据")
                return {"error": "无法解析LLM响应", "raw_response": llm_response}
        except Exception as e:
            print(f"解析LLM响应出错: {str(e)}")
            return {"error": str(e), "raw_response": llm_response}
    
    def _build_chain_of_thought_prompt(self, data):
        """
        构建Chain-of-Thought提示词
        
        Args:
            data: 预处理后的数据
            
        Returns:
            str: 提示词
        """
        context = "你是一个专业的房产估价师，需要分析以下房产数据并增强信息。"
        
        input_data = f"""
[输入数据]
视觉特征: {json.dumps(data['v_vis_norm'], ensure_ascii=False, indent=2)}
文本特征: {json.dumps(data['v_text_norm'], ensure_ascii=False, indent=2)}
地理位置: {json.dumps(data['l_geo_std'], ensure_ascii=False, indent=2)}
设施评分: {json.dumps(data['s_poi_struct'], ensure_ascii=False, indent=2)}
"""
        
        task = """
请基于以上数据，执行以下信息增强任务：
1. 补全缺失的房产关键参数
2. 验证信息一致性并解决冲突
3. 分析影响房产价值的核心因素
4. 关联当前市场趋势数据
"""
        
        reasoning = """
请逐步思考：
步骤1: 分析现有数据的完整性，识别信息缺口
步骤2: 基于已知信息推断缺失参数
步骤3: 交叉验证各数据源信息一致性
步骤4: 提取价值影响因素并量化其影响
"""
        
        output_format = """
请以JSON格式输出增强后的信息，包含以下部分：
{
  "property_info": {
    "location": "房产位置",
    "area": 面积数值,
    "type": "房型",
    "year": 建成年份,
    "floor": "楼层",
    "decoration": "装修情况",
    "structure": "结构类型"
  },
  "consistency_check": {
    "conflicts": ["冲突1", "冲突2"],
    "resolutions": ["解决方案1", "解决方案2"]
  },
  "value_factors": [
    {"factor": "因素1", "impact": "影响描述", "weight": 权重},
    {"factor": "因素2", "impact": "影响描述", "weight": 权重}
  ],
  "market_trends": {
    "current_price_level": "当前价格水平",
    "price_trend": "价格趋势",
    "liquidity": "市场流动性",
    "policy_impact": "政策影响"
  },
  "estimated_price_range": {
    "low": 最低估价,
    "high": 最高估价,
    "confidence": 置信度
  }
}
"""
        
        return f"{context}\n{input_data}\n{task}\n{reasoning}\n{output_format}"
    
    def process_and_enhance(self, multimodal_data):
        """
        处理并增强多模态数据
        
        Args:
            multimodal_data: 多模态数据
            
        Returns:
            dict: 增强后的数据
        """
        # 提取各类数据
        visual_data = {**multimodal_data.get("visual_features", {}), **multimodal_data.get("cert_info", {})}
        text_data = {**multimodal_data.get("structured_info", {}), **multimodal_data.get("semantic_features", {})}
        geo_data = multimodal_data.get("location", {})
        poi_data = multimodal_data.get("poi_info", {})
        
        # 预处理数据
        preprocessed_data = self.preprocess_data(visual_data, text_data, geo_data, poi_data)
        
        # 使用LLM增强数据
        enhanced_data = self.enhance_with_llm(preprocessed_data)
        
        # 合并原始数据和增强数据
        result = {
            "original_data": multimodal_data,
            "enhanced_data": enhanced_data
        }
        
        return result 