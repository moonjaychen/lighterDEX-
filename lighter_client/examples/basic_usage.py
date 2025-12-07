"""
文件名：basic_usage.py
用途：Lighter交易所客户端基本使用示例，演示WebSocket优先的数据获取模式
依赖：asyncio, logging, sys, os, lighter_client
核心功能：1. 客户端初始化与配置；2. WebSocket实时数据订阅；3. 数据验证与精度管理；4. 错误处理与资源清理
注意事项：所有交易所数据优先通过WebSocket获取，仅当WebSocket不可用时回退到REST API
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional

# 添加必要的目录到Python路径
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
lighter_python_path = os.path.join(project_root, '..', 'lighter-python')

# 添加路径
sys.path.insert(0, project_root)  # lighter_client 目录
if lighter_python_path not in sys.path:
    sys.path.insert(0, lighter_python_path)  # lighter-python 目录

from src.lighter_client import LighterClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def order_book_callback(event_type: str, data: Dict[str, Any]):
    """
    功能：订单簿WebSocket回调函数，处理实时订单簿数据
    入参：event_type - 事件类型；data - 事件数据
    返回值：无
    核心规则：1. 验证数据完整性；2. 处理订阅确认；3. 处理实时更新
    """
    try:
        if event_type == 'subscribed':
            channel = data.get('channel', '未知频道')
            logger.info(f"订单簿订阅成功: {channel}")
            print(f"✅ 订单簿订阅成功: {channel}")
            
        elif event_type == 'update':
            channel = data.get('channel', '未知频道')
            update_data = data.get('data', {})
            
            # 验证数据完整性
            if not update_data:
                logger.warning(f"订单簿更新数据为空: {channel}")
                return
            
            # 提取订单簿数据
            asks = update_data.get('asks', [])
            bids = update_data.get('bids', [])
            
            # 数据验证
            if not isinstance(asks, list) or not isinstance(bids, list):
                logger.error(f"订单簿数据格式错误: asks={type(asks)}, bids={type(bids)}")
                return
            
            logger.debug(f"订单簿更新: {channel}, 卖单数={len(asks)}, 买单数={len(bids)}")
            
            # 显示前3个价格档位
            if asks:
                print(f"📉 卖单前3档:")
                for i, ask in enumerate(asks[:3]):
                    price = ask.get('price', 0)
                    quantity = ask.get('quantity', 0)
                    print(f"    {i+1}. 价格={price}, 数量={quantity}")
            
            if bids:
                print(f"📈 买单前3档:")
                for i, bid in enumerate(bids[:3]):
                    price = bid.get('price', 0)
                    quantity = bid.get('quantity', 0)
                    print(f"    {i+1}. 价格={price}, 数量={quantity}")
                    
    except Exception as e:
        logger.error(f"订单簿回调处理失败: {e}")


async def account_callback(event_type: str, data: Dict[str, Any]):
    """
    功能：账户WebSocket回调函数，处理实时账户数据
    入参：event_type - 事件类型；data - 事件数据
    返回值：无
    核心规则：1. 验证数据完整性；2. 处理订阅确认；3. 处理余额更新
    """
    try:
        if event_type == 'subscribed':
            channel = data.get('channel', '未知频道')
            initial_data = data.get('data', {})
            
            logger.info(f"账户订阅成功: {channel}")
            print(f"✅ 账户订阅成功: {channel}")
            
            # 显示初始账户信息
            if initial_data and 'assets' in initial_data:
                assets = initial_data['assets']
                if isinstance(assets, dict):
                    print(f"💰 初始账户资产: {len(assets)} 种")
                    for symbol, asset_info in list(assets.items())[:5]:  # 显示前5个资产
                        balance = asset_info.get('balance', 0)
                        locked = asset_info.get('locked_balance', 0)
                        total = float(balance) + float(locked)
                        print(f"    {symbol}: 可用={balance}, 锁定={locked}, 总计={total}")
            
        elif event_type == 'update':
            channel = data.get('channel', '未知频道')
            update_data = data.get('data', {})
            
            # 验证数据完整性
            if not update_data:
                logger.warning(f"账户更新数据为空: {channel}")
                return
            
            logger.debug(f"账户更新: {channel}")
            
            # 检查是否有余额变化
            if 'assets' in update_data:
                assets = update_data['assets']
                if isinstance(assets, dict):
                    print(f"🔄 账户余额更新:")
                    for symbol, asset_info in assets.items():
                        balance = asset_info.get('balance', 0)
                        locked = asset_info.get('locked_balance', 0)
                        total = float(balance) + float(locked)
                        print(f"    {symbol}: 可用={balance}, 锁定={locked}, 总计={total}")
                        
    except Exception as e:
        logger.error(f"账户回调处理失败: {e}")


async def main():
    """
    功能：Lighter客户端主演示函数，展示WebSocket优先的数据获取模式
    入参：无
    返回值：无
    核心规则：1. 优先使用WebSocket获取实时数据；2. 验证数据正确性；3. 完善的错误处理
    """
    print("=" * 60)
    print("Lighter交易所客户端使用示例 - WebSocket优先模式")
    print("=" * 60)
    
    # 创建客户端实例
    print("\n1. 创建Lighter客户端实例...")
    try:
        client = LighterClient()
        print("✅ 客户端实例创建成功")
    except Exception as e:
        print(f"❌ 客户端实例创建失败: {e}")
        return
    
    try:
        # 初始化客户端
        print("\n2. 初始化客户端...")
        initialized = await client.initialize()
        
        if not initialized:
            print("❌ 客户端初始化失败")
            return
        
        print("✅ 客户端初始化成功")
        print(f"客户端状态:\n{client}")
        
        # 获取市场信息（精度管理）
        print("\n3. 获取市场信息与精度验证...")
        try:
            market_info = await client.get_market_info()
            
            # 数据验证
            required_fields = ['symbol', 'price_precision', 'quantity_precision', 'min_quantity']
            missing_fields = [field for field in required_fields if field not in market_info]
            
            if missing_fields:
                print(f"⚠️  市场信息缺少字段: {missing_fields}")
            else:
                print(f"✅ 市场信息完整")
                print(f"   交易对: {market_info['symbol']}")
                print(f"   价格精度: {market_info['price_precision']}")
                print(f"   数量精度: {market_info['quantity_precision']}")
                print(f"   最小数量: {market_info['min_quantity']}")
                
                # 验证精度值合理性
                if market_info['price_precision'] < 0 or market_info['price_precision'] > 10:
                    print(f"⚠️  价格精度值异常: {market_info['price_precision']}")
                if market_info['quantity_precision'] < 0 or market_info['quantity_precision'] > 10:
                    print(f"⚠️  数量精度值异常: {market_info['quantity_precision']}")
                    
        except Exception as e:
            print(f"❌ 获取市场信息失败: {e}")
            return
        
        # WebSocket优先的数据获取
        print("\n4. WebSocket优先数据获取演示...")
        
        # 检查WebSocket连接状态
        ws_available = client.ws_client and client.ws_client.is_connected()
        
        if ws_available:
            print("✅ WebSocket已连接，使用实时数据模式")
            
            # 创建WebSocket数据收集器
            order_book_updates = []
            account_updates = []
            
            # 定义收集器回调函数
            async def collect_order_book_updates(event_type: str, data: Dict[str, Any]):
                if event_type == 'update':
                    order_book_updates.append(data)
            
            async def collect_account_updates(event_type: str, data: Dict[str, Any]):
                if event_type == 'update':
                    account_updates.append(data)
            
            # 订阅订单簿
            symbol = client.config.symbol
            print(f"\n4.1 订阅订单簿实时数据: {symbol}")
            subscribed = await client.subscribe_order_book(symbol, collect_order_book_updates)
            
            if subscribed:
                print(f"✅ 订单簿订阅成功")
                
                # 同时订阅账户数据
                print(f"\n4.2 订阅账户实时数据")
                account_subscribed = await client.subscribe_account(collect_account_updates)
                
                if account_subscribed:
                    print(f"✅ 账户订阅成功")
                    
                    # 等待收集实时数据
                    print(f"\n4.3 等待5秒收集实时数据...")
                    await asyncio.sleep(5)
                    
                    # 显示收集到的数据统计
                    print(f"\n📊 实时数据收集结果:")
                    print(f"   订单簿更新次数: {len(order_book_updates)}")
                    print(f"   账户更新次数: {len(account_updates)}")
                    
                    if order_book_updates:
                        latest_order_book = order_book_updates[-1]
                        update_data = latest_order_book.get('data', {})
                        asks = update_data.get('asks', [])
                        bids = update_data.get('bids', [])
                        print(f"   最新订单簿: 卖单={len(asks)}, 买单={len(bids)}")
                    
                    if account_updates:
                        latest_account = account_updates[-1]
                        print(f"   最新账户更新时间: {latest_account.get('timestamp', '未知')}")
                    
                    # 取消订阅
                    print(f"\n4.4 取消订阅...")
                    # 注意：实际取消订阅需要根据具体实现调整
                    
                else:
                    print(f"❌ 账户订阅失败，回退到REST API")
                    ws_available = False
            else:
                print(f"❌ 订单簿订阅失败，回退到REST API")
                ws_available = False
        else:
            print("⚠️  WebSocket不可用，使用REST API模式")
        
        # 回退到REST API获取数据
        if not ws_available:
            print("\n5. 使用REST API获取数据...")
            
            # 获取账户余额
            print("\n5.1 获取账户余额...")
            try:
                balances = await client.get_account_balance()
                
                # 数据验证
                if not isinstance(balances, dict):
                    print(f"⚠️  账户余额数据格式错误: {type(balances)}")
                else:
                    print(f"✅ 获取账户余额成功")
                    print(f"   资产数量: {len(balances)}")
                    
                    # 显示前5个资产
                    for i, (symbol, balance) in enumerate(list(balances.items())[:5]):
                        free = balance.get('free', 0)
                        locked = balance.get('locked', 0)
                        total = balance.get('total', 0)
                        
                        # 验证数据一致性
                        if abs(total - (free + locked)) > 0.0001:
                            print(f"⚠️  资产数据不一致: {symbol}, 总计={total}, 可用+锁定={free+locked}")
                        
                        print(f"   {i+1}. {symbol}: 可用={free}, 锁定={locked}, 总计={total}")
                    
                    if len(balances) > 5:
                        print(f"   ... 还有 {len(balances) - 5} 个资产未显示")
                        
            except Exception as e:
                print(f"❌ 获取账户余额失败: {e}")
            
            # 获取订单簿
            print("\n5.2 获取订单簿...")
            try:
                order_book = await client.get_order_book(depth=5)
                
                # 数据验证
                required_fields = ['symbol', 'asks', 'bids']
                missing_fields = [field for field in required_fields if field not in order_book]
                
                if missing_fields:
                    print(f"⚠️  订单簿数据缺少字段: {missing_fields}")
                else:
                    print(f"✅ 获取订单簿成功")
                    print(f"   交易对: {order_book['symbol']}")
                    print(f"   卖单数量: {len(order_book['asks'])}")
                    print(f"   买单数量: {len(order_book['bids'])}")
                    
                    # 验证订单簿数据
                    if order_book['asks']:
                        print("   前3个卖单:")
                        for i, ask in enumerate(order_book['asks'][:3]):
                            price = ask.get('price', 0)
                            quantity = ask.get('quantity', 0)
                            
                            # 验证价格和数量合理性
                            if price <= 0:
                                print(f"⚠️   卖单价格异常: {price}")
                            if quantity <= 0:
                                print(f"⚠️   卖单数量异常: {quantity}")
                            
                            print(f"     {i+1}. 价格={price}, 数量={quantity}")
                    
                    if order_book['bids']:
                        print("   前3个买单:")
                        for i, bid in enumerate(order_book['bids'][:3]):
                            price = bid.get('price', 0)
                            quantity = bid.get('quantity', 0)
                            
                            # 验证价格和数量合理性
                            if price <= 0:
                                print(f"⚠️   买单价格异常: {price}")
                            if quantity <= 0:
                                print(f"⚠️   买单数量异常: {quantity}")
                            
                            print(f"     {i+1}. 价格={price}, 数量={quantity}")
                            
            except Exception as e:
                print(f"❌ 获取订单簿失败: {e}")
        
        # 交易功能演示（仅展示，不实际交易）
        print("\n6. 交易功能演示...")
        if client.signer_client:
            print("✅ 签名客户端可用")
            
            # 演示创建订单的参数验证
            print("   订单参数验证演示:")
            
            # 获取市场信息用于验证
            market_info = await client.get_market_info()
            symbol = market_info['symbol']
            price_precision = market_info['price_precision']
            quantity_precision = market_info['quantity_precision']
            
            print(f"   交易对: {symbol}")
            print(f"   价格精度: {price_precision}")
            print(f"   数量精度: {quantity_precision}")
            
            # 演示精度转换
            if client.precision_manager:
                raw_quantity = 1.23456789
                formatted_quantity = client.precision_manager.format_quantity(raw_quantity, symbol)
                print(f"   数量精度转换: {raw_quantity} -> {formatted_quantity}")
                
                raw_price = 1234.56789
                adjusted_price = client.precision_manager.adjust_to_tick_size(raw_price, symbol)
                print(f"   价格精度转换: {raw_price} -> {adjusted_price}")
            
            print("   ⚠️  注意：此为演示，不会实际创建订单")
        else:
            print("⚠️  签名客户端不可用，交易功能受限")
            print("   请检查私钥配置和签名客户端库")
        
        print("\n" + "=" * 60)
        print("示例运行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 运行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭客户端
        print("\n7. 关闭客户端...")
        try:
            await client.close()
            print("✅ 客户端已关闭")
        except Exception as e:
            print(f"⚠️  关闭客户端时出错: {e}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
