"""
敏感字段对称加密工具。

使用 Fernet 对称加密（AES-128-CBC + HMAC），密钥通过环境变量 ENCRYPTION_KEY 提供。
向后兼容：旧数据为明文存储，解密失败时按明文返回。
"""

import os
import base64
import hashlib

from django.conf import settings

# Fernet 对应前缀，用于判断密文格式
_FERNET_PREFIX = b'gAAAAA'


def _get_fernet():
    """获取Fernet实例，密钥未配置时抛出异常"""
    key = os.environ.get('ENCRYPTION_KEY', '')
    if not key:
        raise RuntimeError('未配置 ENCRYPTION_KEY 环境变量，无法加解密敏感字段（可用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 生成）')
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise RuntimeError(f'ENCRYPTION_KEY 无效: {e}')


def encrypt_value(value):
    """加密字符串，空值原样返回"""
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value):
    """解密字符串。

    密文格式匹配则解密；否则视为历史明文数据原样返回（兼容迁移前数据）。
    """
    if not value:
        return value
    # 仅对 Fernet 密文格式尝试解密，避免把明文当密文解密报错
    if not value.startswith(_FERNET_PREFIX.decode('utf-8')):
        return value
    f = _get_fernet()
    try:
        return f.decrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        # 密文损坏或密钥轮换后无法解密
        return ''


def is_encrypted(value):
    """判断值是否已是密文格式"""
    return bool(value) and value.startswith(_FERNET_PREFIX.decode('utf-8'))
