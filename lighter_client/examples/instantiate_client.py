#!/usr/bin/env python3
"""
文件名：instantiate_client.py
用途：Lighter客户端实例化示例，展示多种配置方式
依赖：asyncio, logging, sys, os, lighter_client, config
核心功能：1. 默认配置实例化；2. 自定义配置实例化；3. 配置文件实例化
"""

import asyncio
import logging
import sys
import os

# 添加 lighter-python 目录到Python路径，确保能正确导入 lighter 模块
lighter_python_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lighter-python')
if os.path.exists(lighter_python_path):
    sys.path.insert(0, lighter_python_path)
    print(f"✅ 添加 lighter-python 路径: {lighter_python_path}")
else:
    print(f"⚠️  未找到 lighter-python 目录: {lighter_python_path}")
    # 尝试其他可能的路径
    possible_paths = [
        '/root/myapp/simpleapp2/lighter-python',
        os.path.join(os.getcwd(), 'lighter-python'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lighter-python'),
    ]
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            sys.path.insert(0, path)
            print(f"✅ 从备用路径添加: {path}")
            break

# 添加当前目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lighter_client import LighterClient
from src.config import LighterConfig


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def instantiate_client_example():
    """客户端实例化示例"""
    print("=" * 60)
    print("Lighter客户端实例化示例")
    print("=" * 60)
    
    # 方法1：使用默认配置（从环境变量加载）
    print("\n方法1：使用默认配置")
    print("-" * 40)
    
    try:
        # 创建默认配置（从环境变量加载）
        config1 = LighterConfig()
        client1 = LighterClient(config1)
        
        print(f"✅ 客户端实例化成功")
        print(f"   网络: {config1.network}")
        print(f"   REST URL: {config1.rest_url}")
        print(f"   WebSocket URL: {config1.ws_url}")
        print(f"   交易对: {config1.symbol}")
        
        # 初始化客户端
        await client1.initialize()
        print(f"✅ 客户端初始化成功")
        
        # 获取市场信息
        market_info = await client1.get_market_info()
        print(f"✅ 获取市场信息成功:")
        print(f"   市场ID: {market_info['market_id']}")
        print(f"   价格精度: {market_info['price_precision']}")
        print(f"   数量精度: {market_info['quantity_precision']}")
        
        await client1.close()
        print("✅ 客户端已关闭")
        
    except Exception as e:
        print(f"❌ 方法1失败: {e}")
    
    # 方法2：使用自定义配置
    print("\n方法2：使用自定义配置")
    print("-" * 40)
    
    try:
        # 创建自定义配置 - 使用示例私钥（非真实私钥）
        # 注意：在实际使用中，应该从环境变量或安全存储中加载私钥
        config2 = LighterConfig(
            network="mainnet",
            account_index=0,
            api_key_index=0,
            private_key="example_private_key_64_chars_1234567890abcdef1234567890abcdef1234567890abcdef",  # 示例私钥
            symbol="BTC"  # 使用BTC交易对
        )
        
        client2 = LighterClient(config2)
        
        print(f"✅ 客户端实例化成功")
        print(f"   网络: {config2.network}")
        print(f"   交易对: {config2.symbol}")
        print(f"   注意：使用示例私钥，实际交易需要真实私钥")
        
        # 初始化客户端
        await client2.initialize()
        print(f"✅ 客户端初始化成功")
        
        # 获取市场信息
        market_info = await client2.get_market_info()
        print(f"✅ 获取市场信息成功:")
        print(f"   市场ID: {market_info['market_id']}")
        print(f"   价格精度: {market_info['price_precision']}")
        print(f"   数量精度: {market_info['quantity_precision']}")
        
        await client2.close()
        print("✅ 客户端已关闭")
        
    except Exception as e:
        print(f"❌ 方法2失败: {e}")
        print(f"   注意：示例私钥无法用于实际交易，仅用于演示配置方式")
    
    # 方法3：使用配置文件
    print("\n方法3：使用配置文件")
    print("-" * 40)
    
    try:
        # 从指定环境文件加载配置
        config3 = LighterConfig(env_file=".env.test")
        client3 = LighterClient(config3)
        
        print(f"✅ 客户端实例化成功")
        print(f"   配置文件: .env.test")
        print(f"   网络: {config3.network}")
        print(f"   交易对: {config3.symbol}")
        
        # 初始化客户端
        await client3.initialize()
        print(f"✅ 客户端初始化成功")
        
        # 获取订单簿
        order_book = await client3.get_order_book(depth=2)
        print(f"✅ 获取订单簿成功:")
        print(f"   卖单数量: {len(order_book['asks'])}")
        print(f"   买单数量: {len(order_book['bids'])}")
        
        if order_book['asks']:
            print(f"   卖1: {order_book['asks'][0]['price']}")
        if order_book['bids']:
            print(f"   买1: {order_book['bids'][0]['price']}")
        
        await client3.close()
        print("✅ 客户端已关闭")
        
    except Exception as e:
        print(f"❌ 方法3失败: {e}")
    
    print("\n" + "=" * 60)
    print("实例化示例完成")
    print("=" * 60)


async def main():
    """主函数"""
    await instantiate_client_example()


if __name__ == "__main__":
    print("🚀 启动Lighter客户端实例化示例...")
    asyncio.run(main())
    print("\n👋 示例结束")


# 快速使用指南
"""
快速使用Lighter客户端的步骤：

1. 安装依赖：
   pip install -r requirements.txt
   cd ../lighter-python && pip install -e .

2. 配置环境变量：
   复制 .env.example 为 .env
   编辑 .env 文件，设置私钥和交易对

3. 基本使用：
   ```python
   import asyncio
   from src.lighter_client import LighterClient
   from src.config import LighterConfig
   
   async def main():
       # 创建配置
       config = LighterConfig()
       
       # 创建客户端
       client = LighterClient(config)
       
       # 初始化
       await client.initialize()
       
       # 使用客户端
       market_info = await client.get_market_info()
       order_book = await client.get_order_book()
       
       # 关闭客户端
       await client.close()
   
   asyncio.run(main())
   ```

4. 支持的交易对：
   - ETH (以太坊永续合约)
   - BTC (比特币永续合约)
   - SOL (Solana永续合约)
   - 等其他交易对

5. 注意事项：
   - 确保网络连接正常
   - 私钥需要正确配置
   - 交易前验证精度信息
"""
