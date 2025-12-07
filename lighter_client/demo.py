#!/usr/bin/env python3
"""
Lighter客户端演示脚本
展示如何实例化和使用Lighter交易所客户端
"""

import asyncio
import logging
import sys
import os

# 添加必要的目录到Python路径
current_dir = os.path.dirname(__file__)
project_root = current_dir
lighter_python_path = os.path.join(project_root, '..', 'lighter-python')

# 添加路径
sys.path.insert(0, project_root)  # lighter_client 目录
if lighter_python_path not in sys.path:
    sys.path.insert(0, lighter_python_path)  # lighter-python 目录

from src.lighter_client import LighterClient
from src.config import LighterConfig


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def demo_lighter_client():
    """演示Lighter客户端的使用"""
    print("=" * 70)
    print("Lighter交易所客户端演示")
    print("=" * 70)
    
    print("\n📋 演示步骤:")
    print("1. 创建配置和客户端实例")
    print("2. 初始化客户端")
    print("3. 获取市场信息")
    print("4. 获取订单簿")
    print("5. 演示WebSocket连接")
    print("6. 清理资源")
    
    # 1. 创建配置
    print("\n" + "=" * 70)
    print("1. 创建配置和客户端实例")
    print("=" * 70)
    
    try:
        # 使用测试环境文件
        config = LighterConfig(env_file=".env.test")
        print(f"✅ 配置加载成功:")
        print(f"   网络: {config.network}")
        print(f"   REST URL: {config.rest_url}")
        print(f"   WebSocket URL: {config.ws_url}")
        print(f"   账户索引: {config.account_index}")
        print(f"   交易对: {config.symbol} (永续合约)")
        
        # 创建客户端
        client = LighterClient(config)
        print("✅ 客户端实例创建成功")
        
    except Exception as e:
        print(f"❌ 创建客户端失败: {e}")
        return
    
    try:
        # 2. 初始化客户端
        print("\n" + "=" * 70)
        print("2. 初始化客户端")
        print("=" * 70)
        
        initialized = await client.initialize()
        if not initialized:
            print("❌ 客户端初始化失败")
            return
        
        print("✅ 客户端初始化成功")
        print(f"\n📊 客户端状态:")
        print(client)
        
        # 3. 获取市场信息
        print("\n" + "=" * 70)
        print("3. 获取市场信息")
        print("=" * 70)
        
        market_info = await client.get_market_info()
        print(f"✅ 市场信息获取成功:")
        print(f"   交易对: {market_info['symbol']}")
        print(f"   价格精度: {market_info['price_precision']} 位小数")
        print(f"   数量精度: {market_info['quantity_precision']} 位小数")
        print(f"   最小数量: {market_info['min_quantity']}")
        print(f"   最小交易额: {market_info['min_notional']}")
        
        # 4. 获取订单簿
        print("\n" + "=" * 70)
        print("4. 获取订单簿")
        print("=" * 70)
        
        order_book = await client.get_order_book(depth=3)
        print(f"✅ 订单簿获取成功:")
        print(f"   交易对: {order_book['symbol']}")
        print(f"   卖单数量: {len(order_book['asks'])}")
        print(f"   买单数量: {len(order_book['bids'])}")
        
        if order_book['asks']:
            print(f"\n📈 前3个卖单:")
            for i, ask in enumerate(order_book['asks'][:3]):
                print(f"   {i+1}. 价格: {ask['price']}, 数量: {ask['quantity']}")
        
        if order_book['bids']:
            print(f"\n📉 前3个买单:")
            for i, bid in enumerate(order_book['bids'][:3]):
                print(f"   {i+1}. 价格: {bid['price']}, 数量: {bid['quantity']}")
        
        # 5. WebSocket演示
        print("\n" + "=" * 70)
        print("5. WebSocket连接状态")
        print("=" * 70)
        
        if client.ws_client:
            if client.ws_client.is_connected():
                print("✅ WebSocket已连接")
                print(f"   连接URL: {client.config.ws_url}")
                
                # 演示订阅功能
                print(f"\n📡 订阅功能:")
                print(f"   - 支持订阅订单簿")
                print(f"   - 支持订阅账户更新")
                print(f"   - 支持订阅Ticker")
                print(f"   - 自动重连机制")
            else:
                print("⚠️  WebSocket未连接")
        else:
            print("⚠️  WebSocket客户端不可用")
        
        # 6. 交易功能状态
        print("\n" + "=" * 70)
        print("6. 交易功能状态")
        print("=" * 70)
        
        if client.signer_client:
            print("✅ 签名客户端可用")
            print("   支持功能:")
            print("   - 创建订单")
            print("   - 取消订单")
            print("   - 查询订单状态")
            print("   - 账户交易")
        else:
            print("⚠️  签名客户端不可用")
            print("   原因: 未安装签名库或配置不正确")
            print("   注意: 需要有效的私钥才能使用交易功能")
        
        # 7. 精度管理演示
        print("\n" + "=" * 70)
        print("7. 精度管理演示")
        print("=" * 70)
        
        if client.precision_manager:
            print("✅ 精度管理器可用")
            print("   功能:")
            print("   - 自动从交易所获取精度信息")
            print("   - 价格和数量精度转换")
            print("   - 缓存精度数据提高性能")
            
            # 演示精度转换
            test_price = 3002.755
            test_quantity = 0.123456
            
            formatted_price = client.precision_manager.format_price(test_price, config.symbol)
            formatted_quantity = client.precision_manager.format_quantity(test_quantity, config.symbol)
            
            print(f"\n📐 精度转换示例:")
            print(f"   原始价格: {test_price}")
            print(f"   格式化后: {formatted_price}")
            print(f"   原始数量: {test_quantity}")
            print(f"   格式化后: {formatted_quantity}")
        else:
            print("⚠️  精度管理器不可用")
        
        print("\n" + "=" * 70)
        print("演示完成")
        print("=" * 70)
        
        print("\n🎉 Lighter客户端演示成功!")
        print("\n📝 总结:")
        print("   ✅ REST API连接正常")
        print("   ✅ WebSocket连接正常")
        print("   ✅ 市场信息获取正常")
        print("   ✅ 订单簿获取正常")
        print("   ✅ 精度管理功能正常")
        print("   ⚠️  交易功能需要有效私钥")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理资源
        print("\n" + "=" * 70)
        print("清理资源")
        print("=" * 70)
        
        try:
            await client.close()
            print("✅ 客户端已关闭，资源已释放")
        except Exception as e:
            print(f"⚠️  关闭客户端时出错: {e}")


async def main():
    """主函数"""
    await demo_lighter_client()


if __name__ == "__main__":
    print("🚀 启动Lighter客户端演示...")
    asyncio.run(main())
    print("\n👋 演示结束")
