from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import aiohttp
import json

@register("urldb", "ctwj", "老九网盘资源系统的自动回复插件", "1.0.0")
class URLDBPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        if config is None:
            config = {}
        self.config = {
            "api_domain": config.get("api_domain", "https://pan.l9.lc"),
            "api_endpoint": config.get("api_path", "/api/public/resources/search"),
            "api_token": config.get("api_token", ""),  # 如果需要API密钥
            "timeout": config.get("timeout", 30),
            "max_results": config.get("max_results", 5)
        }

    @filter.regex(r"^帮我找.*")  
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
                
                logger.info(f"开始搜索，关键词: {search_query}")
                
                # 调用配置的API
                result = await self.call_api(search_query)
                yield event.plain_result(f"@{user_name} 找到了，\n{result}")
                
            except Exception as e:
                logger.error(f"调用API失败: {e}")
                yield event.plain_result(f"@{user_name} 抱歉，搜索时出现了错误，请稍后重试。")

    async def call_api(self, query: str) -> str:
        """调用配置的API"""
        url = f"{self.config['api_domain']}{self.config['api_endpoint']}"
        
        # 准备请求参数
        params = {
            "keyword": query,
            "page": 1,
            "page_size": self.config.get("max_results", 5)
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AstrBot-URLDB-Plugin/1.0"
        }
        
        # 只有在token不为空时才添加
        if self.config.get("api_token"):
            headers["X-API-Token"] = f"{self.config['api_token']}"
            logger.info(f"已添加API Token到请求头")
        else:
            logger.warning("API Token为空，未添加到请求头")
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.get("timeout", 30))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    logger.info(f"API响应状态码: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API响应数据: {data}")
                        return self.format_api_response(data)
                    else:
                        error_text = await response.text()
                        logger.error(f"API请求失败，状态码: {response.status}, 响应内容: {error_text}")
                        raise Exception(f"API请求失败，状态码: {response.status}, 响应: {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {e}")
            raise Exception(f"网络连接失败: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            raise Exception(f"API返回的数据格式错误: {e}")
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise e

    def format_api_response(self, data: dict) -> str:
        """格式化API响应数据"""
        try:
            logger.info(f"开始格式化API响应: {data}")
            logger.info(f"API响应数据类型: {type(data)}")
            logger.info(f"API响应数据键: {list(data.keys()) if isinstance(data, dict) else '不是字典'}")
            
            # 根据实际API响应格式进行解析
            if data.get("success") and data.get("data", {}).get("list"):
                resources = data["data"]["list"]
                total = data["data"].get("total", 0)
                formatted = []
                
                for i, resource in enumerate(resources[:self.config.get("max_results", 5)], 1):
                    title = resource.get("title", "无标题")
                    url = resource.get("url", "")
                    
                    formatted.append(f"{i}. {title}\n   🔗 {url}")
                
                result = "\n\n".join(formatted)
                if total > len(resources):
                    result += f"\n\n📊 共找到 {total} 个结果，显示前 {len(resources)} 个"
                
                return result
            else:
                # 如果不符合预期格式，显示错误信息
                logger.warning(f"API响应格式不符合预期: {data}")
                message = data.get("message", "没有找到相关结果")
                return f"搜索结果: {message}"
        except Exception as e:
            logger.error(f"格式化API响应失败: {e}")
            return f"API返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}"

    @filter.command("urldb_test")
    async def test_api(self, event: AstrMessageEvent):
        """测试API连接"""
        user_name = event.get_sender_name()
        
        try:
            logger.info("开始测试API连接...")
            result = await self.call_api("test")
            yield event.plain_result(f"@{user_name} API测试成功！\n{result}")
        except Exception as e:
            logger.error(f"API测试失败: {e}")
            yield event.plain_result(f"@{user_name} API测试失败: {e}")

    @filter.command("urldb_show_config")
    async def show_config(self, event: AstrMessageEvent):
        """显示当前配置"""
        user_name = event.get_sender_name()
        
        config_info = f"""@{user_name} 当前配置：
- API域名: {self.config.get('api_domain', '未设置')}
- API端点: {self.config.get('api_endpoint', '未设置')}
- API Token: {'已设置' if self.config.get('api_token') else '未设置'}
- 超时时间: {self.config.get('timeout', 30)}秒
- 最大结果数: {self.config.get('max_results', 5)}"""
        
        yield event.plain_result(config_info)

    async def terminate(self):
        """插件销毁时的清理工作"""
        logger.info("URLDB插件已卸载")
