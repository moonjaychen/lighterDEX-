# Lighter交易所客户端

一个完整的Lighter交易所客户端实现，支持REST API、WebSocket和交易功能。

## 功能特性

- ✅ **REST API集成**: 完整的REST API客户端
- ✅ **WebSocket实时数据**: 支持订单簿、账户、ticker等实时订阅
- ✅ **精度管理**: 自动从交易所获取精度信息并转换
- ✅ **配置管理**: 通过环境变量或配置文件管理
- ✅ **错误处理**: 统一的错误处理和重试机制
- ✅ **模块化设计**: 易于扩展和维护
- ⚠️ **交易功能**: 需要有效私钥和签名库

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd lighter_client
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装Lighter SDK

```bash
# 安装lighter-python SDK
cd ../lighter-python
pip install -e .
```

## 配置

### 环境变量配置

复制示例配置文件：

```bash
cp .env.example .env
```

编辑`.env`文件：

```env
# Lighter交易所配置
# 网络选择：mainnet 或 testnet
LIGHTER_NETWORK=mainnet

# 主网配置
LIGHTER_MAINNET_URL=https://mainnet.zklighter.elliot.ai
LIGHTER_MAINNET_WS_URL=wss://mainnet.zklighter.elliot.ai/stream

# 测试网配置
LIGHTER_TESTNET_URL=https://testnet.zklighter.elliot.ai
LIGHTER_TESTNET_WS_URL=wss://testnet.zklighter.elliot.ai/stream

# 账户配置
# 账户索引（从0开始）
LIGHTER_ACCOUNT_INDEX=0

# API密钥索引（从0开始）
LIGHTER_API_KEY_INDEX=0

# 私钥（不带0x前缀）
LIGHTER_PRIVATE_KEY=your_private_key_here

# 交易对配置
LIGHTER_SYMBOL=ETH-USDT

# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### 配置说明

- **LIGHTER_NETWORK**: 选择网络环境（mainnet/testnet）
- **LIGHTER_PRIVATE_KEY**: 账户私钥，用于签名交易（不带0x前缀）
  - 支持40字符、64字符和80字符格式
  - 80字符私钥会自动处理
- **LIGHTER_SYMBOL**: 默认交易对符号
- **LIGHTER_ACCOUNT_INDEX**: 账户索引，从0开始
- **LIGHTER_API_KEY_INDEX**: API密钥索引，从0开始

## 快速开始

### 基本使用

```python
import asyncio
from src.lighter_client import LighterClient
from src.config import LighterConfig

async def main():
    # 1. 创建配置
    config = LighterConfig()
    
    # 2. 创建客户端
    client = LighterClient(config)
    
    # 3. 初始化客户端
    await client.initialize()
    
    # 4. 获取市场信息
    market_info = await client.get_market_info()
    print(f"市场信息: {market_info}")
    
    # 5. 获取订单簿
    order_book = await client.get_order_book(depth=5)
    print(f"订单簿: {order_book}")
    
    # 6. 关闭客户端
    await client.close()

asyncio.run(main())
```

### 运行演示

```bash
python demo.py
```

### 运行测试

```bash
python test_basic.py
```

## 模块结构

```
lighter_client/
├── src/
│   ├── __init__.py              # 模块导出
│   ├── config.py               # 配置管理
│   ├── lighter_client.py       # 主客户端
│   ├── precision_manager.py    # 精度管理
│   └── websocket_client.py     # WebSocket客户端
├── examples/
│   └── basic_usage.py          # 使用示例
├── .env.example                # 环境变量示例
├── .env.test                   # 测试配置
├── requirements.txt            # 依赖列表
├── test_basic.py              # 基本测试
├── demo.py                    # 演示脚本
└── README.md                  # 本文档
```

## API参考

### LighterClient类

#### 初始化

```python
client = LighterClient(config=None)
```

- `config`: 可选，LighterConfig实例

#### 主要方法

```python
# 初始化客户端
await client.initialize()

# 获取市场信息
market_info = await client.get_market_info(symbol="ETH-USDT")

# 获取订单簿
order_book = await client.get_order_book(symbol="ETH-USDT", depth=10)

# 获取账户余额
balances = await client.get_account_balance()

# 订阅订单簿更新
await client.subscribe_order_book("ETH-USDT", callback_function)

# 订阅账户更新
await client.subscribe_account(callback_function)

# 创建订单（需要签名客户端）
order_result = await client.create_order(
    symbol="ETH-USDT",
    side="buy",
    order_type="limit",
    quantity=0.1,
    price=3000.0
)

# 关闭客户端
await client.close()
```

### 配置类

```python
from src.config import LighterConfig, get_config

# 从环境变量加载配置
config = LighterConfig()

# 或从指定文件加载
config = LighterConfig(env_file=".env.custom")

# 获取默认配置
config = get_config()
```

## 精度管理

客户端自动从交易所获取精度信息，并提供精度转换功能：

```python
# 格式化价格到正确精度
formatted_price = client.precision_manager.format_price(3002.755, "ETH-USDT")
# 结果: "3002.76"

# 格式化数量到正确精度
formatted_quantity = client.precision_manager.format_quantity(0.123456, "ETH-USDT")
# 结果: "0.1235"

# 调整价格到tick size倍数
adjusted_price = client.precision_manager.adjust_to_tick_size(3002.755, "ETH-USDT")
```

## WebSocket订阅

支持多种实时数据订阅：

```python
async def order_book_callback(data):
    """订单簿更新回调"""
    print(f"订单簿更新: {data}")

async def account_callback(data):
    """账户更新回调"""
    print(f"账户更新: {data}")

# 订阅订单簿
await client.subscribe_order_book("ETH-USDT", order_book_callback)

# 订阅账户
await client.subscribe_account(account_callback)
```

## 错误处理

客户端提供统一的错误处理：

```python
from src.lighter_client import LighterClientError

try:
    client = LighterClient()
    await client.initialize()
except LighterClientError as e:
    print(f"客户端错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 注意事项

1. **私钥安全**: 私钥应妥善保管，不要提交到版本控制系统
2. **网络连接**: 确保网络可以访问Lighter交易所API
3. **精度转换**: 交易前务必使用精度管理器格式化价格和数量
4. **WebSocket重连**: 客户端自动处理WebSocket断开重连
5. **交易功能**: 需要安装签名库和有效私钥

## 故障排除

### 1. 导入错误

如果遇到导入错误，确保已安装lighter-python SDK：

```bash
cd ../lighter-python
pip install -e .
```

### 2. SignerClient导入问题

如果出现"未找到签名客户端库"警告：

1. 确保 lighter-python 目录在 Python 路径中
2. 检查 lighter-python/lighter/signer_client.py 文件是否存在
3. 重启 Python 解释器或应用程序

### 3. 私钥长度错误

如果出现"invalid private key length"错误：

1. **40字符私钥**: SignerClient期望的标准格式
2. **64字符私钥**: 标准ECDSA私钥，会自动截取前40字符
3. **80字符私钥**: 特殊格式，支持整个字符串使用
4. **其他长度**: 会自动处理，但可能不是有效私钥

检查 .env 文件中的 LIGHTER_PRIVATE_KEY 配置。

### 4. WebSocket连接失败

检查网络连接和防火墙设置，确保可以访问WebSocket URL。

### 5. 交易功能不可用

确保：
- 已安装签名库
- 私钥配置正确
- 账户有足够余额

### 6. API调用失败

检查网络连接和API端点配置，确保使用正确的网络（mainnet/testnet）。

## 开发指南

### 添加新功能

1. 在相应模块中添加功能
2. 更新错误处理
3. 添加测试用例
4. 更新文档

### 代码规范

- 遵循PEP 8编码规范
- 使用类型注解
- 添加文档字符串
- 统一错误处理

## 许可证

[根据项目许可证]

## 支持

如有问题或建议，请提交Issue或联系开发者。
