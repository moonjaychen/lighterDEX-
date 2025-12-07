"""
文件名：websocket_client.py
用途：Lighter交易所WebSocket客户端，实现实时数据订阅和消息处理
依赖：websockets, asyncio, json, logging, typing
核心功能：1. WebSocket连接管理；2. 实时数据订阅；3. 消息回调处理；4. 自动重连机制
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any
import websockets


class WebSocketClientError(Exception):
    """WebSocket客户端相关错误"""
    pass


class LighterWebSocketClient:
    """
    功能：Lighter交易所WebSocket客户端，实现实时数据订阅和消息处理
    入参：ws_url - WebSocket服务器URL；logger - 日志记录器
    返回值：WebSocket客户端实例
    核心规则：1. 优先使用WebSocket获取实时数据；2. 实现自动重连；3. 支持多频道订阅
    """
    
    def __init__(self, ws_url: str, logger: Optional[logging.Logger] = None):
        """
        功能：初始化WebSocket客户端
        入参：ws_url - WebSocket服务器URL；logger - 日志记录器
        返回值：无
        核心规则：初始化连接状态、订阅频道和回调函数
        """
        self.ws_url = ws_url
        self.logger = logger or logging.getLogger(__name__)
        
        # 连接状态
        self.connected = False
        self.connecting = False
        self.reconnecting = False
        
        # WebSocket连接对象
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        
        # 订阅管理
        self.subscriptions: Dict[str, List[Callable]] = {
            'order_book': {},      # market_id -> 回调函数列表
            'trade': {},           # market_id -> 回调函数列表
            'account_all': {},     # account_id -> 回调函数列表
            'ticker': {},          # symbol -> 回调函数列表
        }
        
        # 消息处理器
        self.message_handlers = {
            'connected': self._handle_connected,
            'ping': self._handle_ping,
            'pong': self._handle_pong,
            'subscribed/order_book': self._handle_subscribed_order_book,
            'update/order_book': self._handle_update_order_book,
            'subscribed/trade': self._handle_subscribed_trade,
            'update/trade': self._handle_update_trade,
            'subscribed/account_all': self._handle_subscribed_account,
            'update/account_all': self._handle_update_account,
            'subscribed/ticker': self._handle_subscribed_ticker,
            'update/ticker': self._handle_update_ticker,
        }
        
        # 重连配置
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1  # 初始重连延迟（秒）
        self.max_reconnect_delay = 30  # 最大重连延迟（秒）
        
        self.logger.debug(f"WebSocket客户端初始化完成，URL: {ws_url}")
    
    async def connect(self):
        """
        功能：连接到WebSocket服务器
        入参：无
        返回值：bool - 连接是否成功
        核心规则：1. 建立WebSocket连接；2. 等待连接确认；3. 处理连接错误
        """
        if self.connected or self.connecting:
            self.logger.warning("WebSocket已经在连接或已连接")
            return self.connected
        
        self.connecting = True
        self.reconnecting = False
        
        try:
            self.logger.info(f"连接到WebSocket: {self.ws_url}")
            self.websocket = await websockets.connect(self.ws_url)
            
            # 等待连接确认消息
            message = await asyncio.wait_for(self.websocket.recv(), timeout=5)
            message_data = json.loads(message)
            
            if message_data.get('type') == 'connected':
                self.connected = True
                self.connecting = False
                self.reconnect_attempts = 0
                self.reconnect_delay = 1
                
                self.logger.info("WebSocket连接成功")
                
                # 启动消息接收任务
                asyncio.create_task(self._receive_messages())
                
                # 重新订阅之前订阅的频道
                await self._resubscribe_all()
                
                return True
            else:
                self.logger.error(f"意外的连接响应: {message_data}")
                await self.disconnect()
                return False
                
        except asyncio.TimeoutError:
            self.logger.error("连接超时")
            await self.disconnect()
            return False
            
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            await self.disconnect()
            return False
    
    async def disconnect(self):
        """
        功能：断开WebSocket连接
        入参：无
        返回值：无
        核心规则：1. 关闭WebSocket连接；2. 更新连接状态；3. 清理资源
        """
        self.connected = False
        self.connecting = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.info("WebSocket连接已断开")
            except Exception as e:
                self.logger.error(f"断开连接时出错: {e}")
            finally:
                self.websocket = None
    
    async def _receive_messages(self):
        """
        功能：接收和处理WebSocket消息
        入参：无
        返回值：无
        核心规则：1. 持续接收消息；2. 解析JSON；3. 分发给对应的处理器
        """
        while self.connected and self.websocket:
            try:
                message = await self.websocket.recv()
                await self._process_message(message)
                
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket连接已关闭")
                self.connected = False
                await self._handle_disconnection()
                break
                
            except Exception as e:
                self.logger.error(f"接收消息时出错: {e}")
                # 继续接收下一条消息
    
    async def _process_message(self, message: str):
        """
        功能：处理接收到的WebSocket消息
        入参：message - 原始消息字符串
        返回值：无
        核心规则：1. 解析JSON；2. 根据消息类型调用处理器；3. 触发回调函数
        """
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            # 调用对应的消息处理器
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                self.logger.debug(f"未处理的消息类型: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {message}")
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
    
    async def _handle_disconnection(self):
        """
        功能：处理连接断开
        入参：无
        返回值：无
        核心规则：1. 尝试自动重连；2. 指数退避重连延迟
        """
        if self.reconnecting:
            return
        
        self.reconnecting = True
        
        while self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.logger.info(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
            
            # 等待重连延迟
            await asyncio.sleep(self.reconnect_delay)
            
            # 尝试重连
            if await self.connect():
                self.reconnecting = False
                return
            
            # 指数退避
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        self.logger.error(f"重连失败，已达到最大重连次数: {self.max_reconnect_attempts}")
        self.reconnecting = False
    
    async def subscribe(self, channel_type: str, identifier: str, callback: Callable):
        """
        功能：订阅WebSocket频道
        入参：channel_type - 频道类型；identifier - 标识符；callback - 回调函数
        返回值：bool - 订阅是否成功
        核心规则：1. 验证频道类型；2. 发送订阅消息；3. 注册回调函数
        """
        if channel_type not in self.subscriptions:
            raise WebSocketClientError(f"不支持的频道类型: {channel_type}")
        
        if not self.connected:
            self.logger.error("WebSocket未连接，无法订阅")
            return False
        
        # 构建频道字符串
        channel = f"{channel_type}/{identifier}"
        
        # 发送订阅消息
        subscribe_msg = {
            'type': 'subscribe',
            'channel': channel
        }
        
        try:
            await self.websocket.send(json.dumps(subscribe_msg))
            self.logger.info(f"发送订阅请求: {channel}")
            
            # 注册回调函数
            if identifier not in self.subscriptions[channel_type]:
                self.subscriptions[channel_type][identifier] = []
            
            self.subscriptions[channel_type][identifier].append(callback)
            
            return True
            
        except Exception as e:
            self.logger.error(f"订阅失败: {channel}, 错误: {e}")
            return False
    
    async def unsubscribe(self, channel_type: str, identifier: str):
        """
        功能：取消订阅WebSocket频道
        入参：channel_type - 频道类型；identifier - 标识符
        返回值：bool - 取消订阅是否成功
        核心规则：1. 验证频道类型；2. 发送取消订阅消息；3. 移除回调函数
        """
        if channel_type not in self.subscriptions:
            raise WebSocketClientError(f"不支持的频道类型: {channel_type}")
        
        if not self.connected:
            self.logger.error("WebSocket未连接，无法取消订阅")
            return False
        
        # 检查是否已订阅
        if identifier not in self.subscriptions[channel_type]:
            self.logger.warning(f"未订阅: {channel_type}/{identifier}")
            return False
        
        # 构建频道字符串
        channel = f"{channel_type}/{identifier}"
        
        # 发送取消订阅消息
        unsubscribe_msg = {
            'type': 'unsubscribe',
            'channel': channel
        }
        
        try:
            await self.websocket.send(json.dumps(unsubscribe_msg))
            self.logger.info(f"发送取消订阅请求: {channel}")
            
            # 移除回调函数
            del self.subscriptions[channel_type][identifier]
            
            return True
            
        except Exception as e:
            self.logger.error(f"取消订阅失败: {channel}, 错误: {e}")
            return False
    
    async def _resubscribe_all(self):
        """重新订阅所有频道"""
        self.logger.info("重新订阅所有频道")
        
        for channel_type, identifiers in self.subscriptions.items():
            for identifier, callbacks in identifiers.items():
                if callbacks:  # 如果有回调函数，重新订阅
                    # 只使用第一个回调函数重新订阅
                    await self.subscribe(channel_type, identifier, callbacks[0])
    
    # ========== 消息处理器 ==========
    
    async def _handle_connected(self, data: Dict[str, Any]):
        """处理连接确认消息"""
        self.logger.debug("收到连接确认消息")
    
    async def _handle_ping(self, data: Dict[str, Any]):
        """处理ping消息，回复pong"""
        try:
            pong_msg = {'type': 'pong'}
            await self.websocket.send(json.dumps(pong_msg))
            self.logger.debug("回复pong消息")
        except Exception as e:
            self.logger.error(f"回复pong失败: {e}")
    
    async def _handle_pong(self, data: Dict[str, Any]):
        """处理pong消息"""
        self.logger.debug("收到pong消息")
    
    async def _handle_subscribed_order_book(self, data: Dict[str, Any]):
        """处理订单簿订阅确认"""
        channel = data.get('channel', '')
        if ':' in channel:
            market_id = channel.split(':')[1]
            self.logger.info(f"订单簿订阅成功: market_id={market_id}")
            
            # 触发回调函数
            callbacks = self.subscriptions['order_book'].get(market_id, [])
            for callback in callbacks:
                try:
                    await callback('subscribed', data)
                except Exception as e:
                    self.logger.error(f"订单簿订阅回调执行失败: {e}")
    
    async def _handle_update_order_book(self, data: Dict[str, Any]):
        """处理订单簿更新"""
        channel = data.get('channel', '')
        if ':' in channel:
            market_id = channel.split(':')[1]
            
            # 触发回调函数
            callbacks = self.subscriptions['order_book'].get(market_id, [])
            for callback in callbacks:
                try:
                    await callback('update', data)
                except Exception as e:
                    self.logger.error(f"订单簿更新回调执行失败: {e}")
    
    async def _handle_subscribed_trade(self, data: Dict[str, Any]):
        """处理交易订阅确认"""
        channel = data.get('channel', '')
        if ':' in channel:
            market_id = channel.split(':')[1]
            self.logger.info(f"交易订阅成功: market_id={market_id}")
            
            # 触发回调函数
            callbacks = self.subscriptions['trade'].get(market_id, [])
            for callback in callbacks:
                try:
                    await callback('subscribed', data)
                except Exception as e:
                    self.logger.error(f"交易订阅回调执行失败: {e}")
    
    async def _handle_update_trade(self, data: Dict[str, Any]):
        """处理交易更新"""
        channel = data.get('channel', '')
        if ':' in channel:
            market_id = channel.split(':')[1]
            
            # 触发回调函数
            callbacks = self.subscriptions['trade'].get(market_id, [])
            for callback in callbacks:
                try:
                    await callback('update', data)
                except Exception as e:
                    self.logger.error(f"交易更新回调执行失败: {e}")
    
    async def _handle_subscribed_account(self, data: Dict[str, Any]):
        """处理账户订阅确认"""
        channel = data.get('channel', '')
        if ':' in channel:
            account_id = channel.split(':')[1]
            self.logger.info(f"账户订阅成功: account_id={account_id}")
            
            # 触发回调函数
            callbacks = self.subscriptions['account_all'].get(account_id, [])
            for callback in callbacks:
                try:
                    await callback('subscribed', data)
                except Exception as e:
                    self.logger.error(f"账户订阅回调执行失败: {e}")
    
    async def _handle_update_account(self, data: Dict[str, Any]):
        """处理账户更新"""
        channel = data.get('channel', '')
        if ':' in channel:
            account_id = channel.split(':')[1]
            
            # 触发回调函数
            callbacks = self.subscriptions['account_all'].get(account_id, [])
            for callback in callbacks:
                try:
                    await callback('update', data)
                except Exception as e:
                    self.logger.error(f"账户更新回调执行失败: {e}")
    
    async def _handle_subscribed_ticker(self, data: Dict[str, Any]):
        """处理ticker订阅确认"""
        channel = data.get('channel', '')
        if ':' in channel:
            symbol = channel.split(':')[1]
            self.logger.info(f"Ticker订阅成功: symbol={symbol}")
            
            # 触发回调函数
            callbacks = self.subscriptions['ticker'].get(symbol, [])
            for callback in callbacks:
                try:
                    await callback('subscribed', data)
                except Exception as e:
                    self.logger.error(f"Ticker订阅回调执行失败: {e}")
    
    async def _handle_update_ticker(self, data: Dict[str, Any]):
        """处理ticker更新"""
        channel = data.get('channel', '')
        if ':' in channel:
            symbol = channel.split(':')[1]
            
            # 触发回调函数
            callbacks = self.subscriptions['ticker'].get(symbol, [])
            for callback in callbacks:
                try:
                    await callback('update', data)
                except Exception as e:
                    self.logger.error(f"Ticker更新回调执行失败: {e}")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def get_subscription_count(self) -> Dict[str, int]:
        """获取各类型频道的订阅数量"""
        return {
            channel_type: len(identifiers)
            for channel_type, identifiers in self.subscriptions.items()
        }
