"""
Lighter交易所Python客户端包

提供功能完整的Lighter交易所客户端，支持REST API、WebSocket实时数据、
自动精度管理和交易功能。
"""

from .config import LighterConfig, get_config, ConfigError
from .precision_manager import PrecisionManager, PrecisionManagerError
from .websocket_client import LighterWebSocketClient, WebSocketClientError
from .lighter_client import LighterClient, LighterClientError

__version__ = "1.0.0"
__author__ = "Lighter Client Team"
__email__ = ""

__all__ = [
    # 配置模块
    "LighterConfig",
    "get_config",
    "ConfigError",
    
    # 精度管理模块
    "PrecisionManager",
    "PrecisionManagerError",
    
    # WebSocket模块
    "LighterWebSocketClient",
    "WebSocketClientError",
    
    # 主客户端
    "LighterClient",
    "LighterClientError",
]
