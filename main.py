from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import json

@register("urldb", "YourName", "一个可以配置域名并调用API的插件", "1.0.0")
class URLDBPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 默认配置，可以通过配置文件覆盖
        self.config = {
            "api_domain": "https://api.example.com",
            "api_endpoint": "/search",
            "api_key": ""  # 如果需要API密钥
        }

    async def initialize(self):
        """插件初始化时加载配置"""
        try:
            # 尝试从配置文件加载配置
            config = await self.context.get_config()
            if config:
                self.config.update(config)
            logger.info(f"URLDB插件初始化完成，配置域名: {self.config['api_domain']}")
        except Exception as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")

    @filter.regex(^(搜|全网搜))
    async def handle_at_message(self, event: AstrMessageEvent):
        """处理@机器人的消息"""
        message_str = event.message_str.strip()
        user_name = event.get_sender_name()
        
        # 检查消息是否包含"帮我找"
        if "帮我找" in message_str:
            try:
                # 提取搜索关键词（去掉"帮我找"）
                search_query = message_str.replace("帮我找", "").strip()
                if not search_query:
                    yield event.plain_result(f"@{user_name} 请告诉我你要找什么？")
                    return
                
                # 调用配置的API
                result = await self.call_api(search_query)
                yield event.plain_result(f"@{user_name} 搜索结果：\n{result}")
                
            except Exception as e:
                logger.error(f"调用API失败: {e}")
                yield event.plain_result(f"@{user_name} 抱歉，搜索时出现了错误，请稍后重试。")

    async def call_api(self, query: str) -> str:
        """调用配置的API"""
        url = f"{self.config['api_domain']}{self.config['api_endpoint']}"
        
        # 准备请求参数
        params = {
            "query": query,
            "limit": 5  # 限制返回结果数量
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AstrBot-URLDB-Plugin/1.0"
        }
        
        # 如果有API密钥，添加到请求头
        if self.config.get("api_key"):
            headers["Authorization"] = f"Bearer {self.config['api_key']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_api_response(data)
                else:
                    raise Exception(f"API请求失败，状态码: {response.status}")

    def format_api_response(self, data: dict) -> str:
        """格式化API响应数据"""
        try:
            # 这里需要根据实际API的响应格式来调整
            # 假设API返回的是包含results字段的JSON
            if "results" in data and data["results"]:
                results = data["results"]
                formatted = []
                for i, result in enumerate(results[:5], 1):  # 最多显示5个结果
                    title = result.get("title", "无标题")
                    url = result.get("url", "")
                    description = result.get("description", "无描述")
                    formatted.append(f"{i}. {title}\n   {url}\n   {description}")
                return "\n\n".join(formatted)
            else:
                return "没有找到相关结果"
        except Exception as e:
            logger.error(f"格式化API响应失败: {e}")
            return f"API返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}"

    @filter.command("urldb_config")
    async def config_command(self, event: AstrMessageEvent):
        """配置命令，用于设置API域名"""
        message_str = event.message_str.strip()
        user_name = event.get_sender_name()
        
        if not message_str:
            yield event.plain_result(f"@{user_name} 当前配置的API域名: {self.config['api_domain']}\n使用方法: /urldb_config <域名>")
            return
        
        # 更新配置
        self.config["api_domain"] = message_str
        try:
            # 保存配置到文件
            await self.context.set_config(self.config)
            yield event.plain_result(f"@{user_name} 配置已更新，API域名设置为: {message_str}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            yield event.plain_result(f"@{user_name} 配置更新失败: {e}")

    async def terminate(self):
        """插件销毁时的清理工作"""
        logger.info("URLDB插件已卸载")
