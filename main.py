from pydantic import Field
from pydantic.dataclasses import dataclass

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


# 获取随机图片的Tool
@dataclass
class GetRandomImageTool(FunctionTool[AstrAgentContext]):
    name: str = "get_random_image"  # 工具名称
    description: str = "A tool to get a random image."  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "imageType": {
                    "type": "string",
                    "description": "Type of image to search for.",
                    "enum": ["SFW", "NSFW", "ALL"],
                },
                "imageIsAllowAiType": {
                    "type": "string",
                    "description": "Whether to allow AI-generated images.",
                    "enum": ["AiOnly", "ALL", "NotAllowAi"]
                },
            },
            "required": ["imageType", "imageIsAllowAiType"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        imageType = kwargs.get("imageType", "SFW")
        imageIsAllowAiType = kwargs.get("imageIsAllowAiType", "ALL")
        event = context.context.event
        logger.info(f"Request parameters: imageType: {imageType}, imageIsAllowAiType: {imageIsAllowAiType}")

        return event.image_result(f"https://kafuumiaki.top/api/Image/random/images?type={imageType}&isAllowAiGenerated={imageIsAllowAiType}")



@register("random_image", "KafuuMiaki", "提供从指定源获取随机一张图片或指定图片功能的 AstrBot 插件", "1.0.3")
class ImagePlugin(Star):
    replace_map = {
        ord("o"): "AiOnly",
        ord("a"): "ALL",
        ord("n"): "NotAllowAi"
    }

    def __init__(self, context: Context):
        super().__init__(context)
        self.context.add_llm_tools(GetRandomImageTool()) #添加Tool


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""


    # 注册指令的装饰器。指令名为 random_image。注册成功后，发送 `/random_image` 就会触发这个指令，并回复图片
    @filter.command("random_image", alias={"随机图片","sjtp"})
    async def random_image(self, event: AstrMessageEvent, imageType: str = "SFW", imageIsAllowAiType: str = "ALL"):
        """这是一个 random_image 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        event.get_sender_name()
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        imageIsAllowAiTypeParam = imageIsAllowAiType.lower().translate(self.replace_map)
        logger.info(f"Request parameters: imageType: {imageType}, imageIsAllowAiType: {imageIsAllowAiType}")
        chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Image.fromURL(f"https://kafuumiaki.top/api/Image/random/images?type={imageType}&isAllowAiGenerated={imageIsAllowAiTypeParam}"),
        ]
        yield event.chain_result(chain) # 返回消息链

    # 注册指令的装饰器。指令名为 spec_image。注册成功后，发送 `/spec_image` 就会触发这个指令，并回复图片
    @filter.command("spec_image", alias={"指定图片","zdtp"})
    async def spec_image(self, event: AstrMessageEvent, id: int):
        """这是一个 spec_image 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        event.get_sender_name()
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        logger.info(f"Request parameters: id: {id}")
        chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Image.fromURL(f"https://kafuumiaki.top/api/Image/images/{id}"),
        ]
        yield event.chain_result(chain) # 返回消息链

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
