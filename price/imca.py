"""
本模块包含智能化市场比较法（IMCA）实现，用于房产估值
"""
import numpy as np
import pandas as pd
from datetime import datetime
import os
import sys

# 添加项目根目录到路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rules.differentiable_rule import DifferentiableRuleLearningFramework
except ImportError:
    # 如果规则模块不存在，使用空的框架
    DifferentiableRuleLearningFramework = None

class IMCA:
    """
    智能化市场比较法（Intelligent Market Comparison Approach）
    """
    def __init__(self, rule_framework=None):
        """
        初始化IMCA
        
        Args:
            rule_framework: 可微分规则学习框架
        """
        self.rule_framework = rule_framework
        
        # 默认特征权重
        self.default_weights = {
            'location': 0.25,       # 位置权重
            'time': 0.15,           # 时间权重
            'physical': 0.20,       # 物理特性权重
            'legal': 0.10,          # 法律特性权重
            'environment': 0.15,    # 环境特性权重
            'transaction': 0.15     # 交易特性权重
        }
        
        # 默认特征相似度计算参数
        self.similarity_params = {
            'time_decay_rate': 0.1,  # 时间衰减率（每年）
            'distance_decay_rate': 0.2,  # 距离衰减率（每公里）
            'area_tolerance': 10,    # 面积容忍度（平方米）
            'floor_importance': 0.5, # 楼层重要性
            'decoration_importance': 0.7, # 装修重要性
            'age_importance': 0.6    # 房龄重要性
        }
    
    def preprocess_data(self, target_property, comparable_cases):
        """
        预处理数据
        
        Args:
            target_property: 目标房产数据
            comparable_cases: 可比案例数据
            
        Returns:
            tuple: (处理后的目标房产, 处理后的可比案例)
        """
        # 深拷贝，避免修改原始数据
        target = target_property.copy()
        cases = [case.copy() for case in comparable_cases]
        
        # 计算房龄
        current_year = datetime.now().year
        
        if 'built_year' in target:
            target['age'] = current_year - target['built_year']
        elif 'built_time' in target:
            try:
                built_year = datetime.strptime(target['built_time'], '%Y-%m-%d').year
                target['age'] = current_year - built_year
            except:
                target['age'] = 0
        
        for case in cases:
            if 'built_year' in case:
                case['age'] = current_year - case['built_year']
            elif 'built_time' in case:
                try:
                    built_year = datetime.strptime(case['built_time'], '%Y-%m-%d').year
                    case['age'] = current_year - built_year
                except:
                    case['age'] = 0
            
            # 计算交易时间与当前时间的差（年）
            if 'transaction_time' in case:
                try:
                    transaction_date = datetime.strptime(case['transaction_time'], '%Y-%m-%d')
                    case['time_diff'] = (datetime.now() - transaction_date).days / 365.0
                except:
                    case['time_diff'] = 0
        
        return target, cases
    
    def calculate_similarity(self, target, case):
        """
        计算目标房产与可比案例的相似度
        
        Args:
            target: 目标房产
            case: 可比案例
            
        Returns:
            dict: 相似度得分
        """
        similarities = {}
        
        # 1. 时间相似度（越近越好）
        time_diff = case.get('time_diff', 0)
        time_similarity = np.exp(-self.similarity_params['time_decay_rate'] * time_diff)
        similarities['time'] = time_similarity
        
        # 2. 位置相似度（基于经纬度或地址）
        # 实际项目中应使用地理编码API计算真实距离
        location_similarity = 1.0  # 默认最高
        if 'distance' in case:  # 如果已经预先计算了距离
            location_similarity = np.exp(-self.similarity_params['distance_decay_rate'] * case['distance'])
        similarities['location'] = location_similarity
        
        # 3. 物理特性相似度
        # 3.1 面积相似度
        area_similarity = 1.0
        if 'size' in target and 'size' in case:
            area_diff = abs(target['size'] - case['size'])
            area_similarity = np.exp(-area_diff / self.similarity_params['area_tolerance'])
        
        # 3.2 楼层相似度
        floor_similarity = 1.0
        if 'floor' in target and 'floor' in case:
            if target['floor'] == case['floor']:
                floor_similarity = 1.0
            else:
                floor_similarity = 0.5
        
        # 3.3 装修相似度
        decoration_similarity = 1.0
        if 'fitment' in target and 'fitment' in case:
            if target['fitment'] == case['fitment']:
                decoration_similarity = 1.0
            else:
                decoration_similarity = 0.5
        
        # 3.4 房龄相似度
        age_similarity = 1.0
        if 'age' in target and 'age' in case:
            age_diff = abs(target['age'] - case['age'])
            age_similarity = np.exp(-age_diff / 10)  # 10年差异为衰减因子
        
        # 计算物理特性综合相似度
        physical_similarity = (
            area_similarity + 
            self.similarity_params['floor_importance'] * floor_similarity + 
            self.similarity_params['decoration_importance'] * decoration_similarity + 
            self.similarity_params['age_importance'] * age_similarity
        ) / (1 + self.similarity_params['floor_importance'] + self.similarity_params['decoration_importance'] + self.similarity_params['age_importance'])
        
        similarities['physical'] = physical_similarity
        
        # 4. 环境特性相似度
        environment_similarity = 1.0
        if 'green_rate' in target and 'green_rate' in case:
            green_rate_diff = abs(target['green_rate'] - case['green_rate'])
            environment_similarity = np.exp(-green_rate_diff / 0.1)  # 10%差异为衰减因子
        similarities['environment'] = environment_similarity
        
        # 5. 法律特性相似度（简化处理）
        similarities['legal'] = 1.0
        
        # 6. 交易特性相似度
        transaction_similarity = 1.0
        if 'transaction_type' in target and 'transaction_type' in case:
            if target['transaction_type'] == case['transaction_type']:
                transaction_similarity = 1.0
            else:
                transaction_similarity = 0.7  # 不同交易类型打折
        similarities['transaction'] = transaction_similarity
        
        # 计算综合相似度
        total_similarity = sum(self.default_weights[key] * similarities[key] for key in similarities.keys())
        
        return {
            'similarities': similarities,
            'total_similarity': total_similarity
        }
    
    def calculate_adjustment_factors(self, target, case):
        """
        计算修正系数
        
        Args:
            target: 目标房产
            case: 可比案例
            
        Returns:
            dict: 修正系数
        """
        adjustments = {}
        
        # 如果有规则框架，使用规则框架计算修正系数
        if self.rule_framework:
            # 准备数据
            data = {**target, **{f"comp_{k}": v for k, v in case.items()}}
            
            # 应用规则
            rule_results = self.rule_framework.apply_rule_sets(data)
            
            # 提取修正系数
            for rule_set_name, rule_set_result in rule_results.items():
                for rule_name, rule_result in rule_set_result["rule_results"].items():
                    adjustments[f"{rule_set_name}_{rule_name}"] = rule_result
            
            # 综合修正系数
            total_adjustment = rule_set_result["weighted_average"]
            
        else:
            # 如果没有规则框架，使用简单的修正方法
            
            # 1. 时间修正
            time_adjustment = 1.0
            if 'time_diff' in case:
                # 假设每年房价上涨5%
                time_adjustment = 1.0 + 0.05 * case['time_diff']
            adjustments['time'] = time_adjustment
            
            # 2. 面积修正
            area_adjustment = 1.0
            if 'size' in target and 'size' in case:
                # 面积越大，单价越低，假设每增加10平方米，单价下降1%
                area_diff = target['size'] - case['size']
                area_adjustment = 1.0 - 0.01 * (area_diff / 10)
            adjustments['area'] = area_adjustment
            
            # 3. 楼层修正
            floor_adjustment = 1.0
            if 'floor' in target and 'floor' in case:
                # 楼层差异修正
                floor_map = {'低楼层': 0, '中楼层': 1, '高楼层': 2}
                if isinstance(target['floor'], str) and isinstance(case['floor'], str):
                    target_floor = floor_map.get(target['floor'], target['floor'])
                    case_floor = floor_map.get(case['floor'], case['floor'])
                else:
                    target_floor = target['floor']
                    case_floor = case['floor']
                
                floor_diff = target_floor - case_floor
                # 每层差异修正1%
                floor_adjustment = 1.0 + 0.01 * floor_diff
            adjustments['floor'] = floor_adjustment
            
            # 4. 装修修正
            decoration_adjustment = 1.0
            if 'fitment' in target and 'fitment' in case:
                # 装修差异修正
                fitment_map = {'毛坯': 0, '简装': 1, '精装': 2}
                if isinstance(target['fitment'], str) and isinstance(case['fitment'], str):
                    target_fitment = fitment_map.get(target['fitment'], target['fitment'])
                    case_fitment = fitment_map.get(case['fitment'], case['fitment'])
                else:
                    target_fitment = target['fitment']
                    case_fitment = case['fitment']
                
                fitment_diff = target_fitment - case_fitment
                # 每级装修差异修正5%
                decoration_adjustment = 1.0 + 0.05 * fitment_diff
            adjustments['decoration'] = decoration_adjustment
            
            # 5. 房龄修正
            age_adjustment = 1.0
            if 'age' in target and 'age' in case:
                # 房龄差异修正
                age_diff = target['age'] - case['age']
                # 每年房龄差异修正0.5%
                age_adjustment = 1.0 - 0.005 * age_diff
            adjustments['age'] = age_adjustment
            
            # 6. 绿化率修正
            green_rate_adjustment = 1.0
            if 'green_rate' in target and 'green_rate' in case:
                # 绿化率差异修正
                green_rate_diff = target['green_rate'] - case['green_rate']
                # 每10%绿化率差异修正2%
                green_rate_adjustment = 1.0 + 0.2 * green_rate_diff
            adjustments['green_rate'] = green_rate_adjustment
            
            # 计算总修正系数
            total_adjustment = np.prod(list(adjustments.values()))
        
        adjustments['total'] = total_adjustment
        
        return adjustments
    
    def calculate_weights(self, similarities):
        """
        计算案例权重
        
        Args:
            similarities: 相似度列表
            
        Returns:
            list: 权重列表
        """
        # 提取总相似度
        total_similarities = [s['total_similarity'] for s in similarities]
        
        # 使用softmax函数计算权重
        exp_similarities = np.exp(total_similarities)
        weights = exp_similarities / np.sum(exp_similarities)
        
        return weights
    
    def estimate(self, target_property, comparable_cases):
        """
        估算房产价值
        
        Args:
            target_property: 目标房产
            comparable_cases: 可比案例列表
            
        Returns:
            dict: 估值结果
        """
        # 预处理数据
        target, cases = self.preprocess_data(target_property, comparable_cases)
        
        # 计算相似度
        similarities = [self.calculate_similarity(target, case) for case in cases]
        
        # 计算修正系数
        adjustments = [self.calculate_adjustment_factors(target, case) for case in cases]
        
        # 计算权重
        weights = self.calculate_weights(similarities)
        
        # 计算估值
        adjusted_prices = []
        for i, case in enumerate(cases):
            if 'price' in case:
                adjusted_price = case['price'] * adjustments[i]['total']
                adjusted_prices.append(adjusted_price)
            else:
                print(f"警告：案例 {i} 缺少价格信息")
        
        if not adjusted_prices:
            return {
                'estimated_price': None,
                'confidence': 0,
                'details': {
                    'similarities': similarities,
                    'adjustments': adjustments,
                    'weights': weights.tolist() if isinstance(weights, np.ndarray) else weights
                }
            }
        
        # 加权平均估值
        estimated_price = np.sum(np.array(adjusted_prices) * weights[:len(adjusted_prices)])
        
        # 计算置信度
        # 使用权重分布熵作为置信度指标
        weights_entropy = -np.sum(weights * np.log(weights + 1e-10)) / np.log(len(weights))
        confidence = 1 - weights_entropy  # 熵越低，置信度越高
        
        # 构建结果
        result = {
            'estimated_price': float(estimated_price),
            'confidence': float(confidence),
            'details': {
                'similarities': similarities,
                'adjustments': adjustments,
                'weights': weights.tolist() if isinstance(weights, np.ndarray) else weights,
                'adjusted_prices': adjusted_prices
            }
        }
        
        return result
    
    def generate_explanation(self, estimation_result, target_property, comparable_cases):
        """
        生成估值解释
        
        Args:
            estimation_result: 估值结果
            target_property: 目标房产
            comparable_cases: 可比案例
            
        Returns:
            str: 估值解释
        """
        if estimation_result['estimated_price'] is None:
            return "无法生成估值解释，因为没有有效的可比案例。"
        
        # 提取关键信息
        estimated_price = estimation_result['estimated_price']
        confidence = estimation_result['confidence']
        details = estimation_result['details']
        
        # 生成解释文本
        explanation = f"基于智能化市场比较法(IMCA)，估计目标房产的单价为 {estimated_price:.2f} 元/平方米，置信度为 {confidence:.2%}。\n\n"
        
        # 添加可比案例信息
        explanation += "分析使用了以下可比案例：\n"
        for i, case in enumerate(comparable_cases):
            price = case.get('price', 'N/A')
            address = case.get('address', '未知地址')
            similarity = details['similarities'][i]['total_similarity']
            weight = details['weights'][i]
            
            explanation += f"案例 {i+1}：单价 {price} 元/平方米，位于 {address}，相似度 {similarity:.2%}，权重 {weight:.2%}\n"
        
        # 添加主要影响因素
        explanation += "\n主要影响因素：\n"
        
        # 分析物理特性
        if 'size' in target_property:
            explanation += f"- 面积：目标房产面积为 {target_property['size']} 平方米"
            if target_property['size'] > 120:
                explanation += "，属于大户型，单价相对较低。\n"
            elif target_property['size'] < 60:
                explanation += "，属于小户型，单价相对较高。\n"
            else:
                explanation += "，属于中等户型，单价适中。\n"
        
        # 分析楼层
        if 'floor' in target_property:
            explanation += f"- 楼层：目标房产位于 {target_property['floor']}，"
            if target_property['floor'] == '高楼层' or (isinstance(target_property['floor'], (int, float)) and target_property['floor'] > 10):
                explanation += "视野较好，采光充足，对价格有正面影响。\n"
            elif target_property['floor'] == '低楼层' or (isinstance(target_property['floor'], (int, float)) and target_property['floor'] < 3):
                explanation += "便于出行，但可能视野受限，对价格有一定负面影响。\n"
            else:
                explanation += "楼层适中，对价格影响中性。\n"
        
        # 分析装修
        if 'fitment' in target_property:
            explanation += f"- 装修：目标房产装修状况为 {target_property['fitment']}，"
            if target_property['fitment'] == '精装' or target_property['fitment'] == 2:
                explanation += "精装修状况良好，对价格有明显正面影响。\n"
            elif target_property['fitment'] == '简装' or target_property['fitment'] == 1:
                explanation += "简单装修，对价格有一定正面影响。\n"
            else:
                explanation += "毛坯房，需要额外装修成本，对价格有一定负面影响。\n"
        
        # 分析房龄
        if 'age' in target_property:
            explanation += f"- 房龄：目标房产房龄为 {target_property['age']} 年，"
            if target_property['age'] < 5:
                explanation += "属于新房，对价格有正面影响。\n"
            elif target_property['age'] > 20:
                explanation += "房龄较长，可能需要维护，对价格有一定负面影响。\n"
            else:
                explanation += "房龄适中，对价格影响中性。\n"
        
        # 添加置信度解释
        explanation += f"\n估值置信度为 {confidence:.2%}，"
        if confidence > 0.8:
            explanation += "表示可比案例与目标房产高度相似，估值结果可靠性高。"
        elif confidence > 0.5:
            explanation += "表示可比案例与目标房产相似度适中，估值结果可靠性中等。"
        else:
            explanation += "表示可比案例与目标房产相似度较低，估值结果仅供参考。"
        
        return explanation 