# URLDB Plugin for AstrBot

一个可以配置域名并调用API的AstrBot插件，支持被@时搜索功能。

## 功能特性

- 🔧 **可配置API域名**：支持自定义API服务地址
- 📝 **@机器人搜索**：被@时检测"帮我找"关键词并调用API
- ⚙️ **灵活配置**：支持API密钥、超时时间等配置
- 📊 **结果格式化**：自动格式化API返回的搜索结果

## 安装依赖

```bash
pip install aiohttp
```

## 配置说明

### 1. 配置文件方式

创建 `config.yaml` 文件：

```yaml
# API域名配置
api_domain: "https://your-api-domain.com"
api_endpoint: "/search"
api_key: "your-api-key-if-needed"
timeout: 30
max_results: 5
```

### 2. 命令配置方式

使用 `/urldb_config` 命令动态配置：

```
/urldb_config https://your-api-domain.com
```

## 使用方法

### 搜索功能

在群聊中@机器人并包含"帮我找"关键词：

```
@机器人 帮我找Python教程
@机器人 帮我找机器学习资料
```

### 配置命令

- 查看当前配置：`/urldb_config`
- 设置API域名：`/urldb_config https://your-api.com`

## API接口要求

插件期望的API响应格式：

```json
{
  "results": [
    {
      "title": "搜索结果标题",
      "url": "https://example.com",
      "description": "搜索结果描述"
    }
  ]
}
```

## 自定义API格式

如果你的API返回格式不同，可以修改 `format_api_response` 方法来适配你的API响应格式。

## 错误处理

- API请求失败时会返回友好的错误提示
- 网络超时和连接错误都有相应的处理
- 所有错误都会记录到日志中便于调试

## 许可证

MIT License
