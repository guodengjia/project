# 通用 TCP 服务端与客户端

这是一个用 Python 编写的通用 TCP 服务端和客户端实现，支持多客户端并发连接、JSON 消息格式以及交互式命令行界面。

## 特性

### 服务端特性
- ✅ 支持多客户端并发连接（使用多线程）
- ✅ 自动处理客户端连接和断开
- ✅ 支持 JSON 和纯文本消息格式
- ✅ 内置 ping/pong 和 echo 消息类型
- ✅ 完整的日志记录
- ✅ 可配置的监听地址、端口和最大连接数
- ✅ 优雅的关闭和资源清理

### 客户端特性
- ✅ 自动重连机制
- ✅ 异步消息接收（独立线程）
- ✅ 交互式命令行界面
- ✅ 支持 JSON 和纯文本消息
- ✅ 内置常用命令（ping、echo、send、json）
- ✅ 完整的日志记录
- ✅ 可配置的连接超时

## 文件说明

- `tcp_server.py` - TCP 服务端实现
- `tcp_client.py` - TCP 客户端实现
- `README.md` - 项目说明文档

## 环境要求

- Python 3.6 或更高版本
- 无需额外依赖，仅使用 Python 标准库

## 快速开始

### 1. 启动服务端

```bash
python tcp_server.py
```

服务端将在 `0.0.0.0:8888` 上监听连接。

**自定义配置：**

编辑 `tcp_server.py` 的 `main()` 函数：

```python
server = TCPServer(
    host='0.0.0.0',      # 监听地址
    port=8888,           # 监听端口
    max_connections=10   # 最大连接数
)
```

### 2. 启动客户端

在新的终端窗口中：

```bash
python tcp_client.py
```

客户端将连接到 `localhost:8888`。

**自定义配置：**

编辑 `tcp_client.py` 的 `main()` 函数：

```python
client = TCPClient(
    host='localhost',  # 服务端地址
    port=8888,         # 服务端端口
    timeout=10         # 连接超时（秒）
)
```

## 使用示例

### 客户端交互命令

连接成功后，客户端将进入交互模式，支持以下命令：

#### 1. ping - 测试连接
```
>>> ping
```
发送 ping 请求，服务端将返回 pong 响应。

#### 2. echo - 回显消息
```
>>> echo 你好世界
```
服务端将回显您发送的消息。

#### 3. send - 发送纯文本消息
```
>>> send 这是一条测试消息
```
发送纯文本消息给服务端。

#### 4. json - 发送 JSON 消息
```
>>> json {"type": "custom", "data": "some data"}
```
发送自定义 JSON 格式消息。

#### 5. quit/exit - 退出
```
>>> quit
```
断开连接并退出客户端。

## 编程接口

### 服务端 API

```python
from tcp_server import TCPServer

# 创建服务端实例
server = TCPServer(host='0.0.0.0', port=8888, max_connections=10)

# 启动服务端
server.start()

# 获取已连接的客户端列表
clients = server.get_connected_clients()

# 停止服务端
server.stop()
```

### 客户端 API

```python
from tcp_client import TCPClient

# 创建客户端实例
client = TCPClient(host='localhost', port=8888, timeout=10)

# 连接到服务端
if client.connect():
    # 发送纯文本消息
    client.send_message("Hello Server")
    
    # 发送 JSON 消息
    client.send_json({
        'type': 'custom',
        'message': 'Hello'
    })
    
    # 发送 ping
    client.ping()
    
    # 发送 echo
    client.echo("测试回显")
    
    # 检查连接状态
    if client.is_alive():
        print("连接正常")
    
    # 断开连接
    client.disconnect()
```

## 消息格式

### 标准 JSON 消息格式

服务端和客户端默认使用 JSON 格式进行通信：

```json
{
    "type": "message_type",
    "message": "消息内容",
    "server_time": "2025-11-06T12:00:00"
}
```

### 内置消息类型

1. **welcome** - 欢迎消息（服务端发送）
```json
{
    "type": "welcome",
    "message": "欢迎连接到 TCP 服务端",
    "server_time": "2025-11-06T12:00:00"
}
```

2. **ping/pong** - 连接测试
```json
// 客户端发送
{"type": "ping"}

// 服务端响应
{
    "type": "pong",
    "message": "服务端在线",
    "server_time": "2025-11-06T12:00:00"
}
```

3. **echo** - 消息回显
```json
// 客户端发送
{
    "type": "echo",
    "message": "要回显的内容"
}

// 服务端响应
{
    "type": "echo_response",
    "original_message": "要回显的内容",
    "server_time": "2025-11-06T12:00:00"
}
```

4. **error** - 错误消息
```json
{
    "type": "error",
    "message": "错误描述"
}
```

## 自定义扩展

### 扩展服务端消息处理

修改 `tcp_server.py` 中的 `_process_message()` 方法：

```python
def _process_message(self, message: str, client_address: tuple) -> dict:
    try:
        msg_data = json.loads(message)
        msg_type = msg_data.get('type', 'unknown')
        
        # 添加自定义消息类型处理
        if msg_type == 'my_custom_type':
            # 自定义处理逻辑
            return {
                'type': 'my_custom_response',
                'data': 'processed data'
            }
        # ... 其他类型处理
    except json.JSONDecodeError:
        # 处理非 JSON 消息
        pass
```

### 扩展客户端消息处理

修改 `tcp_client.py` 中的 `_handle_message()` 方法：

```python
def _handle_message(self, message: str):
    try:
        msg_data = json.loads(message)
        msg_type = msg_data.get('type', 'unknown')
        
        # 添加自定义消息类型处理
        if msg_type == 'my_custom_response':
            # 自定义处理逻辑
            logger.info(f"[自定义] {msg_data.get('data')}")
        # ... 其他类型处理
    except json.JSONDecodeError:
        pass
```

## 常见问题

### 1. 服务端启动失败：Address already in use

**原因：** 端口被占用

**解决方案：**
- 更改端口号
- 或者找到占用端口的进程并关闭：
  ```bash
  # Linux/Mac
  lsof -i :8888
  kill -9 <PID>
  
  # Windows
  netstat -ano | findstr :8888
  taskkill /PID <PID> /F
  ```

### 2. 客户端无法连接

**可能原因：**
- 服务端未启动
- 防火墙阻止连接
- 主机地址或端口配置错误

**解决方案：**
- 确认服务端已启动
- 检查防火墙设置
- 验证主机地址和端口配置

### 3. 消息乱码

**原因：** 字符编码问题

**解决方案：**
- 确保使用 UTF-8 编码
- 代码中已默认使用 UTF-8，一般不会出现此问题

## 安全注意事项

⚠️ **重要提示：** 这是一个基础的 TCP 实现，适用于学习和开发环境。在生产环境中使用时，请考虑：

1. **身份验证：** 添加客户端认证机制
2. **加密：** 使用 SSL/TLS 加密通信
3. **输入验证：** 验证和清理所有输入数据
4. **速率限制：** 防止 DoS 攻击
5. **日志安全：** 避免记录敏感信息
6. **异常处理：** 增强错误处理和恢复机制

## 性能优化建议

1. **使用连接池：** 对于高并发场景，考虑使用连接池
2. **异步 I/O：** 对于大量连接，考虑使用 `asyncio` 重写
3. **消息队列：** 使用消息队列处理高负载
4. **负载均衡：** 部署多个服务端实例

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，欢迎联系。