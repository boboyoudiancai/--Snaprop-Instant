from http import HTTPStatus
import dashscope
import pandas as pd


def QwenAnswer(Prompt: str, Request: str) -> str:
    message = [{'role': 'system', 'content': Prompt},
               {'role': 'user', 'content': Request}]
    reply = dashscope.Generation.call(
        model='qwen-max',
        api_key="sk-f21ceba42bc2482397f758ed3d198bfb",
        messages=message,
        result_format='text'
    )
    return reply.output.text



prompt_getinfo = (
    "你是一位房屋估价师，现在用户会告诉你他目标住宅的信息，"
    "请从众多信息中提取出下列列表中的可用信息："
    "{lists}"
    "数值转为数字，带有百分号的数值除以100转为小数形式（例如用户输入5%，你的返回值应该为0.05,请把它计算出来），house_year表示房屋建成年份,若用户没有提及，可以为空，只要保留数字就可以了，"
    "house_type表示房型，格式为*室*厅*卫，其中*表示数字，"
    "house_floor表示房屋楼层，有低楼层/中楼层/高楼层可选，"
    "house_decorating表示房屋装修情况，有精装/简装/毛坯可选"
    "已知之前已经获得的Python二维列表如下："
    "{history}"
    "请在历史信息的基础上修改补充"
    "请注意：返回的参数格式要求如下："
    "以Python二维列表的形式返回给我，参数名在前，数值在后。也只需要返回这些信息给我，多余的内容都不要。"
)

prompt_after_getinfo = (
    "你是一位房屋估价师，现在你已经从和用户的交流中得到了关于目标住宅的信息如下，"
    "{history}"
    "请根据下列列表补充目前已知的所有目标住宅的信息，"
    "{lists}"
    "其中house_location表示小区名称，house_area表示房屋面积，house_type表示房型，house_year表示房屋建成年份，house_floor表示楼层，house_decorating表示房屋装修情况"
    "请根据已经获得的目标住宅判断是否已经全部获取列表中的所有参数，"
    "若有不确定或缺失的元素都可以再次向用户提问确认；"
    "若已经获得全部参数，则以表格的形式清晰罗列所有信息给用户，等待用户确认。"
    "注意，你不需要透露列表中的参数名，那太官方，你只需要贴近口语的表达。"
)

inputs = [
    "house_location",
    "house_area",
    "house_type",
    "house_year",
    "house_floor",
    "house_decorating"
]


def get_info(user_input: str, history_info):
    prmp_get = prompt_getinfo.format(lists=",".join(inputs), history=history_info)
    print(prmp_get + "\n\n")
    info = QwenAnswer(Prompt=prmp_get, Request=user_input)
    print(info)
    prmp_response = prompt_after_getinfo.format(lists=",".join(inputs), history=info)
    print(prmp_response + "\n\n")
    response = QwenAnswer(Prompt=prmp_response, Request=info)
    return info, response


prompt_respond_plan = (
    "你是一位房屋估价师，现在用户会告诉你他目标住宅的产证信息，"
    "请从产证信息中提取出下列列表中的可用信息："
    "{lists}"
    "数值转为数字，带有百分号的数值除以100转为小数形式（例如用户输入5%，你的返回值应该为0.05,请把它计算出来），house_year表示房屋建成年份,只要保留数字就可以了，"
    "house_floor表示房屋楼层，请根据房屋所在楼层和该幢楼层总高度之比，小于0.33的是低楼层，介于0.33和0.66之间的是中楼层，高于0.66的是高楼层"
    "已知之前已经获得的Python二维列表如下："
    "{history}"
    "请在历史信息的基础上修改补充"
    "请注意：返回的参数格式要求如下："
    "以Python二维列表的形式返回给我，参数名在前，数值在后。也只需要返回这些信息给我，多余的内容都不要。"
)


def get_request_table(table_path,history_info):
    # 读取所有工作表
    sheets = pd.read_excel(table_path, sheet_name=None)
    user_input = ""
    # 显示每个工作表的数据
    for sheet_name, df in sheets.items():
        # print(f'Sheet: {sheet_name}')
        info = df.to_csv()
        # print(info)
        user_input += info
        # print(df.head())
    prmp = prompt_respond_plan.format(lists=",".join(inputs), history=history_info)
    print(prmp + "\n\n")
    info = QwenAnswer(Prompt=prmp, Request=user_input)
    prmp_response = prompt_after_getinfo.format(lists=",".join(inputs), history=info)
    print(prmp_response + "\n\n")
    response = QwenAnswer(Prompt=prmp_response, Request=info)
    return info, response

# if __name__ == "__main__":
#     get_request_table('static\ocr_tables\ocr_data_20250225_141913.xlsx',{})
