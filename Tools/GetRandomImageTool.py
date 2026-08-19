from pydantic import Field
from pydantic.dataclasses import dataclass

import astrbot.api.message_components as Comp
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext


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
                },
                "imageIsAllowAiType": {
                    "type": "string",
                    "description": "Whether to allow AI-generated images.",
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

        chain = [
            Comp.Image.fromURL(f"https://kafuumiaki.top/api/Image/random/images?type={imageType}&isAllowAiGenerated={imageIsAllowAiType}"),
        ]
        return chain
