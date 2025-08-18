import urllib.parse
import urllib.request
import hashlib
import logging
import time
from typing import Optional, Dict, Any
from open_webui.models.phone_verification import (
    PhoneVerificationCodes,
    VerificationPurpose,
)
from open_webui.config import get_config_value, save_config, CONFIG_DATA

log = logging.getLogger(__name__)


class SMSConfig:
    """短信配置类 - 基于数据库配置"""

    def __init__(self):
        self.config_path = "sms"
        self.load_config()

    def md5_encode(self, text: str) -> str:
        """MD5加密"""
        return hashlib.md5(text.encode("utf8")).hexdigest()

    def load_config(self):
        """从数据库加载配置"""
        sms_config = get_config_value(self.config_path) or {}

        self.provider = sms_config.get("provider", "smsbao")
        self.api_url = sms_config.get("api_url", "http://api.smsbao.com/")
        self.username = sms_config.get("username", "")
        self.password_md5 = sms_config.get("password_md5", "")
        self.signature = sms_config.get("signature", "【验证码】")
        self.enabled = sms_config.get("enabled", False)

    def save_config(self, config: Dict[str, Any]):
        """保存配置到数据库"""
        # 如果传入的是明文密码，进行MD5加密
        password = config.get("password", "")
        if password and not config.get("is_password_md5", False):
            config["password_md5"] = self.md5_encode(password)
            # 不保存明文密码
            config.pop("password", None)
        elif password and config.get("is_password_md5", False):
            config["password_md5"] = password
            config.pop("password", None)

        # 更新数据库配置
        CONFIG_DATA[self.config_path] = config
        save_config(CONFIG_DATA)

        # 重新加载配置
        self.load_config()

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            "provider": self.provider,
            "api_url": self.api_url,
            "username": self.username,
            "signature": self.signature,
            "enabled": self.enabled,
        }

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.enabled and self.username and self.password_md5


class SMSService:
    """短信服务类"""

    def __init__(self):
        self.config = SMSConfig()
        self.status_messages = {
            "0": "短信发送成功",
            "-1": "参数不全",
            "-2": "服务器空间不支持,请确认支持curl或者fsocket,联系您的空间商解决或者更换空间",
            "30": "密码错误",
            "40": "账号不存在",
            "41": "余额不足",
            "42": "账户已过期",
            "43": "IP地址限制",
            "50": "内容含有敏感词",
        }

    def update_config(self, config: Dict[str, Any]):
        """更新短信配置"""
        self.config.save_config(config)

    def get_verification_content(self, code: str, purpose: VerificationPurpose) -> str:
        """根据用途生成验证码短信内容"""
        purpose_texts = {
            VerificationPurpose.REGISTER: "注册",
            VerificationPurpose.LOGIN: "登录",
            VerificationPurpose.BIND: "绑定",
            VerificationPurpose.CHANGE: "修改",
        }
        purpose_text = purpose_texts.get(purpose, "验证")
        return f"您的{purpose_text}验证码是{code}，5分钟内有效，请勿泄露。"

    def send_verification_code(
        self, phone: str, purpose: VerificationPurpose, user_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """发送验证码短信"""
        try:
            # 检查短信服务是否已配置
            if not self.config.is_configured():
                return False, "SMS service not configured"

            # 创建验证码记录
            verification_code = PhoneVerificationCodes.create_verification_code(
                phone, purpose, user_id
            )
            if not verification_code:
                can_send, error_msg = PhoneVerificationCodes.can_send_code(phone)
                if not can_send:
                    return False, error_msg
                return False, "Failed to create verification code"

            # 生成短信内容
            content = self.config.signature + self.get_verification_content(
                verification_code.code, purpose
            )

            # 发送短信
            success, message = self._send_sms(phone, content)

            if success:
                log.info(f"SMS sent successfully to {phone} for {purpose.value}")
                return True, "Verification code sent successfully"
            else:
                log.error(f"Failed to send SMS to {phone}: {message}")
                return False, f"Failed to send SMS: {message}"

        except Exception as e:
            log.error(f"Error sending verification code: {str(e)}")
            return False, "Internal error occurred"

    def _send_sms(self, phone: str, content: str) -> tuple[bool, str]:
        """调用短信宝API发送短信"""
        try:
            # 构建请求参数
            data = urllib.parse.urlencode(
                {
                    "u": self.config.username,
                    "p": self.config.password_md5,
                    "m": phone,
                    "c": content,
                }
            )

            # 构建完整URL
            send_url = self.config.api_url + "sms?" + data

            # 发送HTTP请求
            response = urllib.request.urlopen(send_url, timeout=10)
            result_code = response.read().decode("utf-8").strip()

            # 解析响应
            if result_code in self.status_messages:
                message = self.status_messages[result_code]
                success = result_code == "0"
                return success, message
            else:
                return False, f"Unknown response code: {result_code}"

        except urllib.error.HTTPError as e:
            return False, f"HTTP error: {e.code} - {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL error: {str(e)}"
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def verify_code(
        self,
        phone: str,
        code: str,
        purpose: VerificationPurpose,
        user_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """验证验证码"""
        try:
            success, message = PhoneVerificationCodes.verify_code(
                phone, code, purpose, user_id
            )
            return success, message or "Verification failed"
        except Exception as e:
            log.error(f"Error verifying code: {str(e)}")
            return False, "Internal error occurred"

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        # 重新加载配置以确保最新状态
        self.config.load_config()
        config = self.config.get_config()
        config["configured"] = self.config.is_configured()
        return config


# 全局短信服务实例
sms_service = SMSService()


def get_sms_service() -> SMSService:
    """获取短信服务实例"""
    return sms_service


def send_verification_code(
    phone: str, purpose: VerificationPurpose, user_id: Optional[str] = None
) -> tuple[bool, str]:
    """发送验证码的便捷函数"""
    return sms_service.send_verification_code(phone, purpose, user_id)


def verify_verification_code(
    phone: str, code: str, purpose: VerificationPurpose, user_id: Optional[str] = None
) -> tuple[bool, str]:
    """验证验证码的便捷函数"""
    return sms_service.verify_code(phone, code, purpose, user_id)


def update_sms_config(config: Dict[str, Any]):
    """更新短信配置的便捷函数"""
    sms_service.update_config(config)


def get_sms_config_status() -> Dict[str, Any]:
    """获取短信配置状态的便捷函数"""
    return sms_service.get_config_status()
