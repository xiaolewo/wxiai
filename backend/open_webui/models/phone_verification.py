import time
import uuid
from typing import Optional, List
from enum import Enum

from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, Field, validator
from sqlalchemy import BigInteger, Column, String, Integer, and_, desc

####################
# Enums
####################


class VerificationPurpose(str, Enum):
    REGISTER = "register"
    LOGIN = "login"
    BIND = "bind"
    CHANGE = "change"


####################
# Phone Verification DB Schema
####################


class PhoneVerificationCode(Base):
    __tablename__ = "phone_verification_codes"

    id = Column(String, primary_key=True)
    phone = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    attempts = Column(Integer, default=0)
    created_at = Column(BigInteger, nullable=False, index=True)
    expires_at = Column(BigInteger, nullable=False, index=True)
    used_at = Column(BigInteger, nullable=True)


####################
# Pydantic Models
####################


class PhoneVerificationCodeModel(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    phone: str
    code: str
    purpose: VerificationPurpose
    user_id: Optional[str] = None
    attempts: int = 0
    created_at: int = Field(default_factory=lambda: int(time.time()))
    expires_at: int
    used_at: Optional[int] = None

    model_config = {"from_attributes": True}


####################
# Form Models
####################


class SendSmsCodeForm(BaseModel):
    phone: str
    purpose: VerificationPurpose

    @validator("phone")
    def validate_phone(cls, v):
        # 中国大陆手机号验证
        import re

        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("Invalid Chinese mobile phone number format")
        return v


class VerifySmsCodeForm(BaseModel):
    phone: str
    code: str
    purpose: VerificationPurpose

    @validator("phone")
    def validate_phone(cls, v):
        # 中国大陆手机号验证
        import re

        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("Invalid Chinese mobile phone number format")
        return v

    @validator("code")
    def validate_code(cls, v):
        # 验证码格式验证 (6位数字)
        import re

        if not re.match(r"^\d{6}$", v):
            raise ValueError("Verification code must be 6 digits")
        return v


####################
# Database Operations
####################


class PhoneVerificationCodesTable:
    def __init__(self):
        self.CODE_EXPIRY_SECONDS = 300  # 5分钟
        self.SEND_INTERVAL_SECONDS = 60  # 1分钟发送间隔
        self.MAX_ATTEMPTS = 5  # 最大尝试次数

    def generate_code(self) -> str:
        """生成6位随机验证码"""
        import random

        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    def can_send_code(self, phone: str) -> tuple[bool, Optional[str]]:
        """检查是否可以发送验证码"""
        current_time = int(time.time())

        with get_db() as db:
            # 查找最近的验证码记录
            recent_code = (
                db.query(PhoneVerificationCode)
                .filter(
                    and_(
                        PhoneVerificationCode.phone == phone,
                        PhoneVerificationCode.created_at
                        > current_time - self.SEND_INTERVAL_SECONDS,
                    )
                )
                .order_by(desc(PhoneVerificationCode.created_at))
                .first()
            )

            if recent_code:
                remaining_time = self.SEND_INTERVAL_SECONDS - (
                    current_time - recent_code.created_at
                )
                return (
                    False,
                    f"Please wait {remaining_time} seconds before requesting again",
                )

            return True, None

    def create_verification_code(
        self, phone: str, purpose: VerificationPurpose, user_id: Optional[str] = None
    ) -> Optional[PhoneVerificationCodeModel]:
        """创建验证码记录"""
        # 检查发送频率限制
        can_send, error_msg = self.can_send_code(phone)
        if not can_send:
            return None

        current_time = int(time.time())
        code = self.generate_code()
        expires_at = current_time + self.CODE_EXPIRY_SECONDS

        verification_code = PhoneVerificationCodeModel(
            phone=phone,
            code=code,
            purpose=purpose,
            user_id=user_id,
            expires_at=expires_at,
        )

        with get_db() as db:
            db_record = PhoneVerificationCode(**verification_code.dict())
            db.add(db_record)
            db.commit()
            db.refresh(db_record)

            if db_record:
                return PhoneVerificationCodeModel.model_validate(db_record)
            return None

    def verify_code(
        self,
        phone: str,
        code: str,
        purpose: VerificationPurpose,
        user_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """验证验证码"""
        current_time = int(time.time())

        with get_db() as db:
            # 查找有效的验证码
            verification_record = (
                db.query(PhoneVerificationCode)
                .filter(
                    and_(
                        PhoneVerificationCode.phone == phone,
                        PhoneVerificationCode.purpose == purpose.value,
                        PhoneVerificationCode.used_at.is_(None),
                        PhoneVerificationCode.expires_at > current_time,
                    )
                )
                .order_by(desc(PhoneVerificationCode.created_at))
                .first()
            )

            if not verification_record:
                return False, "Verification code not found or expired"

            # 检查尝试次数
            if verification_record.attempts >= self.MAX_ATTEMPTS:
                return False, "Too many failed attempts"

            # 验证码匹配
            if verification_record.code != code:
                # 增加尝试次数
                verification_record.attempts += 1
                db.commit()
                remaining_attempts = self.MAX_ATTEMPTS - verification_record.attempts
                return (
                    False,
                    f"Invalid verification code. {remaining_attempts} attempts remaining",
                )

            # 验证成功，标记为已使用
            verification_record.used_at = current_time
            db.commit()

            return True, None

    def cleanup_expired_codes(self) -> int:
        """清理过期的验证码"""
        current_time = int(time.time())

        with get_db() as db:
            # 删除过期的验证码
            deleted_count = (
                db.query(PhoneVerificationCode)
                .filter(PhoneVerificationCode.expires_at < current_time)
                .delete()
            )
            db.commit()

            return deleted_count

    def get_user_recent_codes(
        self, user_id: str, limit: int = 10
    ) -> List[PhoneVerificationCodeModel]:
        """获取用户最近的验证码记录"""
        with get_db() as db:
            records = (
                db.query(PhoneVerificationCode)
                .filter(PhoneVerificationCode.user_id == user_id)
                .order_by(desc(PhoneVerificationCode.created_at))
                .limit(limit)
                .all()
            )

            return [
                PhoneVerificationCodeModel.model_validate(record) for record in records
            ]


PhoneVerificationCodes = PhoneVerificationCodesTable()
