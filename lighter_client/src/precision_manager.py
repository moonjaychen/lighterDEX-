"""
文件名：precision_manager.py
用途：代币交易精度管理，从交易所获取精度并自动转换
依赖：lighter, asyncio, logging, typing
核心功能：1. 从交易所API获取市场信息；2. 解析精度数据；3. 提供精度转换方法
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from lighter.api_client import ApiClient
from lighter.api.order_api import OrderApi


class PrecisionManagerError(Exception):
    """精度管理相关错误"""
    pass


class PrecisionManager:
    """
    功能：代币交易精度管理，从交易所获取精度并自动转换
    入参：api_client - ApiClient实例
    返回值：精度管理器实例
    核心规则：1. 优先从WebSocket获取实时数据；2. 回退到REST API；3. 缓存精度信息
    """
    
    def __init__(self, api_client: ApiClient):
        """
        功能：初始化精度管理器
        入参：api_client - ApiClient实例
        返回值：无
        核心规则：初始化API客户端和缓存字典
        """
        self.api_client = api_client
        self.order_api = OrderApi(api_client)
        self.logger = logging.getLogger(__name__)
        
        # 缓存市场精度信息：market_id -> 精度信息
        self._precision_cache: Dict[int, Dict[str, Any]] = {}
        
        # 缓存符号到market_id的映射
        self._symbol_to_market_id: Dict[str, int] = {}
        
        self.logger.debug("精度管理器初始化完成")
    
    async def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        功能：获取交易对的市场信息，包括精度数据
        入参：symbol - 交易对符号（如"ETH"）
        返回值：Dict[str, Any] - 市场信息字典
        核心规则：1. 检查缓存；2. 从交易所API获取；3. 解析精度数据
        """
        # 检查缓存
        if symbol in self._symbol_to_market_id:
            market_id = self._symbol_to_market_id[symbol]
            if market_id in self._precision_cache:
                return self._precision_cache[market_id]
        
        try:
            # 从交易所获取订单簿信息
            order_books = await self.order_api.order_books()
            
            # 查找匹配的交易对
            market_id = None
            market_info = None
            
            for order_book in order_books.order_books:
                # 根据实际API响应，symbol字段包含交易对名称
                if hasattr(order_book, 'symbol') and order_book.symbol == symbol:
                    market_id = order_book.market_id
                    market_info = self._parse_market_info(order_book)
                    break
            
            if market_id is None:
                # 如果没有找到，尝试模糊匹配
                # 例如，用户可能输入"ETH-USDT"，但交易所使用"ETH"
                base_symbol = symbol.split('-')[0] if '-' in symbol else symbol
                for order_book in order_books.order_books:
                    if hasattr(order_book, 'symbol') and order_book.symbol == base_symbol:
                        market_id = order_book.market_id
                        market_info = self._parse_market_info(order_book)
                        break
            
            if market_id is None:
                # 如果仍然没有找到，尝试通过market_id映射
                market_id = await self._symbol_to_market_id_from_api(symbol)
                if market_id is None:
                    raise PrecisionManagerError(f"未找到交易对: {symbol}")
                
                # 获取特定market_id的详细信息
                order_book_details = await self.order_api.order_book_details(market_id=market_id)
                market_info = self._parse_market_details(order_book_details)
            
            # 缓存结果
            self._symbol_to_market_id[symbol] = market_id
            self._precision_cache[market_id] = market_info
            
            self.logger.info(f"获取市场信息成功: {symbol} -> market_id: {market_id}")
            return market_info
            
        except Exception as e:
            self.logger.error(f"获取市场信息失败: {symbol}, 错误: {e}")
            # 返回默认精度（如果API失败）
            return self._get_default_precision(symbol)
    
    async def _symbol_to_market_id_from_api(self, symbol: str) -> Optional[int]:
        """
        功能：通过API将符号转换为market_id
        入参：symbol - 交易对符号
        返回值：Optional[int] - market_id或None
        核心规则：遍历订单簿查找匹配的符号
        """
        try:
            order_books = await self.order_api.order_books()
            
            # 根据实际API结构调整
            # 假设order_books.order_books是列表，每个元素有market_id和symbol
            for order_book in order_books.order_books:
                if hasattr(order_book, 'symbol') and order_book.symbol == symbol:
                    return order_book.market_id
                
                # 尝试其他可能的字段名
                if hasattr(order_book, 'market_symbol'):
                    market_symbol = order_book.market_symbol.replace('/', '-')
                    if market_symbol == symbol:
                        return order_book.market_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"转换符号到market_id失败: {symbol}, 错误: {e}")
            return None
    
    def _parse_market_info(self, order_book: Any) -> Dict[str, Any]:
        """
        功能：解析订单簿信息，提取精度数据
        入参：order_book - 订单簿对象
        返回值：Dict[str, Any] - 解析后的市场信息
        核心规则：从订单簿对象中提取价格精度、数量精度等信息
        """
        # 根据实际API响应结构调整
        # 从用户提供的API响应中，我们可以看到以下字段：
        # symbol, market_id, market_type, base_asset_id, quote_asset_id, status
        # taker_fee, maker_fee, liquidation_fee, min_base_amount, min_quote_amount
        # order_quote_limit, supported_size_decimals, supported_price_decimals, supported_quote_decimals
        
        # 获取精度信息
        price_precision = getattr(order_book, 'supported_price_decimals', 2)
        quantity_precision = getattr(order_book, 'supported_size_decimals', 4)
        
        # 获取最小数量
        min_quantity_str = getattr(order_book, 'min_base_amount', '0.001')
        min_notional_str = getattr(order_book, 'min_quote_amount', '10.0')
        
        # 解析市场类型和资产信息
        market_type = getattr(order_book, 'market_type', 'perp')
        base_asset_id = getattr(order_book, 'base_asset_id', 0)
        quote_asset_id = getattr(order_book, 'quote_asset_id', 0)
        
        # 根据市场类型确定报价资产
        if market_type == 'spot':
            quote_asset = 'USDC'  # 假设现货交易对使用USDC
        else:
            quote_asset = 'USD'   # 永续合约使用USD
        
        market_info = {
            'symbol': getattr(order_book, 'symbol', 'UNKNOWN'),
            'market_id': getattr(order_book, 'market_id', 0),
            'market_type': market_type,
            'base_asset_id': base_asset_id,
            'quote_asset_id': quote_asset_id,
            'base_asset': getattr(order_book, 'symbol', 'UNKNOWN'),  # 基础资产就是符号本身
            'quote_asset': quote_asset,
            'price_precision': int(price_precision),
            'quantity_precision': int(quantity_precision),
            'min_quantity': float(min_quantity_str),
            'min_notional': float(min_notional_str),
            'status': getattr(order_book, 'status', 'unknown'),
            'taker_fee': float(getattr(order_book, 'taker_fee', '0.0000')),
            'maker_fee': float(getattr(order_book, 'maker_fee', '0.0000')),
        }
        
        return market_info
    
    def _parse_market_details(self, order_book_details: Any) -> Dict[str, Any]:
        """
        功能：解析订单簿详细信息
        入参：order_book_details - 订单簿详细信息对象
        返回值：Dict[str, Any] - 解析后的市场信息
        核心规则：从详细信息中提取精度数据
        """
        # 根据实际API结构调整
        market_info = {
            'symbol': getattr(order_book_details, 'symbol', 'UNKNOWN'),
            'market_id': getattr(order_book_details, 'market_id', 0),
            'base_asset': getattr(order_book_details, 'base_asset', ''),
            'quote_asset': getattr(order_book_details, 'quote_asset', ''),
            'price_precision': self._extract_precision(getattr(order_book_details, 'tick_size', '0.01')),
            'quantity_precision': self._extract_precision(getattr(order_book_details, 'step_size', '0.001')),
            'min_quantity': float(getattr(order_book_details, 'min_order_size', '0.001')),
            'min_notional': float(getattr(order_book_details, 'min_notional_value', '10.0')),
        }
        
        return market_info
    
    def _extract_precision(self, tick_size: str) -> int:
        """
        功能：从tick_size字符串中提取精度（小数位数）
        入参：tick_size - tick大小字符串（如"0.01"）
        返回值：int - 精度（小数位数）
        核心规则：计算小数点后的位数
        """
        if '.' not in tick_size:
            return 0
        
        # 移除末尾的0
        decimal_part = tick_size.split('.')[1].rstrip('0')
        return len(decimal_part)
    
    def _get_default_precision(self, symbol: str) -> Dict[str, Any]:
        """
        功能：获取默认精度（当API失败时使用）
        入参：symbol - 交易对符号
        返回值：Dict[str, Any] - 默认精度信息
        核心规则：根据常见交易对提供合理的默认值
        """
        self.logger.warning(f"使用默认精度: {symbol}")
        
        # 常见交易对的默认精度
        default_precisions = {
            'BTC-USDT': {'price': 2, 'quantity': 6},
            'ETH-USDT': {'price': 2, 'quantity': 4},
            'SOL-USDT': {'price': 3, 'quantity': 2},
        }
        
        precision = default_precisions.get(symbol, {'price': 2, 'quantity': 4})
        
        return {
            'symbol': symbol,
            'market_id': 0,
            'base_asset': symbol.split('-')[0],
            'quote_asset': symbol.split('-')[1] if '-' in symbol else 'USDT',
            'price_precision': precision['price'],
            'quantity_precision': precision['quantity'],
            'min_quantity': 0.001,
            'min_notional': 10.0,
        }
    
    def format_price(self, price: float, symbol: str) -> str:
        """
        功能：格式化价格到正确的精度
        入参：price - 原始价格；symbol - 交易对符号
        返回值：str - 格式化后的价格字符串
        核心规则：根据交易对的精度进行四舍五入
        """
        market_info = self._precision_cache.get(
            self._symbol_to_market_id.get(symbol, 0),
            self._get_default_precision(symbol)
        )
        
        precision = market_info['price_precision']
        formatted = f"{price:.{precision}f}"
        return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
    
    def format_quantity(self, quantity: float, symbol: str) -> str:
        """
        功能：格式化数量到正确的精度
        入参：quantity - 原始数量；symbol - 交易对符号
        返回值：str - 格式化后的数量字符串
        核心规则：根据交易对的精度进行四舍五入
        """
        market_info = self._precision_cache.get(
            self._symbol_to_market_id.get(symbol, 0),
            self._get_default_precision(symbol)
        )
        
        precision = market_info['quantity_precision']
        min_quantity = market_info['min_quantity']
        
        # 确保数量不小于最小数量
        if quantity < min_quantity:
            quantity = min_quantity
        
        formatted = f"{quantity:.{precision}f}"
        return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
    
    def adjust_to_tick_size(self, price: float, symbol: str) -> float:
        """
        功能：调整价格到tick size的倍数
        入参：price - 原始价格；symbol - 交易对符号
        返回值：float - 调整后的价格
        核心规则：根据价格精度进行舍入
        """
        market_info = self._precision_cache.get(
            self._symbol_to_market_id.get(symbol, 0),
            self._get_default_precision(symbol)
        )
        
        precision = market_info['price_precision']
        factor = 10 ** precision
        
        # 四舍五入到指定精度
        adjusted = round(price * factor) / factor
        return adjusted
    
    async def refresh_cache(self):
        """刷新精度缓存"""
        self.logger.info("刷新精度缓存")
        self._precision_cache.clear()
        self._symbol_to_market_id.clear()
        
        try:
            # 重新获取所有订单簿信息
            order_books = await self.order_api.order_books()
            
            for order_book in order_books.order_books:
                if hasattr(order_book, 'symbol') and hasattr(order_book, 'market_id'):
                    symbol = order_book.symbol
                    market_id = order_book.market_id
                    
                    self._symbol_to_market_id[symbol] = market_id
                    self._precision_cache[market_id] = self._parse_market_info(order_book)
            
            self.logger.info(f"精度缓存刷新完成，缓存了 {len(self._precision_cache)} 个市场")
            
        except Exception as e:
            self.logger.error(f"刷新精度缓存失败: {e}")
