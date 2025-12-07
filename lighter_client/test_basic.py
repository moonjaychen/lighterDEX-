#!/usr/bin/env python3
"""
Lighter客户端基本功能测试
"""

import asyncio
import logging
import sys
import os

# 添加当前目录到Python路径，以便导入src模块
sys.path.insert(0, os.path.dirname(__file__))

# 直接从src导入
from src.lighter_client import LighterClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("Lighter客户端基本功能测试")
    print("=" * 60)
    
    # 创建客户端实例（使用测试环境文件）
    print("\n1. 创建客户端实例...")
    try:
        # 使用测试环境文件
        from src.config import LighterConfig
        config = LighterConfig(env_file=".env.test")
        client = LighterClient(config)
        print("✅ 客户端实例创建成功")
    except Exception as e:
        print(f"❌ 客户端实例创建失败: {e}")
        return False
    
    try:
        # 初始化客户端
        print("\n2. 初始化客户端...")
        initialized = await client.initialize()
        
        if not initialized:
            print("❌ 客户端初始化失败")
            return False
        
        print("✅ 客户端初始化成功")
        print(f"客户端状态:\n{client}")
        
        # 测试获取市场信息
        print("\n3. 测试获取市场信息...")
        try:
            market_info = await client.get_market_info()
            print(f"✅ 获取市场信息成功")
            print(f"  交易对: {market_info.get('symbol')}")
            print(f"  价格精度: {market_info.get('price_precision')}")
            print(f"  数量精度: {market_info.get('quantity_precision')}")
        except Exception as e:
            print(f"❌ 获取市场信息失败: {e}")
            return False
        
        # 测试获取账户余额（可能失败，如果没有配置正确的私钥）
        print("\n4. 测试获取账户余额...")
        try:
            balances = await client.get_account_balance()
            print(f"✅ 获取账户余额成功")
            print(f"  资产数量: {len(balances)}")
            if balances:
                for symbol in list(balances.keys())[:3]:  # 只显示前3个
                    balance = balances[symbol]
                    print(f"  {symbol}: 可用={balance['free']}, 总计={balance['total']}")
        except Exception as e:
            print(f"⚠️  获取账户余额失败（可能是配置问题）: {e}")
            # 这不一定是测试失败，可能是配置问题
        
        # 测试获取订单簿
        print("\n5. 测试获取订单簿...")
        try:
            order_book = await client.get_order_book(depth=3)
            print(f"✅ 获取订单簿成功")
            print(f"  交易对: {order_book.get('symbol')}")
            print(f"  卖单数量: {len(order_book.get('asks', []))}")
            print(f"  买单数量: {len(order_book.get('bids', []))}")
            
            if order_book.get('asks'):
                print("  前2个卖单:")
                for i, ask in enumerate(order_book['asks'][:2]):
                    print(f"    {i+1}. 价格={ask.get('price')}, 数量={ask.get('quantity')}")
            
            if order_book.get('bids'):
                print("  前2个买单:")
                for i, bid in enumerate(order_book['bids'][:2]):
                    print(f"    {i+1}. 价格={bid.get('price')}, 数量={bid.get('quantity')}")
        except Exception as e:
            print(f"❌ 获取订单簿失败: {e}")
            return False
        
        # 测试WebSocket连接
        print("\n6. 测试WebSocket连接...")
        if client.ws_client:
            if client.ws_client.is_connected():
                print("✅ WebSocket已连接")
                print(f"  订阅数量: {client.ws_client.get_subscription_count()}")
            else:
                print("⚠️  WebSocket未连接")
        else:
            print("⚠️  WebSocket客户端不可用")
        
        print("\n" + "=" * 60)
        print("基本功能测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 关闭客户端
        print("\n7. 关闭客户端...")
        try:
            await client.close()
            print("✅ 客户端已关闭")
        except Exception as e:
            print(f"⚠️  关闭客户端时出错: {e}")


async def main():
    """主函数"""
    success = await test_basic_functionality()
    
    if success:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
