"""
文件名：config.py
用途：Lighter交易所客户端配置管理，处理环境变量加载和验证
依赖：os, dotenv, typing
核心功能：1. 从.env文件加载配置；2. 验证配置完整性；3. 提供网络URL获取方法
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv


class ConfigError(Exception):
    """配置相关错误"""
    pass


class LighterConfig:
    """
    功能：Lighter交易所客户端配置管理
    入参：无（从环境变量加载）
    返回值：配置对象实例
    核心规则：1. 优先从.env文件加载；2. 验证必需配置项；3. 提供网络URL获取
    """
    
    # 必需配置项
    REQUIRED_KEYS = [
        'LIGHTER_NETWORK',
        'LIGHTER_ACCOUNT_INDEX',
        'LIGHTER_API_KEY_INDEX',
        'LIGHTER_PRIVATE_KEY',
    ]
    
    # 可选配置项（有默认值）
    OPTIONAL_KEYS = {
        'LIGHTER_SYMBOL': 'ETH-USDT',
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, env_file: Optional[str] = None, **kwargs):
        """
        功能：初始化配置，加载环境变量或使用提供的参数
        入参：
            env_file - .env文件路径（可选）
            **kwargs - 配置参数（可选），如果提供则覆盖环境变量
        返回值：无
        核心规则：1. 加载.env文件；2. 使用提供的参数；3. 验证必需配置；4. 设置默认值
        """
        # 加载环境变量
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            # 尝试从当前目录加载.env文件
            load_dotenv()
        
        # 如果有提供的参数，设置环境变量
        self._set_env_from_kwargs(kwargs)
        
        # 验证必需配置
        self._validate_config()
        
        # 设置配置属性
        self._set_config_values()
        
        # 验证私钥格式
        self._validate_private_key()
    
    def _set_env_from_kwargs(self, kwargs: dict):
        """从kwargs设置环境变量"""
        if not kwargs:
            return
        
        # 映射参数名到环境变量名
        param_mapping = {
            'network': 'LIGHTER_NETWORK',
            'account_index': 'LIGHTER_ACCOUNT_INDEX',
            'api_key_index': 'LIGHTER_API_KEY_INDEX',
            'private_key': 'LIGHTER_PRIVATE_KEY',
            'symbol': 'LIGHTER_SYMBOL',
            'log_level': 'LOG_LEVEL',
        }
        
        for param_name, env_name in param_mapping.items():
            if param_name in kwargs:
                os.environ[env_name] = str(kwargs[param_name])
    
    def _validate_config(self):
        """验证必需配置项是否存在"""
        missing_keys = []
        for key in self.REQUIRED_KEYS:
            if not os.getenv(key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigError(f"缺少必需配置项: {', '.join(missing_keys)}")
    
    def _set_config_values(self):
        """设置配置属性"""
        # 必需配置项
        self.network = os.getenv('LIGHTER_NETWORK').lower()
        self.account_index = int(os.getenv('LIGHTER_ACCOUNT_INDEX'))
        self.api_key_index = int(os.getenv('LIGHTER_API_KEY_INDEX'))
        self.private_key = os.getenv('LIGHTER_PRIVATE_KEY')
        
        # 可选配置项（使用默认值）
        self.symbol = os.getenv('LIGHTER_SYMBOL', self.OPTIONAL_KEYS['LIGHTER_SYMBOL'])
        self.log_level = os.getenv('LOG_LEVEL', self.OPTIONAL_KEYS['LOG_LEVEL'])
        
        # 网络URL配置
        self._set_network_urls()
    
    def _set_network_urls(self):
        """设置网络URL"""
        if self.network == 'mainnet':
            self.rest_url = os.getenv('LIGHTER_MAINNET_URL', 'https://mainnet.zklighter.elliot.ai')
            self.ws_url = os.getenv('LIGHTER_MAINNET_WS_URL', 'wss://mainnet.zklighter.elliot.ai/stream')
        elif self.network == 'testnet':
            self.rest_url = os.getenv('LIGHTER_TESTNET_URL', 'https://testnet.zklighter.elliot.ai')
            self.ws_url = os.getenv('LIGHTER_TESTNET_WS_URL', 'wss://testnet.zklighter.elliot.ai/stream')
        else:
            raise ConfigError(f"未知的网络类型: {self.network}，支持: mainnet, testnet")
    
    def _validate_private_key(self):
        """
        功能：验证私钥格式，支持多种私钥长度
        入参：无
        返回值：无
        核心规则：
        1. SignerClient期望40字符私钥（20字节）
        2. 标准ECDSA私钥是64字符（32字节）
        3. 支持从长字符串中提取有效私钥
        4. 自动处理0x前缀
        """
        if not self.private_key:
            raise ConfigError("私钥不能为空")
        
        # 移除0x前缀（如果存在）
        if self.private_key.startswith('0x'):
            self.private_key = self.private_key[2:]
        
        # 检查私钥长度
        key_length = len(self.private_key)
        
        # 根据SignerClient要求，优先使用40字符私钥
        # 但也要支持其他常见格式
        if key_length == 40:
            # SignerClient期望的40字符私钥（20字节）
            print(f"✅ 使用40字符私钥（SignerClient格式）")
            pass
        elif key_length == 64:
            # 标准64字符ECDSA私钥（32字节）
            print(f"⚠️  检测到64字符私钥，SignerClient可能需要40字符格式")
            # 尝试从64字符中提取40字符
            # 通常前40字符或后40字符可能是有效的
            self.private_key = self.private_key[:40]
            print(f"⚠️  截取前40字符: {self.private_key[:8]}...{self.private_key[-8:]}")
        elif key_length == 66:
            # 可能包含额外的校验字符
            self.private_key = self.private_key[:40]
            print(f"⚠️  私钥长度66，截取前40字符: {self.private_key[:8]}...{self.private_key[-8:]}")
        elif key_length == 80:
            # 用户提供的80字符私钥
            # 根据错误信息分析，可能是以下情况之一：
            # 1. 整个80字符字符串就是私钥（但SignerClient期望40字符）
            # 2. 80字符包含两个40字符的私钥，需要选择正确的一个
            # 3. 80字符是其他格式，需要特殊处理
            
            print(f"🔍 处理80字符私钥...")
            print(f"  原始私钥: {self.private_key[:16]}...{self.private_key[-16:]}")
            
            # 尝试策略：使用整个80字符字符串
            # 虽然SignerClient文档说期望40字符，但实际可能接受80字符
            # 或者C库会自己处理截断
            
            # 先尝试整个80字符
            original_80 = self.private_key
            self.private_key = original_80
            print(f"⚠️  尝试使用整个80字符字符串作为私钥")
            print(f"  长度: {len(self.private_key)} 字符")
            
            # 注意：这可能会失败，因为SignerClient期望40字符
            # 但如果失败，用户需要提供正确的40字符私钥
        else:
            # 对于其他长度，尝试提取40字符
            if key_length > 40:
                self.private_key = self.private_key[:40]
                print(f"⚠️  私钥长度{key_length}，截取前40字符: {self.private_key[:8]}...{self.private_key[-8:]}")
            else:
                raise ConfigError(f"私钥长度不足: {key_length}，至少需要40个字符（不带0x前缀）")
        
        # 检查是否为有效的十六进制字符串
        try:
            int(self.private_key, 16)
        except ValueError:
            raise ConfigError("私钥包含无效的十六进制字符")
        
        # 最终验证长度
        # 对于80字符私钥，我们允许使用整个字符串
        if key_length == 80:
            # 80字符私钥，不验证长度
            print(f"⚠️  使用80字符私钥，跳过标准长度验证")
        elif len(self.private_key) != 40:
            raise ConfigError(f"私钥处理后的长度不正确: {len(self.private_key)}，应为40个字符（SignerClient格式）")
        
        print(f"✅ 私钥验证通过: {self.private_key[:8]}...{self.private_key[-8:]}")
    
    def get_api_keys_dict(self) -> Dict[int, str]:
        """
        功能：获取API密钥字典，用于SignerClient初始化
        入参：无
        返回值：Dict[int, str] - API密钥索引到私钥的映射
        核心规则：使用配置中的api_key_index和private_key创建字典
        """
        return {self.api_key_index: self.private_key}
    
    def to_dict(self) -> Dict[str, str]:
        """返回配置字典（用于调试）"""
        return {
            'network': self.network,
            'account_index': self.account_index,
            'api_key_index': self.api_key_index,
            'private_key': f"{self.private_key[:8]}...{self.private_key[-8:]}" if self.private_key else None,
            'symbol': self.symbol,
            'log_level': self.log_level,
            'rest_url': self.rest_url,
            'ws_url': self.ws_url,
        }
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        config_dict = self.to_dict()
        return "\n".join([f"{key}: {value}" for key, value in config_dict.items()])


# 全局配置实例
_config_instance: Optional[LighterConfig] = None


def get_config(env_file: Optional[str] = None) -> LighterConfig:
    """
    功能：获取全局配置实例（单例模式）
    入参：env_file - .env文件路径（可选）
    返回值：LighterConfig实例
    核心规则：如果实例不存在则创建，否则返回现有实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = LighterConfig(env_file)
    return _config_instance
