# 时间：2024/11/5  10:46
import datetime
import os
import pandas as pd
from PIL import Image
from reportlab.graphics.barcode import qr
from reportlab.lib.colors import black
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import cn2an
from datetime import datetime, date

from record.record import Record
from config.path_config import OCR_PATH, REPORT_PATH, MAP_PATH, UPLOAD_FOLDER
from report.ocr import OCR_Table
from database.mysql_manager import MySQLManager

pdfmetrics.registerFont(TTFont("SimHei", "SimHei.ttf"))
pdfmetrics.registerFont(TTFont("SimSun", "SimSun.ttc"))
pdfmetrics.registerFont(TTFont("SimSunb", "simsunb.ttf"))
pdfmetrics.registerFont(TTFont("simfang", "simfang.ttf"))
pdfmetrics.registerFont(TTFont("simkai", "simkai.ttf"))

pdfmetrics.registerFont(TTFont("segoeuib", "segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("segoeuil", "segoeuil.ttf"))
pdfmetrics.registerFont(TTFont("segoeuisl", "segoeuisl.ttf"))
pdfmetrics.registerFont(TTFont("seguisb", "seguisb.ttf"))


# 我实在是找不到怎么设置加粗字体
class PDFReport:
    def __init__(self, out_file_path: str, property_name: str, pagesize=A4):
        self.index = ""  # 报告编号
        self.result = canvas.Canvas(out_file_path, pagesize)  # 生成的pdf对象
        self.pagenum = 0  # 总页数
        self.title = ""  # 报告标题
        self.subtitle = ""  # 报告副标题
        self.date = date.today().strftime("%Y年%m月%d日")  # 日期
        self.property_name = property_name  # 房产名名称
        self.width, self.height = pagesize  # 页面宽高（像素）
        self.image = []  # 每个要插入图片的路径，位置，大小和页面
        self.text = []  # 每个要插入文字的路径，位置，最大宽度和页面和格式（字体大小和字体格式）
        self.table = []  # 每个要插入表格的路径，位置，最大宽度和页面和格式（字体大小和字体格式）
        self.lines = []
        self.template = {
            "敬启者：": "",
            "主旨：": "",
            "__前言": {
                "估值委托、用途及日期": "",
                "市场价值定义": "",
                "估值假设": "",
                "评估方法": "",
                "资料来源": "",
                "业权查核": "",
                "现场勘查": "",
                "币值": "",
            },
            "评估物业": {
                "物业位置": ""
            },
            "区域位置": {
                "__城市": (),
                "人口，面积及行政区划": "",
                "邻近环境及建筑物": "",
                "交通条件": "",
            },
            "业权状况": {
                "__制度简介": (),
                "相关权证": "",
                "表格集": [pd.DataFrame()],
            },
            "物业概况": {
                "__": ""
            },
            "占用概况": {
                "__": ""
            },
            "评估基准": {
                "评估物业": "",
                "估值假设及特殊假设": ""
            },
            "估值结果": {
                "估值结果": "",
                "非出版物及注意事项": ""
            },
            "__附录": {},
            "目录 ": {
                "评估物业": 0,
                "区域位置": 0,
                "业权状况": 0,
                "物业概况": 0,
                "占用概况": 0,
                "评估基准": 0,
                "估值结果": 0,
            },
        }  # 房产估价模板

    # 添加图片,x,y表示起始位置
    def add_image(self, image_path: str, x, y, page: int, width=None, height=None):
        self.image.append({"image_path": image_path,
                           "x": x,
                           "y": y,
                           "width": width,
                           "height": height,
                           "page": page})
        self.pagenum = max(page, self.pagenum)

    # 修改图片x,y表示起始位置
    def update_image(self, index: int, image_path: str, x, y, page, width=None, height=None):
        if index >= len(self.image):
            return False
        self.image[index] = {"image_path": image_path,
                             "x": x,
                             "y": y,
                             "width": width,
                             "height": height,
                             "page": page}
        self.pagenum = max(page, self.pagenum)
        return True

    # 添加文字x,y表示起始位置
    def add_text(self, text: str, x, y, page, width=None, font="SimHei", size=12):
        text, num_n = self.wrap_text(text, size, font, width)
        self.text.append({"text": text,
                          "x": x,
                          "y": y,
                          "font": font,
                          "size": size,
                          "page": page,
                          "width": width})
        self.pagenum = max(page, self.pagenum)
        return num_n

    # 修改文字x,y表示起始位置
    def update_text(self, index: int, text: str, x, y, page, width=None, font="SimHei", size=12):
        text, num_n = self.wrap_text(text, size, font, width)
        self.text[index] = {"text": text,
                            "x": x,
                            "y": y,
                            "font": font,
                            "size": size,
                            "page": page,
                            "width": width}
        self.pagenum = max(page, self.pagenum)
        return num_n

    # 添加表格，x,y表示起始位置,aW,aH表示容许的最大长度
    def add_table(self, table: pd.DataFrame, x, y, aW, aH, page, tbstyle=None):

        f = Table(table.values.tolist())
        f.setStyle(tbstyle)
        w, h = f.wrap(aW, aH)
        if w > aW or h > aH:
            return -1, -1
        self.table.append({"table": f,
                           "x": x,
                           "y": y,
                           "w": w,
                           "h": h,
                           "tbstyle": tbstyle,
                           "page": page})
        self.pagenum = max(page, self.pagenum)
        return w, h

    # 修改表格，x,y表示起始位置,aW,aH表示容许的最大长度
    def update_table(self, index: int, table: pd.DataFrame, x, y, aW, aH, page, tbstyle=None):
        f = Table(table.values.tolist())
        f.setStyle(tbstyle)
        print(aH)
        w, h = f.wrap(aW, aH)
        if w > aW or h > aH:
            return -1, -1
        self.table[index] = {"table": f,
                             "x": x,
                             "y": y,
                             "w": w,
                             "h": h,
                             "tbstyle": tbstyle,
                             "page": page}
        self.pagenum = max(page, self.pagenum)
        return w, h

    def add_line(self, x1, y1, x2, y2, width, page):
        self.lines.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "width": width,
            "page": page
        })
        self.pagenum = max(page, self.pagenum)

    # TODO：删除操作也要有
    # 将文字根据最大宽度分段
    # 或许可以通过Paragraph自动换行
    def wrap_text(self, txt: str, font_size, font_name, width=None) -> tuple[str, int]:
        char_widths = [stringWidth(char, font_name, font_size) for char in txt]
        line_width = 0
        wrapped_text = ""
        num_n = 1
        for i, char in enumerate(txt):
            if char == '\n':
                line_width = 0
                wrapped_text += char
                num_n += 1
                continue
            line_width += char_widths[i]
            if width != None and line_width > width:
                wrapped_text += '\n'
                line_width = char_widths[i]
                num_n += 1
            wrapped_text += char
        return wrapped_text, num_n

    # 将list的内容绘制在pdf上
    def generate_pdf(self):
        self.result.setTitle(self.subtitle)
        for i in range(1, self.pagenum + 1):
            qr_code = qr.QrCode('https://www.tongji.edu.cn/', width=45, height=45)
            self.result.setFillColorRGB(0, 0, 0)
            qr_code.drawOn(self.result, 0, A4[1] - 45)
            for text in self.text:
                if text["page"] == i:
                    # print(text["x"], text["y"])
                    text_tmp = text['text'].split('\n')
                    textobject = self.result.beginText(x=text["x"], y=text["y"])
                    textobject.setFont(text["font"], text["size"])
                    textobject.textLines(text_tmp, 0)
                    self.result.drawText(textobject)
            for img in self.image:
                if img["page"] == i:
                    self.result.drawImage(x=img["x"], y=img["y"], image=img["image_path"], width=img["width"],
                                          height=img["height"])
            for t in self.table:
                if t["page"] == i:
                    t["table"].drawOn(self.result, t['x'], t['y'] - t['h'])
            for line in self.lines:
                if line["page"] == i:
                    self.result.setLineWidth(line["width"])
                    self.result.line(line['x1'], line['y1'], line['x2'], line['y2'])
            self.result.showPage()
        self.result.save()

    # 填充模板，可以整个填，也可以修改单个
    def fill_template(self, value, key1=None, key2=None):
        if key1 == None and key2 == None:
            assert type(value) == dict, type(value)
            self.template = value
        if key1 != None:
            if key2 == None:
                # assert type(value)== dict,type(value)
                self.template[key1] = value
            else:
                assert type(value) == str, type(value)
                self.template[key1][key2] = value
        pass

    # 以下函数开始，体现模板各个参数，有些作为接口，有些写死在函数内部
    # 添加封面
    def set_cover(self, cover_img=None, title: str = None, subtitle: str = None):
        if title == None:
            self.title = "房地产评估估值报告"
        if subtitle == None:
            self.subtitle = self.property_name + "\n之市场价值评估"
        if cover_img != None:
            self.add_image(cover_img, self.width / 10, self.height / 3, 1, self.width / 3, self.height / 4)
        self.add_text(text=self.title, x=self.width / 10, y=4 * self.height / 5, font="SimHei", size=16, page=1,
                      width=16 * 12)
        self.add_text(text=self.subtitle, x=self.width / 10, y=2 * self.height / 3, font="SimHei", size=12, page=1,
                      width=12 * 12)
        self.add_text(text=self.date, x=self.width / 10, y=self.height / 5, font="SimHei", size=10, page=1,
                      width=10 * 12)

    # 页眉页底文字（很丑陋，得改，得包括logo和其他相对静态的部分,数据写死了，得有更改的接口）
    def set_up_down_label(self, logo_img=None, start_page=1, end_page=None, index: str = ""):
        self.index = index
        if end_page == None:
            end_page = self.pagenum
        assert start_page >= 1 and end_page <= self.pagenum, "页面数越界"
        font = "simkai"
        size = 10
        for i in range(start_page, end_page + 1):
            self.add_image(logo_img, 7 * self.width / 10, 92 * self.height / 100, i, 2 * self.width / 10,
                           7 * self.height / 100)
            n1 = self.add_text(self.property_name, self.width / 10, 9 * self.height / 10, i, 19 * size, font, size)
            n2 = self.add_text("估价时点\n" + self.date, 75 * self.width / 100, 9 * self.height / 10, i, 10 * size,
                               font,
                               size)
            self.add_line(self.width / 10, 9 * self.height / 10 + size * 1.3, 91 * self.width / 100,
                          9 * self.height / 10 + size * 1.3, 2, i)
            self.add_line(self.width / 10, 9 * self.height / 10 + (1 - max(n1, n2)) * size * 1.5, 91 * self.width / 100,
                          9 * self.height / 10 + (1 - max(n1, n2)) * size * 1.5, 2, i)
            self.add_text("报告编号:" + self.index, self.width / 10, self.height / 15, i)
            page_str = f"%d/%d" % (i, self.pagenum)
            str_length = sum([stringWidth(char, font, size) for char in page_str])
            self.add_text(page_str, 9 * self.width / 10 - str_length, self.height / 15, i)  # 丑陋的右对齐
            self.add_line(self.width / 10, self.height / 15 + size * 1.2, 91 * self.width / 100,
                          self.height / 15 + size * 1.2, 2, i)

    # 载入模板，
    def template_to_l(self):
        page_n = 2  # 页数，封面已经加入
        start_x = self.width / 10  # 起始位置
        start_y = 85 * self.height / 100  # 起始位置
        body_width = self.width - 2 * start_x  # 主体宽度
        y = start_y  # 当前行
        title_size = 16  # 标题字号
        subtitle1_size = 14  # 副标题1字号
        subtitle2_size = 12  # 副标题2字号
        content_size = 11  # 内容字号
        subtitle_width = 6  # 副标题宽度（字数）
        content_width = 34  # 内容宽度（字数）
        content_page = 0  # 菜单页码
        min_y = 2 * self.height / 15  # 主体内容可以达到最低处
        for key in self.template:
            if key == "敬启者：" or key == "主旨：":
                assert self.template[key] != ""
                self.add_text(key + self.template[key], start_x, y, 2, font="SimHei", size=subtitle2_size)
                y -= subtitle2_size * 2.2
            elif key == "__附录":
                for key2 in self.template[key]:
                    self.add_text(key2, self.width / 2 - len(key2) / 2 * title_size, y, page_n, size=title_size)
                    y -= title_size * 1.2
                    self.template["目录"][key2] = page_n
                    for img in self.template[key][key2]:
                        width, height = Image.open(img).size
                        if (width / height) >= (self.width / (y - min_y + 1e-6)):
                            w = body_width
                            h = w * height / width
                        else:
                            page_n += 1
                            y = start_y
                            if (width / height) >= (self.width / (y - min_y + 1e-6)):
                                w = body_width
                                h = w * height / width
                            else:
                                h = y - min_y
                                w = h * width / height
                        self.add_image(img, self.width / 2 - w / 2, y - h, page_n, w, h)
                        y -= h
                    y = start_y
                    page_n += 1
                continue
            elif key == "目录":
                self.add_text(key, start_x, y, content_page, font="SimHei", size=title_size)
                y -= title_size * 2.2
                a = " ................................................"
                for key2 in self.template[key]:
                    num_n2 = self.add_text(f"{key2}{a}{self.template[key][key2]}",
                                           start_x + (subtitle_width + 2) * subtitle2_size,
                                           y, content_page, width=content_width * content_size, font="SimHei",
                                           size=content_size)
                    y -= content_size * 1.2 * num_n2 + content_size * 3
                    if y <= 2 * self.height / 15:
                        y = start_y
                        page_n += 1
                        num_n2 = self.update_text(-1, f"{key2}{a}{self.template[key][key2]}",
                                                  start_x + (subtitle_width + 2) * subtitle2_size,
                                                  y, content_page, width=content_width * content_size, font="SimHei",
                                                  size=content_size)
                        y -= content_size * 1.2 * num_n2 + content_size * 3
                page_n += 1
                y = start_y
                continue
            else:
                if key == "评估物业":
                    content_page = page_n
                    page_n += 1
                if self.template[key] == "":
                    continue
                if key[0] != '_':
                    self.add_text(key, start_x, y, page_n, font="SimHei", size=title_size)
                    y -= title_size * 2.2
                for key2 in self.template[key]:
                    if (key2 == "表格集"):
                        ts = [
                            ('FONT', (0, 0), (-1, -1), 'SimHei', 7),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('GRID', (0, 0), (-1, -1), 2, black),
                            ('FONT', (1, 0), (1, -1), 'SimSun', 7),
                        ]
                        aW = content_width * content_size
                        aH = y - min_y
                        for data in self.template[key]["表格集"]:
                            w, h = self.add_table(data, start_x + (subtitle_width + 2) * subtitle2_size, y, aW, aH,
                                                  page_n, ts)
                            y -= h * 1.2
                            if w == -1 or h == -1:
                                y = start_y
                                page_n += 1
                                w, h = self.add_table(data, start_x + (subtitle_width + 2) * subtitle2_size, y, aW, aH,
                                                      page_n, ts)
                                print(aW, aH, w, h)
                                assert w != -1 and h != -1, "表格太大，一页装不下"
                                y -= h * 1.2
                        continue
                    if self.template[key][key2] == "" or self.template[key][key2] == ():
                        continue
                    if key2[0] == '_' and type(self.template[key][key2]) == tuple:
                        num_n1 = self.add_text(self.template[key][key2][0], start_x, y, page_n,
                                               width=subtitle_width * subtitle2_size,
                                               font="SimHei", size=subtitle2_size)
                        num_n2 = self.add_text(self.template[key][key2][1],
                                               start_x + (subtitle_width + 2) * subtitle2_size,
                                               y, page_n, width=content_width * content_size, font="SimSun",
                                               size=content_size)
                        y -= max(subtitle2_size * 1.2 * num_n1, content_size * 1.2 * num_n2) + content_size * 3
                        if y <= min_y:
                            y = start_y
                            page_n += 1
                            num_n1 = self.update_text(-1, self.template[key][key2][0], start_x, y, page_n,
                                                      width=subtitle_width * subtitle2_size,
                                                      font="SimHei", size=subtitle2_size)
                            num_n2 = self.update_text(-1, self.template[key][key2][1],
                                                      start_x + (subtitle_width + 2) * subtitle2_size,
                                                      y, page_n, width=content_width * content_size, font="SimSun",
                                                      size=content_size)
                            y -= max(subtitle2_size * 1.2 * num_n1, content_size * 1.2 * num_n2) + content_size * 3
                    elif key2[0] == '_' and type(self.template[key][key2]) == str:
                        num_n2 = self.add_text(self.template[key][key2],
                                               start_x + (subtitle_width + 2) * subtitle2_size,
                                               y, page_n, width=content_width * content_size, font="SimSun",
                                               size=content_size)
                        y -= content_size * 1.2 * num_n2 + content_size * 3
                        if y <= min_y:
                            y = start_y
                            page_n += 1
                            num_n2 = self.update_text(-1, self.template[key][key2],
                                                      start_x + (subtitle_width + 2) * subtitle2_size,
                                                      y, page_n, width=content_width * content_size, font="SimSun",
                                                      size=content_size)
                            y -= content_size * 1.2 * num_n2 + content_size * 3
                    else:
                        num_n1 = self.add_text(key2, start_x, y, page_n, width=subtitle_width * subtitle2_size,
                                               font="SimHei", size=subtitle2_size)
                        num_n2 = self.add_text(self.template[key][key2],
                                               start_x + (subtitle_width + 2) * subtitle2_size,
                                               y, page_n, width=content_width * content_size, font="SimSun",
                                               size=content_size)
                        y -= max(subtitle2_size * 1.2 * num_n1, content_size * 1.2 * num_n2) + content_size * 3
                        if y <= min_y:
                            y = start_y
                            page_n += 1
                            num_n1 = self.update_text(-2, key2, start_x, y, page_n,
                                                      width=subtitle_width * subtitle2_size,
                                                      font="SimHei", size=subtitle2_size)
                            num_n2 = self.update_text(-1, self.template[key][key2],
                                                      start_x + (subtitle_width + 2) * subtitle2_size,
                                                      y, page_n, width=content_width * content_size, font="SimSun",
                                                      size=content_size)
                            y -= max(subtitle2_size * 1.2 * num_n1, content_size * 1.2 * num_n2) + content_size * 3
                try:
                    if key[0] != '_':
                        self.template["目录"][key] = page_n
                except:
                    pass
                if y <= 2 * self.height / 3:
                    y = start_y
                    page_n += 1
        pass

    # 类似test函数，纯调试用， 但我想应该可以增加几个参数作为报告中可修改的部分（添加的文字/图片，待ocr的图片，估计出来的价格，委托人，房产名之类的），
    # 然后外面的接口只用调用这个函数就好了，但我不太清楚报告中那些是可变的，那些是不用变的，当然也可用默认值
    #目前设置的接口有（依顺序）：封面图片、logo图片、客户名、房产证编号、房产概况、报告编号、ocr生成的表格、
    #                      附录图片字典（目前仅支持只有图片）、城市名和城市介绍、周边环境介绍、交通环境介绍、房产估价，以及房产名称
    def model_report(self, cover_img=None, logo_img=None, client_name: str = "", property_index: str = "",
                     property_summary: str = "", report_index: str = "",
                     ocr_table: list = None, appendix: dict = None, city: tuple = ("", "", ""), environment: str = "",
                     traffic: str = "",
                     property_price: int = 0,
                     property_size: float = 0.0):
        self.set_cover(cover_img)
        value = {
            "敬启者：": f"%s" % client_name,
            "主旨：": f"%s（“评估物业”）" % self.property_name,
            "__前言": {
                "估值委托、用途及日期": f"我们根据委托人的指示，对上述位于中华人民共和国（中国）之该物业进行市场价值评估（详情请见随函附奉之估值报告）。我们证实曾实地勘查该物业，作出有关查询，并搜集我们认为必要之进一步资料，以便向委托人呈报我们对该物业于%s（估价时点）之市场价值意见，供 委托人作参考用途。" % cn2an.transform(
                    self.date, "an2cn"),
                "市场价值定义": "在评估该物业时，我们已符合英国皇家特许测量师学会颁布的英国皇家特许测量师学会物业估值准则（二〇二〇年版）所载的规定。我们对该物业以特殊假设条件为基准之估值乃该物业的市场价值，市场价值的定义为「自愿买方与自愿卖方各自在知情、审慎及无胁迫的情况下，对物业作出适当推销后，于估值日透过公平交易将物业转手的估计金额」。",
                "估值假设": "除特殊标明外，我们的估值并不包括因特别条款或情况（如非典型融资、售后租回安排、由任何与销售相关人士授出的特别考虑因素或特许权或任何特别价值因素）所抬高或贬低的估计价格。我们在评估该物业时，已假设有关物业权益之可转让土地使用权已按象征性土地使用年费批出，而任何应付之地价亦已全数缴清。就物业之业权状况，我们乃依赖由 贵公司所提供之意见。于估值而言，我们假设承让人对物业享有良好业权。我们亦已假设有关物业权益之承让人或使用人可于获批之土地使用年期尚未届满之整段期间，对有关物业享有自由及不受干预之使用权或转让权。我们之估值并无考虑该物业所欠负之任何抵押、按揭或债项，亦无考虑在出售物业权益时可能发生之任何开支或税项。除另有说明外，我们假定该物业概无附带可能影响其价值之他项权利、限制及繁重支销。",
                "评估方法": "我们采用比较法对该物业之现状价值进行评估。\n比较法，即经参考有关市场上可比之成交案例及价格得出评估物业之价值的方法。",
                "资料来源": "我们对该物业进行估值时，乃依赖产权方提供有关物业业权之法定文件副本，惟我们并无查阅文件正本以核实所有权或是否有任何修订并未见於我们所取得的副本。所有有关文件仅用作参考。\n我们在颇大程度上依赖产权方提供之资料并接纳向我们提供关于规划许可或法定通告、地役权、年期、占用情况、规划方案、土地识别、地块面积、规划建筑面积及所有其它相关事项之意见。\n载于本估值报告书内之尺寸、量度及面积均以提供予我们之文件所列载资料作基准，故仅为约数。我们并无理由怀疑产权方提供予我们之资料之真实性及准确性。我们并获知所有相关之重要事实已提供予我们，并无任何遗漏。",
                "业权查核": "我们曾获提供有关该物业业权之法定文档副本，惟我们并无进行查册以确认该物业之业权，或查核有否任何未有记载在该等交予我们之文档之修订条款。",
                "现场勘查": "我们曾勘察该物业之内、外部。然而，我们并未对地块进行勘测，以断定土地条件及设施等是否适合任何未来发展之用。我们的估值以此等各方面均令人满意及建筑期内将不会产生非经常费用及延误为基准。同时，我们也未进行详细的实地丈量以核实该物业之地块面积，我们乃假设该等提供予我们之资料所示之面积乃属正确。",
                "币值": "本报告除特殊标明外，所有货币单位为中华人民共和国法定货币单位：人民币。除非特殊标明外，我们评估该物业之100%权益。",
            },
            "评估物业": {
                "物业位置": f"评估物业位于%s" % self.property_name
            },
            "区域位置": {
                "__城市": city[0:2],
                "人口，面积及行政区划": city[2],
                "邻近环境及建筑物": environment,
                "交通条件": traffic,
            },
            "业权状况": {
                "__制度简介": ("中华人民共和国土地使用制度",
                               "根据《中华人民共和国宪法》(一九八八年修订案)第十条，中国建立了土地使用权与土地所有权两权分离制度。自此，有偿取得之有限年期之土地使用权均可在中国转让、赠予、出租、抵押。市级地方政府可通过拍卖、招标或挂牌三种方式将有限年期之土地使用权国有出让给国内及国外机构。一般情况下，土地使用权国有出让金将按一次性支付，土地使用者在支付全部土地使用权国有出让金后，可领取【国有土地使用证】。土地使用者同时需要支付其它配套公用设施费用、开发费及拆迁补偿费用予原居民。物业建成后，当地房地产管理部门将颁发【房屋所有权证】或【不动产权证】，以证明物业的房屋所有权。"),
                "相关权证": f"根据{property_index}，相关内容摘录如下：",
                "表格集": ocr_table,
            },
            "物业概况": {
                "__": property_summary,
            },
            "占用概况": {
                "__": "于估价时点，估价对象为空置状态"
            },
            "评估基准": {
                "评估物业": f"评估物业为{self.property_name}，总建筑面积为{property_size}平方米。",
                "估值假设及特殊假设": "我们的评估基于如下假设：\n(一) 评估物业可在剩余土地使用期限内自由转让，而无需向政府缴纳土地国有出让金及其他费用；\n(二) 评估物业的土地国有出让金、动拆迁及安置补偿费、市政配套费用已全部支付完毕；\n(三) 评估物业的规划设计符合当地城市规划要求且已获得相关部门批准；\n(四) 评估物业可以自由出售给任何买家;"
            },
            "估值结果": {
                "估值结果": f"综上所述，我们的意见认为，于估值日期%s，" % cn2an.transform(self.date,
                                                                                       "an2cn") + f"在估价假设和限制条件下，评估物业的现状下市场价值为人民币%d元" % property_price + f"(大写人民币%s)" % cn2an.an2cn(
                    f"%d" % property_price, "rmb"),
                "非出版物及注意事项": "如未得到本公司的书面许可，本估值报告书的全文或任何部份内容或任何注释，均不能以任何形式刊载于任何档、通函或声明。\n最后，根据本公司的一贯做法，我们必须申明，本估值报告书仅供委托方使用，本公司不承担对任何第三方对本报告书的全文或任何部份内容的任何责任。"
            },
            "__附录": appendix,
            "目录": {
                "评估物业": 0,
                "区域位置": 0,
                "业权状况": 0,
                "物业概况": 0,
                "占用概况": 0,
                "评估基准": 0,
                "估值结果": 0,
            },
        }
        for key in appendix.keys():
            value["目录"][key] = 0
        self.fill_template(value)
        self.template_to_l()
        self.set_up_down_label(logo_img, index=report_index)
        self.generate_pdf()

    def save_report(self, uid: int, record: Record):
        logo_img = "D:/sitp_work/web/report/logo_img.png"
        cover_img = record.field_img[0]
        client_name = "{}（委托人）".format(uid)  # TODO:数据库里根据uid查找用户名

        # TODO:后续处理
        property_summary = (
            f"估价对象位于「{record.house_location}」内，该社区于{record.house_year}年竣工。根据估价人员现场勘查及权利人提供之相关资料，"
            f"估价对象为{record.house_type}的户型。总建筑面积为{record.house_area}平方米。估价对象为{record.house_structure}。"
            f"于估价时点，估价对象为{record.house_decorating}。")
        # property_index = "【房地产权证】沪(2017)浦字不动产权第015342号"
        property_index = "【房地产权证】"
        print(record.production_ocr)
        ocr_table = OCR_Table().trans_to_df(record.production_ocr)
        apppendix = {
            "附录一": [record.map],
            "附录二": record.production_cert_img,
            "附录三": record.field_img
        }
        city_introduction, city_detail = MySQLManager().get_city_info(record.city)
        city = (record.city, city_introduction, city_detail)
        environment = "该区域内有绿城御园、仁恒森兰雅苑-东区、森兰名轩二期等高品质住宅区，周边配套设施齐全，包括多所知名学校如上海市浦东新区明珠森兰小学和进才森兰实验中学，以及便捷的医疗资源如浦东新区高行社区卫生服务中心。"

        traffic = "评估物业交通便利，周边路网干线丰富，公交和出租车均可到达。\n\n评估物业坐落图请见附录1"
        property_price = int(record.price * record.house_area)
        report_index = f"No.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.model_report(cover_img=cover_img, logo_img=logo_img, client_name=client_name,
                          property_summary=property_summary, property_index=property_index,
                          ocr_table=ocr_table, appendix=apppendix, city=city, environment=environment, traffic=traffic,
                          property_price=property_price, property_size=record.house_area, report_index=report_index)

# 示例使用
# if __name__ == "__main__":
#     filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_report.pdf"
#     file_path = f"../{REPORT_PATH}/{filename}"
#     u_id = 17
#     u_record = Record(u_id)
#     u_record.house_location = "兰谷路2777弄"
#     u_record.city = "上海"
#     u_record.house_area = 136.79
#     u_record.house_type = "2室1厅1厨2卫"
#     u_record.house_year = 2013
#     u_record.house_floor = "低楼层"
#     u_record.house_decorating = "简装"
#     u_record.green_rate = 0.3
#     u_record.price = 88268.3
#     u_record.map = "../static/maps/20250226143736.png"
#     u_record.production_cert_img = ["../static/uploads/20250227214853_cropped_image.png"]
#     u_record.production_ocr = "D:\sitp_work\web\static\ocr_tables\ocr_data_20250227_214856.xlsx"
#     u_record.field_img = ["../static/uploads/20250226143704_cropped_image.png","../static/uploads/20250226185033_cropped_image.png","../static/uploads/20250226185045_cropped_image.png"]
#
#     case = PDFReport(file_path, u_record.house_location)
#     case.save_report(u_id, u_record)
#     # if os.path.exists("../static/ocr_tables/ocr_data_20250227_213039.xlsx"):
#     #     print("文件存在")
