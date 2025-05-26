"""
房估宝 - 房产估值新范式
Web应用入口
"""
import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# 确保可以导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import PropertyValuationSystem
except ImportError as e:
    print(f"导入模块失败: {str(e)}")
    print("请确保已安装所有依赖项，并且所有模块都存在")
    sys.exit(1)

# 创建Flask应用
app = Flask(__name__)

# 配置上传文件目录
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 创建房产估值系统
valuation_system = PropertyValuationSystem()

def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@app.route('/valuation')
def valuation():
    """估值页面"""
    return render_template('valuation.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件API"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件部分'})
    
    file = request.files['file']
    file_type = request.form.get('type', 'photo')  # 文件类型：cert（房产证）或photo（房屋照片）
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        # 安全地获取文件名并保存
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'file_path': file_path,
            'url': f"/static/uploads/{new_filename}"
        })
    
    return jsonify({'success': False, 'error': '不允许的文件类型'})

@app.route('/api/valuation', methods=['POST'])
def api_valuation():
    """估值API"""
    try:
        data = request.get_json()
        
        # 提取房产数据
        property_data = {
            "address": data.get('address'),
            "city": data.get('city'),
            "property_cert_image": data.get('cert_image'),
            "property_photo": data.get('property_photo'),
            "property_text": data.get('description')
        }
        
        # 处理房产数据
        processed_data = valuation_system.process_property_data(property_data)
        
        # 准备目标房产数据
        target_property = {
            "size": float(data.get('area', 90)),
            "floor": data.get('floor', '中楼层'),
            "fitment": data.get('fitment', '简装'),
            "built_time": f"{data.get('year', 2015)}-01-01",
            "green_rate": processed_data.get("enhanced_data", {}).get("property_info", {}).get("green_rate", 0.3),
            "transaction_type": 1
        }
        
        # 估算房产价值
        estimation_result = valuation_system.estimate_property_value(target_property)
        
        # 生成报告
        report_path = valuation_system.generate_report(property_data, estimation_result)
        
        # 构建响应
        response = {
            'success': True,
            'estimated_price': estimation_result['estimated_price'],
            'confidence': estimation_result['confidence'],
            'total_price': estimation_result['estimated_price'] * float(data.get('area', 90)),
            'explanation': estimation_result['explanation'],
            'report_path': report_path
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"估值失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reports/<filename>')
def get_report(filename):
    """获取报告API"""
    reports_dir = os.path.join("static", "reports")
    return send_from_directory(reports_dir, filename)

@app.route('/reports')
def reports():
    """报告列表页面"""
    reports_dir = os.path.join("static", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    reports_list = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(reports_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                # 提取报告信息
                address = report_data.get('property_data', {}).get('address', '未知地址')
                estimated_price = report_data.get('estimation_result', {}).get('estimated_price', 0)
                generated_at = report_data.get('generated_at', '')
                
                reports_list.append({
                    'filename': filename,
                    'address': address,
                    'estimated_price': estimated_price,
                    'generated_at': generated_at
                })
            except Exception as e:
                print(f"读取报告失败 {filename}: {str(e)}")
    
    # 按生成时间排序
    reports_list.sort(key=lambda x: x['generated_at'], reverse=True)
    
    return render_template('reports.html', reports=reports_list)

@app.route('/report/<filename>')
def view_report(filename):
    """查看报告页面"""
    reports_dir = os.path.join("static", "reports")
    file_path = os.path.join(reports_dir, filename)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return render_template('report.html', report=report_data)
    except Exception as e:
        return render_template('error.html', error=f"读取报告失败: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 