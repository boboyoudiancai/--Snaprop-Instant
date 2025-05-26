"""
本模块包含可微分规则学习框架，将专家估值规则转化为端到端可训练的神经模块
"""
import numpy as np
import json
import os
from datetime import datetime

class RuleType:
    """规则类型枚举"""
    COMPARISON = "comparison"  # 比较规则
    THRESHOLD = "threshold"    # 阈值规则
    RANGE = "range"            # 范围规则
    CATEGORICAL = "categorical"  # 类别规则

class Rule:
    """规则基类"""
    def __init__(self, name, description, weight=1.0):
        """
        初始化规则
        
        Args:
            name: 规则名称
            description: 规则描述
            weight: 规则权重
        """
        self.name = name
        self.description = description
        self.weight = weight
        self.is_trainable = True
    
    def apply(self, data):
        """
        应用规则
        
        Args:
            data: 输入数据
            
        Returns:
            float: 规则应用结果（0-1之间）
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def to_dict(self):
        """
        将规则转换为字典
        
        Returns:
            dict: 规则字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "is_trainable": self.is_trainable,
            "type": self.__class__.__name__
        }
    
    @staticmethod
    def from_dict(rule_dict):
        """
        从字典创建规则
        
        Args:
            rule_dict: 规则字典
            
        Returns:
            Rule: 规则对象
        """
        rule_type = rule_dict.pop("type", None)
        if rule_type == "ComparisonRule":
            return ComparisonRule(**rule_dict)
        elif rule_type == "ThresholdRule":
            return ThresholdRule(**rule_dict)
        elif rule_type == "RangeRule":
            return RangeRule(**rule_dict)
        elif rule_type == "CategoricalRule":
            return CategoricalRule(**rule_dict)
        else:
            raise ValueError(f"未知规则类型: {rule_type}")


class ComparisonRule(Rule):
    """比较规则"""
    def __init__(self, name, description, feature1, feature2, operator="greater", margin=0.0, weight=1.0):
        """
        初始化比较规则
        
        Args:
            name: 规则名称
            description: 规则描述
            feature1: 特征1
            feature2: 特征2
            operator: 比较运算符 ("greater", "less", "equal")
            margin: 比较边界
            weight: 规则权重
        """
        super().__init__(name, description, weight)
        self.feature1 = feature1
        self.feature2 = feature2
        self.operator = operator
        self.margin = margin
    
    def apply(self, data):
        """
        应用比较规则
        
        Args:
            data: 输入数据
            
        Returns:
            float: 规则应用结果（0-1之间）
        """
        if self.feature1 not in data or self.feature2 not in data:
            return 0.5  # 缺失特征时返回中性值
        
        value1 = data[self.feature1]
        value2 = data[self.feature2]
        
        if self.operator == "greater":
            diff = value1 - value2
            # 使用sigmoid函数将差值映射到0-1之间
            return 1 / (1 + np.exp(-diff / (self.margin + 1e-6)))
        elif self.operator == "less":
            diff = value2 - value1
            return 1 / (1 + np.exp(-diff / (self.margin + 1e-6)))
        elif self.operator == "equal":
            diff = abs(value1 - value2)
            return np.exp(-diff / (self.margin + 1e-6))
        else:
            raise ValueError(f"未知比较运算符: {self.operator}")
    
    def to_dict(self):
        """
        将规则转换为字典
        
        Returns:
            dict: 规则字典
        """
        rule_dict = super().to_dict()
        rule_dict.update({
            "feature1": self.feature1,
            "feature2": self.feature2,
            "operator": self.operator,
            "margin": self.margin
        })
        return rule_dict


class ThresholdRule(Rule):
    """阈值规则"""
    def __init__(self, name, description, feature, threshold, direction="above", smoothness=1.0, weight=1.0):
        """
        初始化阈值规则
        
        Args:
            name: 规则名称
            description: 规则描述
            feature: 特征名
            threshold: 阈值
            direction: 方向 ("above" 或 "below")
            smoothness: 平滑度
            weight: 规则权重
        """
        super().__init__(name, description, weight)
        self.feature = feature
        self.threshold = threshold
        self.direction = direction
        self.smoothness = smoothness
    
    def apply(self, data):
        """
        应用阈值规则
        
        Args:
            data: 输入数据
            
        Returns:
            float: 规则应用结果（0-1之间）
        """
        if self.feature not in data:
            return 0.5  # 缺失特征时返回中性值
        
        value = data[self.feature]
        
        if self.direction == "above":
            # 使用sigmoid函数平滑过渡
            return 1 / (1 + np.exp(-(value - self.threshold) / self.smoothness))
        elif self.direction == "below":
            return 1 / (1 + np.exp((value - self.threshold) / self.smoothness))
        else:
            raise ValueError(f"未知方向: {self.direction}")
    
    def to_dict(self):
        """
        将规则转换为字典
        
        Returns:
            dict: 规则字典
        """
        rule_dict = super().to_dict()
        rule_dict.update({
            "feature": self.feature,
            "threshold": self.threshold,
            "direction": self.direction,
            "smoothness": self.smoothness
        })
        return rule_dict


class RangeRule(Rule):
    """范围规则"""
    def __init__(self, name, description, feature, min_value, max_value, mode="inside", smoothness=1.0, weight=1.0):
        """
        初始化范围规则
        
        Args:
            name: 规则名称
            description: 规则描述
            feature: 特征名
            min_value: 最小值
            max_value: 最大值
            mode: 模式 ("inside" 或 "outside")
            smoothness: 平滑度
            weight: 规则权重
        """
        super().__init__(name, description, weight)
        self.feature = feature
        self.min_value = min_value
        self.max_value = max_value
        self.mode = mode
        self.smoothness = smoothness
    
    def apply(self, data):
        """
        应用范围规则
        
        Args:
            data: 输入数据
            
        Returns:
            float: 规则应用结果（0-1之间）
        """
        if self.feature not in data:
            return 0.5  # 缺失特征时返回中性值
        
        value = data[self.feature]
        
        # 计算与范围边界的距离
        if value < self.min_value:
            distance = self.min_value - value
        elif value > self.max_value:
            distance = value - self.max_value
        else:
            distance = 0
        
        # 根据模式计算结果
        if self.mode == "inside":
            # 在范围内为1，范围外平滑过渡到0
            return np.exp(-distance / self.smoothness)
        elif self.mode == "outside":
            # 在范围外为1，范围内平滑过渡到0
            if distance == 0:
                # 在范围内
                center = (self.min_value + self.max_value) / 2
                max_distance = (self.max_value - self.min_value) / 2
                internal_distance = abs(value - center) / max_distance
                return 1 - np.exp(-internal_distance / self.smoothness)
            else:
                # 在范围外
                return 1
        else:
            raise ValueError(f"未知模式: {self.mode}")
    
    def to_dict(self):
        """
        将规则转换为字典
        
        Returns:
            dict: 规则字典
        """
        rule_dict = super().to_dict()
        rule_dict.update({
            "feature": self.feature,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mode": self.mode,
            "smoothness": self.smoothness
        })
        return rule_dict


class CategoricalRule(Rule):
    """类别规则"""
    def __init__(self, name, description, feature, categories, values=None, default_value=0.5, weight=1.0):
        """
        初始化类别规则
        
        Args:
            name: 规则名称
            description: 规则描述
            feature: 特征名
            categories: 类别列表
            values: 类别对应的值列表
            default_value: 默认值
            weight: 规则权重
        """
        super().__init__(name, description, weight)
        self.feature = feature
        self.categories = categories
        
        # 如果没有提供值，则默认为均匀分布
        if values is None:
            self.values = [1.0] * len(categories)
        else:
            self.values = values
        
        self.default_value = default_value
    
    def apply(self, data):
        """
        应用类别规则
        
        Args:
            data: 输入数据
            
        Returns:
            float: 规则应用结果（0-1之间）
        """
        if self.feature not in data:
            return self.default_value  # 缺失特征时返回默认值
        
        value = data[self.feature]
        
        # 查找类别索引
        try:
            index = self.categories.index(value)
            return self.values[index]
        except ValueError:
            return self.default_value  # 未知类别时返回默认值
    
    def to_dict(self):
        """
        将规则转换为字典
        
        Returns:
            dict: 规则字典
        """
        rule_dict = super().to_dict()
        rule_dict.update({
            "feature": self.feature,
            "categories": self.categories,
            "values": self.values,
            "default_value": self.default_value
        })
        return rule_dict


class RuleSet:
    """规则集"""
    def __init__(self, name, description=""):
        """
        初始化规则集
        
        Args:
            name: 规则集名称
            description: 规则集描述
        """
        self.name = name
        self.description = description
        self.rules = []
    
    def add_rule(self, rule):
        """
        添加规则
        
        Args:
            rule: 规则对象
        """
        self.rules.append(rule)
    
    def apply(self, data):
        """
        应用规则集
        
        Args:
            data: 输入数据
            
        Returns:
            dict: 规则应用结果
        """
        results = {}
        weighted_sum = 0
        total_weight = 0
        
        for rule in self.rules:
            result = rule.apply(data)
            results[rule.name] = result
            weighted_sum += result * rule.weight
            total_weight += rule.weight
        
        # 计算加权平均值
        if total_weight > 0:
            weighted_average = weighted_sum / total_weight
        else:
            weighted_average = 0.5  # 如果没有规则，返回中性值
        
        return {
            "rule_results": results,
            "weighted_average": weighted_average
        }
    
    def to_dict(self):
        """
        将规则集转换为字典
        
        Returns:
            dict: 规则集字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "rules": [rule.to_dict() for rule in self.rules]
        }
    
    def save(self, file_path):
        """
        保存规则集到文件
        
        Args:
            file_path: 文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load(file_path):
        """
        从文件加载规则集
        
        Args:
            file_path: 文件路径
            
        Returns:
            RuleSet: 规则集对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rule_set = RuleSet(data["name"], data["description"])
        
        for rule_data in data["rules"]:
            rule = Rule.from_dict(rule_data)
            rule_set.add_rule(rule)
        
        return rule_set


class DifferentiableRuleLearningFramework:
    """可微分规则学习框架"""
    def __init__(self):
        """初始化框架"""
        self.rule_sets = {}
        self.training_data = []
    
    def add_rule_set(self, rule_set):
        """
        添加规则集
        
        Args:
            rule_set: 规则集对象
        """
        self.rule_sets[rule_set.name] = rule_set
    
    def add_training_data(self, data, label):
        """
        添加训练数据
        
        Args:
            data: 输入数据
            label: 标签
        """
        self.training_data.append((data, label))
    
    def apply_rule_sets(self, data):
        """
        应用所有规则集
        
        Args:
            data: 输入数据
            
        Returns:
            dict: 规则应用结果
        """
        results = {}
        
        for name, rule_set in self.rule_sets.items():
            results[name] = rule_set.apply(data)
        
        return results
    
    def train(self, learning_rate=0.01, epochs=100):
        """
        训练规则权重
        
        Args:
            learning_rate: 学习率
            epochs: 训练轮数
            
        Returns:
            list: 训练损失历史
        """
        if not self.training_data:
            print("没有训练数据")
            return []
        
        loss_history = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            
            for data, label in self.training_data:
                # 前向传播
                results = self.apply_rule_sets(data)
                
                # 计算损失
                for rule_set_name, rule_set_result in results.items():
                    prediction = rule_set_result["weighted_average"]
                    loss = (prediction - label) ** 2
                    epoch_loss += loss
                    
                    # 反向传播
                    gradient = 2 * (prediction - label)
                    
                    # 更新规则权重
                    rule_set = self.rule_sets[rule_set_name]
                    total_weight = sum(rule.weight for rule in rule_set.rules)
                    
                    for rule in rule_set.rules:
                        if rule.is_trainable:
                            rule_result = rule_set_result["rule_results"][rule.name]
                            weight_gradient = gradient * (rule_result - prediction) / total_weight
                            rule.weight -= learning_rate * weight_gradient
                            
                            # 确保权重非负
                            rule.weight = max(0.1, rule.weight)
            
            # 记录平均损失
            avg_loss = epoch_loss / len(self.training_data)
            loss_history.append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")
        
        return loss_history
    
    def save(self, directory):
        """
        保存框架到目录
        
        Args:
            directory: 目录路径
        """
        os.makedirs(directory, exist_ok=True)
        
        # 保存规则集
        for name, rule_set in self.rule_sets.items():
            file_path = os.path.join(directory, f"{name}.json")
            rule_set.save(file_path)
        
        # 保存训练数据
        training_data_path = os.path.join(directory, "training_data.json")
        with open(training_data_path, 'w', encoding='utf-8') as f:
            json.dump(self.training_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load(directory):
        """
        从目录加载框架
        
        Args:
            directory: 目录路径
            
        Returns:
            DifferentiableRuleLearningFramework: 框架对象
        """
        framework = DifferentiableRuleLearningFramework()
        
        # 加载规则集
        for file_name in os.listdir(directory):
            if file_name.endswith(".json") and file_name != "training_data.json":
                file_path = os.path.join(directory, file_name)
                rule_set = RuleSet.load(file_path)
                framework.add_rule_set(rule_set)
        
        # 加载训练数据
        training_data_path = os.path.join(directory, "training_data.json")
        if os.path.exists(training_data_path):
            with open(training_data_path, 'r', encoding='utf-8') as f:
                framework.training_data = json.load(f)
        
        return framework


# 创建一些示例规则
def create_example_rules():
    """
    创建示例规则
    
    Returns:
        RuleSet: 示例规则集
    """
    # 创建房产估值规则集
    property_valuation = RuleSet("房产估值规则", "用于房产估值的规则集")
    
    # 添加规则
    
    # 1. 面积规则
    property_valuation.add_rule(
        RangeRule(
            name="面积适中规则",
            description="面积在60-120平方米之间最受欢迎",
            feature="house_area",
            min_value=60,
            max_value=120,
            mode="inside",
            smoothness=20,
            weight=1.0
        )
    )
    
    # 2. 楼层规则
    property_valuation.add_rule(
        CategoricalRule(
            name="楼层偏好规则",
            description="不同楼层的受欢迎程度",
            feature="house_floor",
            categories=["低楼层", "中楼层", "高楼层"],
            values=[0.7, 1.0, 0.8],
            weight=0.8
        )
    )
    
    # 3. 装修规则
    property_valuation.add_rule(
        CategoricalRule(
            name="装修偏好规则",
            description="不同装修状况的受欢迎程度",
            feature="house_decorating",
            categories=["毛坯", "简装", "精装"],
            values=[0.6, 0.8, 1.0],
            weight=1.2
        )
    )
    
    # 4. 房龄规则
    property_valuation.add_rule(
        ThresholdRule(
            name="房龄规则",
            description="房龄越小越好",
            feature="house_age",
            threshold=10,
            direction="below",
            smoothness=5,
            weight=0.9
        )
    )
    
    # 5. 绿化率规则
    property_valuation.add_rule(
        ThresholdRule(
            name="绿化率规则",
            description="绿化率越高越好",
            feature="green_rate",
            threshold=0.3,
            direction="above",
            smoothness=0.1,
            weight=0.7
        )
    )
    
    # 6. 交通便利性规则
    property_valuation.add_rule(
        ThresholdRule(
            name="交通便利性规则",
            description="交通设施评分越高越好",
            feature="transportation_score",
            threshold=0.7,
            direction="above",
            smoothness=0.2,
            weight=1.1
        )
    )
    
    # 7. 教育资源规则
    property_valuation.add_rule(
        ThresholdRule(
            name="教育资源规则",
            description="教育设施评分越高越好",
            feature="education_score",
            threshold=0.6,
            direction="above",
            smoothness=0.2,
            weight=1.3
        )
    )
    
    return property_valuation 