import asyncio
import threading
import time

from pydantic import Field
from pydantic.dataclasses import dataclass

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext
from astrbot.core.config.astrbot_config import AstrBotConfig

global_config : AstrBotConfig = Field(default_factory=AstrBotConfig)

# 全局的获取图片方法
async def get_image(self, event: AstrMessageEvent, imageId: int = 0, imageType: str = "SFW", imageIsAllowAiType: str = "ALL"):
    """获取图片"""
    if imageId != 0:
            try:
                image = f"https://kafuumiaki.top/api/Image/images/{imageId}"
                return image
            except Exception as e:
                logger.error(f"Error occurred while fetching image: {e}")
                error = Comp.Plain(f"Error occurred while fetching image with ID {imageId}.")
                return error

    imageTypeParam = imageType.upper()
    if not global_config.get("enable_nsfw") and (imageTypeParam == "NSFW" or imageTypeParam == "ALL"):
        logger.info(f"NSFW image request blocked. imageType: {imageTypeParam}")
        error = Comp.Plain("NSFW 图片功能已被禁用，请联系管理员启用。")
        return error

    imageIsAllowAiTypeParam = imageIsAllowAiType
    if not global_config.get("enable_aigc") and (imageIsAllowAiTypeParam == "AiOnly" or imageIsAllowAiTypeParam == "ALL"):
        logger.info(f"AI image request blocked. imageIsAllowAiType: {imageIsAllowAiTypeParam}")
        error = Comp.Plain("AI 图片功能已被禁用，请联系管理员启用。")
        return error

    logger.info(f"Request parameters: imageId: {imageId}, imageType: {imageTypeParam}, imageIsAllowAiType: {imageIsAllowAiTypeParam}")

    try:
        image = f"https://kafuumiaki.top/api/Image/random/images?type={imageTypeParam}&isAllowAiGenerated={imageIsAllowAiTypeParam}"
        return image
    except Exception as e:
        logger.error(f"Error occurred while fetching random image: {e}")
        error = Comp.Plain("Error occurred while fetching random image.")

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
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        result = await get_image(self, event, imageType=imageType, imageIsAllowAiType=imageIsAllowAiType)
        if type(result) is str:
            chain.append(Comp.Image.fromURL(result))
        else:
            chain.append(result)
        return event.chain_result(chain)

# 获取指定图片的Tool
@dataclass
class GetSpecificImageTool(FunctionTool[AstrAgentContext]):
    name: str = "get_specific_image"  # 工具名称
    description: str = "A tool to get a specific image by image id."  # 工具描述
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "imageId": {
                    "type": "string",
                    "description": "Id of image to search for.",
                },
            },
            "required": ["imageId"],
        }
    )

    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        imageId = kwargs.get("imageId", 0)
        event = context.context.event
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        result = await get_image(self, event, imageId=imageId)
        if type(result) is str:
            chain.append(Comp.Image.fromURL(result))
        else:
            chain.append(result)
        return event.chain_result(chain)



@register("random_image", "KafuuMiaki", "提供从指定源获取随机一张图片或指定图片功能的 AstrBot 插件", "1.0.9")
class ImagePlugin(Star):
    enable_scheduled_sending_random_image = False
    scheduled_sending_random_image_interval = 24
    scheduled_sending_random_image_thread = None
    replace_map = {
        ord("o"): "AiOnly",
        ord("a"): "ALL",
        ord("n"): "NotAllowAi"
    }

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        global global_config
        global_config = self.config
        self.context.add_llm_tools(GetRandomImageTool()) #添加Tool
        if self.config.get("enable_specific_image"):
            self.context.add_llm_tools(GetSpecificImageTool())
        scheduled_config = global_config.get("scheduled_sending_random_image", {})
        self.enable_scheduled_sending_random_image = scheduled_config.get(
            "enable_scheduled_sending_random_image", False
        )
        self.scheduled_sending_random_image_interval = scheduled_config.get(
            "scheduled_time", 24
        )
        # 最低间隔 1 小时，不足 1 小时按 1 小时处理。
        if self.scheduled_sending_random_image_interval < 1:
            self.scheduled_sending_random_image_interval = 1
        if self.enable_scheduled_sending_random_image:
            logger.info("启动定时发送线程")
            self.scheduled_sending_random_image_thread = threading.Thread(
                target=self.scheduled_send_random_image,
                args=(None,),
                daemon=True,
            )
            self.scheduled_sending_random_image_thread.start()
            logger.info(
                f"定时线程: {self.scheduled_sending_random_image_thread.is_alive()}"
            )
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""


    # 注册指令的装饰器。指令名为 random_image。注册成功后，发送 `/random_image` 就会触发这个指令，并回复图片
    @filter.command("random_image", alias={"随机图片","sjtp"})
    async def random_image(self, event: AstrMessageEvent, imageType: str = "SFW", imageIsAllowAiType: str = "ALL"):
        """这是一个 random_image 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        event.get_sender_name()
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        imageTypeParam = imageType

        imageIsAllowAiTypeParam = imageIsAllowAiType.lower().translate(self.replace_map)
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        result = await get_image(self, event, imageType=imageTypeParam, imageIsAllowAiType=imageIsAllowAiTypeParam)
        if type(result) is str:
            chain.append(Comp.Image.fromURL(result))
        else:
            chain.append(result)
        yield event.chain_result(chain) # 返回消息链

    # 注册指令的装饰器。指令名为 spec_image。注册成功后，发送 `/spec_image` 就会触发这个指令，并回复图片
    @filter.command("spec_image", alias={"指定图片","zdtp"})
    async def spec_image(self, event: AstrMessageEvent, id: int):
        """这是一个 spec_image 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        event.get_sender_name()
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        if not self.config.get("enable_specific_image"):
            yield event.chain_result([Comp.Plain("指定图片功能已被禁用，请联系管理员启用。")])
            return

        logger.info(f"Request parameters: id: {id}")
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        result = await get_image(self, event, imageId=id)
        if type(result) is str:
            chain.append(Comp.Image.fromURL(result))
        else:
            chain.append(result)
        yield event.chain_result(chain) # 返回消息链

    def scheduled_send_random_image(self, event: AstrMessageEvent):
        """定时循环：按设定的时间间隔向白名单会话发送随机图片。

        该函数在后台守护线程中运行，每次发送之间等待设定的小时数。
        时间间隔最低为 1 小时，不足 1 小时按 1 小时处理。

        Args:
            event: 消息事件，仅透传给 get_image; 循环本身通过白名单会话发送。
        """
        while self.enable_scheduled_sending_random_image:
            interval = self.scheduled_sending_random_image_interval
            # 最低间隔 1 小时，不足 1 小时按 1 小时处理。
            if interval < 1:
                interval = 1
            time.sleep(interval * 3600)
            if not self.enable_scheduled_sending_random_image:
                break

            try:
                scheduled_config = global_config.get(
                    "scheduled_sending_random_image", {}
                )
                whitelist = scheduled_config.get("shceduled_whitelist", [])
                if not whitelist:
                    logger.warning("定时发送白名单为空，跳过本次发送")
                    continue

                image_type = scheduled_config.get("scheduled_image_type", "SFW")
                allow_aigc = scheduled_config.get("scheduled_image_aigc", "n")
                allow_aigc = self.replace_map[ord(allow_aigc[-1])]
                pre_words = scheduled_config.get("scheduled_text", "")

                result = asyncio.run(
                    get_image(
                        self,
                        event,
                        imageType=image_type,
                        imageIsAllowAiType=allow_aigc,
                    )
                )
                chain = MessageChain()
                if pre_words:
                    chain.message(pre_words)
                if isinstance(result, str):
                    chain.url_image(result)
                else:
                    chain.message("发送定时图片失败")

                for session in whitelist:
                    try:
                        sent = asyncio.run(
                            self.context.send_message(session, chain)
                        )
                        if sent:
                            logger.info(f"成功发送定时图片到 {session}")
                        else:
                            logger.error(f"未找到会话 {session} 对应的平台, 发送失败")
                    except Exception as e:
                        logger.error(f"发送定时图片到 {session} 失败: {e}")
            except Exception as e:
                logger.error(f"本轮定时发送失败: {e}")
        logger.info("退出定时循环")


    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self.enable_scheduled_sending_random_image = False
        thread = self.scheduled_sending_random_image_thread
        if thread is None or not thread.is_alive():
            return
        try:
            await asyncio.wait_for(asyncio.to_thread(thread.join), timeout=5)
        except Exception as e:
            logger.error(f"定时线程未能按时关闭, 将忽略. {e}")

