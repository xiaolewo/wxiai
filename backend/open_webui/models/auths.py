import logging
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.models.users import UserModel, Users
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, Text

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# DB MODEL
####################


class Auth(Base):
    __tablename__ = "auth"

    id = Column(String, primary_key=True)
    email = Column(String)
    password = Column(Text)
    active = Column(Boolean)


class AuthModel(BaseModel):
    id: str
    email: str
    password: str
    active: bool = True


####################
# Forms
####################


class Token(BaseModel):
    token: str
    token_type: str


class ApiKey(BaseModel):
    api_key: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str


class SigninResponse(Token, UserResponse):
    pass


class SigninForm(BaseModel):
    email: str
    password: str


class LdapForm(BaseModel):
    user: str
    password: str


class ProfileImageUrlForm(BaseModel):
    profile_image_url: str


class UpdateProfileForm(BaseModel):
    profile_image_url: str
    name: str


class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str


class SignupForm(BaseModel):
    name: str
    email: str
    password: str
    profile_image_url: Optional[str] = "/user.png"


class AddUserForm(SignupForm):
    role: Optional[str] = "pending"


class SendSmsCodeForm(BaseModel):
    phone: str
    purpose: str  # 'register', 'login', 'bind'


class PhoneSignupForm(BaseModel):
    phone: str
    code: str
    name: str
    password: str
    profile_image_url: Optional[str] = "/user.png"


class PhoneSigninForm(BaseModel):
    phone: str
    code: str


class BindPhoneForm(BaseModel):
    phone: str
    code: str


class BindEmailForm(BaseModel):
    email: str
    password: str  # 当前密码用于验证身份


class AuthsTable:
    def insert_new_auth(
        self,
        email: str,
        password: str,
        name: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
    ) -> Optional[UserModel]:
        with get_db() as db:
            log.info("insert_new_auth")

            id = str(uuid.uuid4())

            auth = AuthModel(
                **{"id": id, "email": email, "password": password, "active": True}
            )
            result = Auth(**auth.model_dump())
            db.add(result)

            user = Users.insert_new_user(
                id, name, email, profile_image_url, role, oauth_sub
            )

            db.commit()
            db.refresh(result)

            if result and user:
                return user
            else:
                return None

    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        # to avoid cycle-import error
        from open_webui.utils.auth import verify_password

        log.info(f"authenticate_user: {email}")

        user = Users.get_user_by_email(email)
        if not user:
            return None

        try:
            with get_db() as db:
                auth = db.query(Auth).filter_by(id=user.id, active=True).first()
                if auth:
                    if verify_password(password, auth.password):
                        return user
                    else:
                        return None
                else:
                    return None
        except Exception:
            return None

    def authenticate_user_by_api_key(self, api_key: str) -> Optional[UserModel]:
        log.info(f"authenticate_user_by_api_key: {api_key}")
        # if no api_key, return None
        if not api_key:
            return None

        try:
            user = Users.get_user_by_api_key(api_key)
            return user if user else None
        except Exception:
            return False

    def authenticate_user_by_email(self, email: str) -> Optional[UserModel]:
        log.info(f"authenticate_user_by_email: {email}")
        try:
            with get_db() as db:
                auth = db.query(Auth).filter_by(email=email, active=True).first()
                if auth:
                    user = Users.get_user_by_id(auth.id)
                    return user
        except Exception:
            return None

    def update_user_password_by_id(self, id: str, new_password: str) -> bool:
        try:
            with get_db() as db:
                result = (
                    db.query(Auth).filter_by(id=id).update({"password": new_password})
                )
                db.commit()
                return True if result == 1 else False
        except Exception:
            return False

    def update_email_by_id(self, id: str, email: str) -> bool:
        try:
            with get_db() as db:
                result = db.query(Auth).filter_by(id=id).update({"email": email})
                db.commit()
                return True if result == 1 else False
        except Exception:
            return False

    def insert_new_auth_with_phone(
        self,
        phone: str,
        password: str,
        name: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
    ) -> Optional[UserModel]:
        """使用手机号创建新用户"""
        with get_db() as db:
            log.info(f"insert_new_auth_with_phone: {phone}")

            id = str(uuid.uuid4())

            # 使用手机号作为email字段（临时方案，保持兼容性）
            # 在实际使用中会通过phone字段来识别
            auth = AuthModel(
                **{"id": id, "email": phone, "password": password, "active": True}
            )
            result = Auth(**auth.model_dump())
            db.add(result)

            # 创建用户记录，将手机号设置到phone字段
            user = Users.insert_new_user(id, name, phone, profile_image_url, role, None)

            # 更新用户的phone字段
            if user:
                Users.update_user_phone_by_id(id, phone)

            db.commit()
            db.refresh(result)

            if result and user:
                # 重新获取更新后的用户信息
                return Users.get_user_by_id(id)
            else:
                return None

    def authenticate_user_by_phone(self, phone: str) -> Optional[UserModel]:
        """通过手机号认证用户（用于验证码登录）"""
        log.info(f"authenticate_user_by_phone: {phone}")
        try:
            user = Users.get_user_by_phone(phone)
            return user if user else None
        except Exception:
            return None

    def get_user_identifier(self, identifier: str) -> Optional[UserModel]:
        """通过邮箱或手机号获取用户"""
        # 判断是否是手机号格式
        import re

        if re.match(r"^1[3-9]\d{9}$", identifier):
            return Users.get_user_by_phone(identifier)
        else:
            return Users.get_user_by_email(identifier)

    def delete_auth_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                # Delete User
                result = Users.delete_user_by_id(id)

                if result:
                    db.query(Auth).filter_by(id=id).delete()
                    db.commit()

                    return True
                else:
                    return False
        except Exception:
            return False


Auths = AuthsTable()
