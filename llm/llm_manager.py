"""
本模块包含 通义千问管理 类
"""
import dashscope
from llm.prompt import Prompt
from config.qianwen_config import model_name, model_api_key


class QianwenManager():
    """
    通义千问管理 类
    """

    def __init__(self):
        self._model = model_name
        self._api_key = model_api_key

    def disconnect_llm(self):
        return

    def interact_qwen(self, prompt: str, request: str):
        message = [{'role': 'system', 'content': prompt},
                   {'role': 'user', 'content': request}]
        reply = dashscope.Generation.call(
            model=self._model,
            api_key=self._api_key,
            messages=message,
            result_format='text'
        )
        return reply.output.text

    def classify_message(self, message: str):
        return self.interact_qwen(prompt=Prompt.PROMPT_CLASSIFY_MESSAGE, request=message)

    def respond_null(self, message: str):
        return self.interact_qwen(prompt=Prompt.PROMPT_RESPOND_NULL, request=message)

    def respond_info(self, message: str, inputs: list[str]):
        prompt = Prompt.PROMPT_RESPOND_INFO.format(lists=",".join(inputs))
        return self.interact_qwen(prompt=prompt, request=message)

    def respond_value(self, missing_values: list[str]):
        prompt = Prompt.PROMPT_RESPOND_VALUE.format(lists=",".join(missing_values))
        return self.interact_qwen(prompt=prompt, request="")

    def respond_table(self, message: str, inputs: list[str]):
        prompt = Prompt.PROMPT_RESPOND_TABLE.format(lists=",".join(inputs))
        return self.interact_qwen(prompt=prompt, request=message)

    def get_near_loc(self, message: str):
        return self.interact_qwen(prompt=Prompt.PROMPT_NEAR_LOC, request=message)

    def get_environment(self, near_places: list[str], hospital: list[str], school: list[str]):
        prompt = Prompt.PROMPT_NEAR_LOC_SHORT.format(near_places=",".join(near_places), hospital=",".join(hospital),
                                                     school=",".join(school))
        return self.interact_qwen(prompt=prompt, request="")
