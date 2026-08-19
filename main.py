from Tools.GetRandomImageTool import GetRandomImageTool

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star, register


@register("random_image", "KafuuMiaki", "提供从指定源获取随机一张图片或指定图片功能的 AstrBot 插件", "1.0.2")
class ImagePlugin(Star):
    replace_map = {
        ord("o"): "AiOnly",
        ord("a"): "ALL",
        ord("n"): "NotAllowAi"
    }
    def __init__(self, context: Context):
        super().__init__(context)
        self.context.add_llm_tools(GetRandomImageTool())


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
