from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

@register("random_image", "KafuuMiaki", "提供获取随机一张图片功能的 AstrBot 插件", "1.0.0")
class ImagePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 random_image。注册成功后，发送 `/random_image` 就会触发这个指令，并回复图片
    @filter.command("random_image", alias={"随机图片","sjtp"})
    async def random_image(self, event: AstrMessageEvent, imageType: str = "SFW", imageIsAllowAiType: str = "ALL"):
        """这是一个 random_image 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        event.get_sender_name()
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        logger.info(f"Request parameters: imageType: {imageType}, imageIsAllowAiType: {imageIsAllowAiType}")
        chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Image.fromURL(f"https://kafuumiaki.top/api/Image/astrbot/get_image?type={imageType}&isAllowAiGenerated={imageIsAllowAiType}"),
        ]
        yield event.chain_result(chain) # 返回消息链

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
