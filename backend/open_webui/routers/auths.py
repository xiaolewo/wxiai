import re
import uuid
import time
import datetime
import logging
from decimal import Decimal

from aiohttp import ClientSession

from open_webui.models.auths import (
    AddUserForm,
    ApiKey,
    Auths,
    Token,
    LdapForm,
    SigninForm,
    SigninResponse,
    SignupForm,
    UpdatePasswordForm,
    UpdateProfileForm,
    UserResponse,
    SendSmsCodeForm,
    PhoneSignupForm,
    PhoneSigninForm,
    BindPhoneForm,
    BindEmailForm,
)
from open_webui.models.users import Users, UserModel
from open_webui.models.groups import Groups
from open_webui.models.credits import Credits
from open_webui.models.phone_verification import VerificationPurpose
from open_webui.utils.sms import (
    send_verification_code,
    verify_verification_code,
    get_sms_config_status,
)

from open_webui.constants import ERROR_MESSAGES, WEBHOOK_MESSAGES
from open_webui.env import (
    WEBUI_AUTH,
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    WEBUI_AUTH_TRUSTED_NAME_HEADER,
    WEBUI_AUTH_TRUSTED_GROUPS_HEADER,
    WEBUI_AUTH_COOKIE_SAME_SITE,
    WEBUI_AUTH_COOKIE_SECURE,
    WEBUI_AUTH_SIGNOUT_REDIRECT_URL,
    SRC_LOG_LEVELS,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response, JSONResponse
from open_webui.config import (
    OPENID_PROVIDER_URL,
    ENABLE_OAUTH_SIGNUP,
    ENABLE_LDAP,
)
from pydantic import BaseModel, Field

from open_webui.utils.misc import parse_duration, validate_email_format
from open_webui.utils.auth import (
    decode_token,
    create_api_key,
    create_token,
    get_admin_user,
    get_verified_user,
    get_current_user,
    get_password_hash,
    get_http_authorization_cred,
    send_verify_email,
    verify_email_by_code,
)
from open_webui.utils.webhook import post_webhook
from open_webui.utils.access_control import get_permissions

from typing import Optional, List

from ssl import CERT_NONE, CERT_REQUIRED, PROTOCOL_TLS

from ldap3 import Server, Connection, NONE, Tls
from ldap3.utils.conv import escape_filter_chars

router = APIRouter()

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


############################
# GetSessionUser
############################


class SessionUserResponse(Token, UserResponse):
    expires_at: Optional[int] = None
    permissions: Optional[dict] = None
    credit: Decimal


@router.get("/", response_model=SessionUserResponse)
async def get_session_user(
    request: Request, response: Response, user: UserModel = Depends(get_current_user)
):
    auth_header = request.headers.get("Authorization")
    auth_token = get_http_authorization_cred(auth_header)
    token = auth_token.credentials
    data = decode_token(token)

    expires_at = None

    if data:
        expires_at = data.get("exp")

        if (expires_at is not None) and int(time.time()) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.INVALID_TOKEN,
            )

        # Set the cookie token
        response.set_cookie(
            key="token",
            value=token,
            expires=(
                datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
                if expires_at
                else None
            ),
            httponly=True,  # Ensures the cookie is not accessible via JavaScript
            samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
            secure=WEBUI_AUTH_COOKIE_SECURE,
        )

    user_permissions = get_permissions(
        user.id, request.app.state.config.USER_PERMISSIONS
    )

    credit = Credits.init_credit_by_user_id(user.id)

    return {
        "token": token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
        "permissions": user_permissions,
        "credit": credit.credit,
    }


############################
# Update Profile
############################


@router.post("/update/profile", response_model=UserResponse)
async def update_profile(
    form_data: UpdateProfileForm, session_user=Depends(get_verified_user)
):
    if session_user:
        user = Users.update_user_by_id(
            session_user.id,
            {"profile_image_url": form_data.profile_image_url, "name": form_data.name},
        )
        if user:
            return user
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.DEFAULT())
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# Update Password
############################


@router.post("/update/password", response_model=bool)
async def update_password(
    form_data: UpdatePasswordForm, session_user=Depends(get_current_user)
):
    if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)
    if session_user:
        user = Auths.authenticate_user(session_user.email, form_data.password)

        if user:
            hashed = get_password_hash(form_data.new_password)
            return Auths.update_user_password_by_id(user.id, hashed)
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_PASSWORD)
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# LDAP Authentication
############################
@router.post("/ldap", response_model=SessionUserResponse)
async def ldap_auth(request: Request, response: Response, form_data: LdapForm):
    ENABLE_LDAP = request.app.state.config.ENABLE_LDAP
    LDAP_SERVER_LABEL = request.app.state.config.LDAP_SERVER_LABEL
    LDAP_SERVER_HOST = request.app.state.config.LDAP_SERVER_HOST
    LDAP_SERVER_PORT = request.app.state.config.LDAP_SERVER_PORT
    LDAP_ATTRIBUTE_FOR_MAIL = request.app.state.config.LDAP_ATTRIBUTE_FOR_MAIL
    LDAP_ATTRIBUTE_FOR_USERNAME = request.app.state.config.LDAP_ATTRIBUTE_FOR_USERNAME
    LDAP_SEARCH_BASE = request.app.state.config.LDAP_SEARCH_BASE
    LDAP_SEARCH_FILTERS = request.app.state.config.LDAP_SEARCH_FILTERS
    LDAP_APP_DN = request.app.state.config.LDAP_APP_DN
    LDAP_APP_PASSWORD = request.app.state.config.LDAP_APP_PASSWORD
    LDAP_USE_TLS = request.app.state.config.LDAP_USE_TLS
    LDAP_CA_CERT_FILE = request.app.state.config.LDAP_CA_CERT_FILE
    LDAP_VALIDATE_CERT = (
        CERT_REQUIRED if request.app.state.config.LDAP_VALIDATE_CERT else CERT_NONE
    )
    LDAP_CIPHERS = (
        request.app.state.config.LDAP_CIPHERS
        if request.app.state.config.LDAP_CIPHERS
        else "ALL"
    )

    if not ENABLE_LDAP:
        raise HTTPException(400, detail="LDAP authentication is not enabled")

    try:
        tls = Tls(
            validate=LDAP_VALIDATE_CERT,
            version=PROTOCOL_TLS,
            ca_certs_file=LDAP_CA_CERT_FILE,
            ciphers=LDAP_CIPHERS,
        )
    except Exception as e:
        log.error(f"TLS configuration error: {str(e)}")
        raise HTTPException(400, detail="Failed to configure TLS for LDAP connection.")

    try:
        server = Server(
            host=LDAP_SERVER_HOST,
            port=LDAP_SERVER_PORT,
            get_info=NONE,
            use_ssl=LDAP_USE_TLS,
            tls=tls,
        )
        connection_app = Connection(
            server,
            LDAP_APP_DN,
            LDAP_APP_PASSWORD,
            auto_bind="NONE",
            authentication="SIMPLE" if LDAP_APP_DN else "ANONYMOUS",
        )
        if not connection_app.bind():
            raise HTTPException(400, detail="Application account bind failed")

        ENABLE_LDAP_GROUP_MANAGEMENT = (
            request.app.state.config.ENABLE_LDAP_GROUP_MANAGEMENT
        )
        ENABLE_LDAP_GROUP_CREATION = request.app.state.config.ENABLE_LDAP_GROUP_CREATION
        LDAP_ATTRIBUTE_FOR_GROUPS = request.app.state.config.LDAP_ATTRIBUTE_FOR_GROUPS

        search_attributes = [
            f"{LDAP_ATTRIBUTE_FOR_USERNAME}",
            f"{LDAP_ATTRIBUTE_FOR_MAIL}",
            "cn",
        ]

        if ENABLE_LDAP_GROUP_MANAGEMENT:
            search_attributes.append(f"{LDAP_ATTRIBUTE_FOR_GROUPS}")
            log.info(
                f"LDAP Group Management enabled. Adding {LDAP_ATTRIBUTE_FOR_GROUPS} to search attributes"
            )

        log.info(f"LDAP search attributes: {search_attributes}")

        search_success = connection_app.search(
            search_base=LDAP_SEARCH_BASE,
            search_filter=f"(&({LDAP_ATTRIBUTE_FOR_USERNAME}={escape_filter_chars(form_data.user.lower())}){LDAP_SEARCH_FILTERS})",
            attributes=search_attributes,
        )

        if not search_success or not connection_app.entries:
            raise HTTPException(400, detail="User not found in the LDAP server")

        entry = connection_app.entries[0]
        username = str(entry[f"{LDAP_ATTRIBUTE_FOR_USERNAME}"]).lower()
        email = entry[
            f"{LDAP_ATTRIBUTE_FOR_MAIL}"
        ].value  # retrieve the Attribute value
        if not email:
            raise HTTPException(400, "User does not have a valid email address.")
        elif isinstance(email, str):
            email = email.lower()
        elif isinstance(email, list):
            email = email[0].lower()
        else:
            email = str(email).lower()

        cn = str(entry["cn"])
        user_dn = entry.entry_dn

        user_groups = []
        if ENABLE_LDAP_GROUP_MANAGEMENT and LDAP_ATTRIBUTE_FOR_GROUPS in entry:
            group_dns = entry[LDAP_ATTRIBUTE_FOR_GROUPS]
            log.info(f"LDAP raw group DNs for user {username}: {group_dns}")

            if group_dns:
                log.info(f"LDAP group_dns original: {group_dns}")
                log.info(f"LDAP group_dns type: {type(group_dns)}")
                log.info(f"LDAP group_dns length: {len(group_dns)}")

                if hasattr(group_dns, "value"):
                    group_dns = group_dns.value
                    log.info(f"Extracted .value property: {group_dns}")
                elif hasattr(group_dns, "__iter__") and not isinstance(
                    group_dns, (str, bytes)
                ):
                    group_dns = list(group_dns)
                    log.info(f"Converted to list: {group_dns}")

                if isinstance(group_dns, list):
                    group_dns = [str(item) for item in group_dns]
                else:
                    group_dns = [str(group_dns)]

                log.info(
                    f"LDAP group_dns after processing - type: {type(group_dns)}, length: {len(group_dns)}"
                )

                for group_idx, group_dn in enumerate(group_dns):
                    group_dn = str(group_dn)
                    log.info(f"Processing group DN #{group_idx + 1}: {group_dn}")

                    try:
                        group_cn = None

                        for item in group_dn.split(","):
                            item = item.strip()
                            if item.upper().startswith("CN="):
                                group_cn = item[3:]
                                break

                        if group_cn:
                            user_groups.append(group_cn)

                        else:
                            log.warning(
                                f"Could not extract CN from group DN: {group_dn}"
                            )
                    except Exception as e:
                        log.warning(
                            f"Failed to extract group name from DN {group_dn}: {e}"
                        )

                log.info(
                    f"LDAP groups for user {username}: {user_groups} (total: {len(user_groups)})"
                )
            else:
                log.info(f"No groups found for user {username}")
        elif ENABLE_LDAP_GROUP_MANAGEMENT:
            log.warning(
                f"LDAP Group Management enabled but {LDAP_ATTRIBUTE_FOR_GROUPS} attribute not found in user entry"
            )

        if username == form_data.user.lower():
            connection_user = Connection(
                server,
                user_dn,
                form_data.password,
                auto_bind="NONE",
                authentication="SIMPLE",
            )
            if not connection_user.bind():
                raise HTTPException(400, "Authentication failed.")

            user = Users.get_user_by_email(email)
            if not user:
                try:
                    role = (
                        "admin"
                        if not Users.has_users()
                        else request.app.state.config.DEFAULT_USER_ROLE
                    )

                    user = Auths.insert_new_auth(
                        email=email,
                        password=str(uuid.uuid4()),
                        name=cn,
                        role=role,
                    )

                    if not user:
                        raise HTTPException(
                            500, detail=ERROR_MESSAGES.CREATE_USER_ERROR
                        )

                except HTTPException:
                    raise
                except Exception as err:
                    log.error(f"LDAP user creation error: {str(err)}")
                    raise HTTPException(
                        500, detail="Internal error occurred during LDAP user creation."
                    )

            user = Auths.authenticate_user_by_email(email)

            if user:
                expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
                expires_at = None
                if expires_delta:
                    expires_at = int(time.time()) + int(expires_delta.total_seconds())

                token = create_token(
                    data={"id": user.id},
                    expires_delta=expires_delta,
                )

                # Set the cookie token
                response.set_cookie(
                    key="token",
                    value=token,
                    expires=(
                        datetime.datetime.fromtimestamp(
                            expires_at, datetime.timezone.utc
                        )
                        if expires_at
                        else None
                    ),
                    httponly=True,  # Ensures the cookie is not accessible via JavaScript
                    samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                    secure=WEBUI_AUTH_COOKIE_SECURE,
                )

                user_permissions = get_permissions(
                    user.id, request.app.state.config.USER_PERMISSIONS
                )

                credit = Credits.init_credit_by_user_id(user.id)

                if (
                    user.role != "admin"
                    and ENABLE_LDAP_GROUP_MANAGEMENT
                    and user_groups
                ):
                    if ENABLE_LDAP_GROUP_CREATION:
                        Groups.create_groups_by_group_names(user.id, user_groups)

                    try:
                        Groups.sync_groups_by_group_names(user.id, user_groups)
                        log.info(
                            f"Successfully synced groups for user {user.id}: {user_groups}"
                        )
                    except Exception as e:
                        log.error(f"Failed to sync groups for user {user.id}: {e}")

                return {
                    "token": token,
                    "token_type": "Bearer",
                    "expires_at": expires_at,
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "profile_image_url": user.profile_image_url,
                    "permissions": user_permissions,
                    "credit": credit.credit,
                }
            else:
                raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)
        else:
            raise HTTPException(400, "User record mismatch.")
    except Exception as e:
        log.error(f"LDAP authentication error: {str(e)}")
        raise HTTPException(400, detail="LDAP authentication failed.")


############################
# SignIn
############################


@router.post("/signin", response_model=SessionUserResponse)
async def signin(request: Request, response: Response, form_data: SigninForm):
    if WEBUI_AUTH_TRUSTED_EMAIL_HEADER:
        if WEBUI_AUTH_TRUSTED_EMAIL_HEADER not in request.headers:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_TRUSTED_HEADER)

        email = request.headers[WEBUI_AUTH_TRUSTED_EMAIL_HEADER].lower()
        name = email

        if WEBUI_AUTH_TRUSTED_NAME_HEADER:
            name = request.headers.get(WEBUI_AUTH_TRUSTED_NAME_HEADER, email)

        if not Users.get_user_by_email(email.lower()):
            await signup(
                request,
                response,
                SignupForm(email=email, password=str(uuid.uuid4()), name=name),
            )

        user = Auths.authenticate_user_by_email(email)
        if WEBUI_AUTH_TRUSTED_GROUPS_HEADER and user and user.role != "admin":
            group_names = request.headers.get(
                WEBUI_AUTH_TRUSTED_GROUPS_HEADER, ""
            ).split(",")
            group_names = [name.strip() for name in group_names if name.strip()]

            if group_names:
                Groups.sync_groups_by_group_names(user.id, group_names)

    elif WEBUI_AUTH == False:
        admin_email = "admin@localhost"
        admin_password = "admin"

        if Users.get_user_by_email(admin_email.lower()):
            user = Auths.authenticate_user(admin_email.lower(), admin_password)
        else:
            if Users.has_users():
                raise HTTPException(400, detail=ERROR_MESSAGES.EXISTING_USERS)

            await signup(
                request,
                response,
                SignupForm(email=admin_email, password=admin_password, name="User"),
            )

            user = Auths.authenticate_user(admin_email.lower(), admin_password)
    else:
        user = Auths.authenticate_user(form_data.email.lower(), form_data.password)

    if user:

        expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
        expires_at = None
        if expires_delta:
            expires_at = int(time.time()) + int(expires_delta.total_seconds())

        token = create_token(
            data={"id": user.id},
            expires_delta=expires_delta,
        )

        datetime_expires_at = (
            datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
            if expires_at
            else None
        )

        # Set the cookie token
        response.set_cookie(
            key="token",
            value=token,
            expires=datetime_expires_at,
            httponly=True,  # Ensures the cookie is not accessible via JavaScript
            samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
            secure=WEBUI_AUTH_COOKIE_SECURE,
        )

        user_permissions = get_permissions(
            user.id, request.app.state.config.USER_PERMISSIONS
        )

        credit = Credits.init_credit_by_user_id(user.id)

        return {
            "token": token,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
            "permissions": user_permissions,
            "credit": credit.credit,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# SignUp
############################


@router.post("/signup", response_model=SessionUserResponse)
async def signup(request: Request, response: Response, form_data: SignupForm):
    has_users = Users.has_users()

    if WEBUI_AUTH:
        if (
            not request.app.state.config.ENABLE_SIGNUP
            or not request.app.state.config.ENABLE_LOGIN_FORM
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
            )
    else:
        if has_users:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
            )

    # check for email domain whitelist
    email_domain_whitelist = [
        i.strip()
        for i in request.app.state.config.SIGNUP_EMAIL_DOMAIN_WHITELIST.split(",")
        if i
    ]
    if email_domain_whitelist:
        domain = form_data.email.split("@")[-1]
        if domain not in email_domain_whitelist:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Only emails from {request.app.state.config.SIGNUP_EMAIL_DOMAIN_WHITELIST} are allowed",
            )

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        if not has_users:
            role = "admin"
        elif request.app.state.config.ENABLE_SIGNUP_VERIFY:
            role = "pending"
            send_verify_email(email=form_data.email.lower())
        else:
            role = request.app.state.config.DEFAULT_USER_ROLE

        # The password passed to bcrypt must be 72 bytes or fewer. If it is longer, it will be truncated before hashing.
        if len(form_data.password.encode("utf-8")) > 72:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.PASSWORD_TOO_LONG,
            )

        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(),
            hashed,
            form_data.name,
            form_data.profile_image_url,
            role,
        )

        if user:
            expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
            expires_at = None
            if expires_delta:
                expires_at = int(time.time()) + int(expires_delta.total_seconds())

            token = create_token(
                data={"id": user.id},
                expires_delta=expires_delta,
            )

            datetime_expires_at = (
                datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
                if expires_at
                else None
            )

            # Set the cookie token
            response.set_cookie(
                key="token",
                value=token,
                expires=datetime_expires_at,
                httponly=True,  # Ensures the cookie is not accessible via JavaScript
                samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                secure=WEBUI_AUTH_COOKIE_SECURE,
            )

            if request.app.state.config.WEBHOOK_URL:
                post_webhook(
                    request.app.state.WEBUI_NAME,
                    request.app.state.config.WEBHOOK_URL,
                    WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                    {
                        "action": "signup",
                        "message": WEBHOOK_MESSAGES.USER_SIGNUP(user.name),
                        "user": user.model_dump_json(exclude_none=True),
                    },
                )

            user_permissions = get_permissions(
                user.id, request.app.state.config.USER_PERMISSIONS
            )

            if not has_users:
                # Disable signup after the first user is created
                request.app.state.config.ENABLE_SIGNUP = False

            credit = Credits.init_credit_by_user_id(user.id)

            return {
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at,
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
                "permissions": user_permissions,
                "credit": credit.credit,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        log.error(f"Signup error: {str(err)}")
        raise HTTPException(500, detail="An internal error occurred during signup.")


@router.get("/signup_verify/{code}")
async def signup_verify(request: Request, code: str):
    email = verify_email_by_code(code=code)
    if not email:
        raise HTTPException(403, detail="Invalid code")

    user = Users.get_user_by_email(email)
    if not user:
        raise HTTPException(404, detail="User not found")

    Users.update_user_role_by_id(user.id, "user")
    return RedirectResponse(url=request.app.state.config.WEBUI_URL)


@router.get("/signout")
async def signout(request: Request, response: Response):
    response.delete_cookie("token")
    response.delete_cookie("oui-session")

    if ENABLE_OAUTH_SIGNUP.value:
        oauth_id_token = request.cookies.get("oauth_id_token")
        if oauth_id_token and OPENID_PROVIDER_URL.value:
            try:
                async with ClientSession(trust_env=True) as session:
                    async with session.get(OPENID_PROVIDER_URL.value) as resp:
                        if resp.status == 200:
                            openid_data = await resp.json()
                            logout_url = openid_data.get("end_session_endpoint")
                            if logout_url:
                                response.delete_cookie("oauth_id_token")

                                return JSONResponse(
                                    status_code=200,
                                    content={
                                        "status": True,
                                        "redirect_url": f"{logout_url}?id_token_hint={oauth_id_token}"
                                        + (
                                            f"&post_logout_redirect_uri={WEBUI_AUTH_SIGNOUT_REDIRECT_URL}"
                                            if WEBUI_AUTH_SIGNOUT_REDIRECT_URL
                                            else ""
                                        ),
                                    },
                                    headers=response.headers,
                                )
                        else:
                            raise HTTPException(
                                status_code=resp.status,
                                detail="Failed to fetch OpenID configuration",
                            )
            except Exception as e:
                log.error(f"OpenID signout error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to sign out from the OpenID provider.",
                )

    if WEBUI_AUTH_SIGNOUT_REDIRECT_URL:
        return JSONResponse(
            status_code=200,
            content={
                "status": True,
                "redirect_url": WEBUI_AUTH_SIGNOUT_REDIRECT_URL,
            },
            headers=response.headers,
        )

    return JSONResponse(
        status_code=200, content={"status": True}, headers=response.headers
    )


############################
# AddUser
############################


@router.post("/add", response_model=SigninResponse)
async def add_user(form_data: AddUserForm, user=Depends(get_admin_user)):
    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(),
            hashed,
            form_data.name,
            form_data.profile_image_url,
            form_data.role,
        )

        if user:
            token = create_token(data={"id": user.id})
            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        log.error(f"Add user error: {str(err)}")
        raise HTTPException(
            500, detail="An internal error occurred while adding the user."
        )


############################
# GetAdminDetails
############################


@router.get("/admin/details")
async def get_admin_details(request: Request, user=Depends(get_current_user)):
    if request.app.state.config.SHOW_ADMIN_DETAILS:
        admin_email = request.app.state.config.ADMIN_EMAIL
        admin_name = None

        log.info(f"Admin details - Email: {admin_email}, Name: {admin_name}")

        if admin_email:
            admin = Users.get_user_by_email(admin_email)
            if admin:
                admin_name = admin.name
        else:
            admin = Users.get_first_user()
            if admin:
                admin_email = admin.email
                admin_name = admin.name

        return {
            "name": admin_name,
            "email": admin_email,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACTION_PROHIBITED)


############################
# ToggleSignUp
############################


@router.get("/admin/config")
async def get_admin_config(request: Request, user=Depends(get_admin_user)):
    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "WEBUI_URL": request.app.state.config.WEBUI_URL,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "ENABLE_SIGNUP_VERIFY": request.app.state.config.ENABLE_SIGNUP_VERIFY,
        "SIGNUP_EMAIL_DOMAIN_WHITELIST": request.app.state.config.SIGNUP_EMAIL_DOMAIN_WHITELIST,
        "ENABLE_API_KEY": request.app.state.config.ENABLE_API_KEY,
        "ENABLE_API_KEY_ENDPOINT_RESTRICTIONS": request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS,
        "API_KEY_ALLOWED_ENDPOINTS": request.app.state.config.API_KEY_ALLOWED_ENDPOINTS,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
        "ENABLE_MESSAGE_RATING": request.app.state.config.ENABLE_MESSAGE_RATING,
        "ENABLE_CHANNELS": request.app.state.config.ENABLE_CHANNELS,
        "ENABLE_NOTES": request.app.state.config.ENABLE_NOTES,
        "ENABLE_USER_WEBHOOKS": request.app.state.config.ENABLE_USER_WEBHOOKS,
        "PENDING_USER_OVERLAY_TITLE": request.app.state.config.PENDING_USER_OVERLAY_TITLE,
        "PENDING_USER_OVERLAY_CONTENT": request.app.state.config.PENDING_USER_OVERLAY_CONTENT,
        "RESPONSE_WATERMARK": request.app.state.config.RESPONSE_WATERMARK,
    }


class AdminConfig(BaseModel):
    SHOW_ADMIN_DETAILS: bool
    WEBUI_URL: str
    ENABLE_SIGNUP: bool
    ENABLE_SIGNUP_VERIFY: bool = Field(default=False)
    SIGNUP_EMAIL_DOMAIN_WHITELIST: str = Field(default="")
    ENABLE_API_KEY: bool
    ENABLE_API_KEY_ENDPOINT_RESTRICTIONS: bool
    API_KEY_ALLOWED_ENDPOINTS: str
    DEFAULT_USER_ROLE: str
    JWT_EXPIRES_IN: str
    ENABLE_COMMUNITY_SHARING: bool
    ENABLE_MESSAGE_RATING: bool
    ENABLE_CHANNELS: bool
    ENABLE_NOTES: bool
    ENABLE_USER_WEBHOOKS: bool
    PENDING_USER_OVERLAY_TITLE: Optional[str] = None
    PENDING_USER_OVERLAY_CONTENT: Optional[str] = None
    RESPONSE_WATERMARK: Optional[str] = None


@router.post("/admin/config")
async def update_admin_config(
    request: Request, form_data: AdminConfig, user=Depends(get_admin_user)
):
    request.app.state.config.SHOW_ADMIN_DETAILS = form_data.SHOW_ADMIN_DETAILS
    request.app.state.config.WEBUI_URL = form_data.WEBUI_URL
    request.app.state.config.ENABLE_SIGNUP = form_data.ENABLE_SIGNUP
    request.app.state.config.ENABLE_SIGNUP_VERIFY = form_data.ENABLE_SIGNUP_VERIFY
    request.app.state.config.SIGNUP_EMAIL_DOMAIN_WHITELIST = (
        form_data.SIGNUP_EMAIL_DOMAIN_WHITELIST
    )

    request.app.state.config.ENABLE_API_KEY = form_data.ENABLE_API_KEY
    request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS = (
        form_data.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS
    )
    request.app.state.config.API_KEY_ALLOWED_ENDPOINTS = (
        form_data.API_KEY_ALLOWED_ENDPOINTS
    )

    request.app.state.config.ENABLE_CHANNELS = form_data.ENABLE_CHANNELS
    request.app.state.config.ENABLE_NOTES = form_data.ENABLE_NOTES

    if form_data.DEFAULT_USER_ROLE in ["pending", "user", "admin"]:
        request.app.state.config.DEFAULT_USER_ROLE = form_data.DEFAULT_USER_ROLE

    pattern = r"^(-1|0|(-?\d+(\.\d+)?)(ms|s|m|h|d|w))$"

    # Check if the input string matches the pattern
    if re.match(pattern, form_data.JWT_EXPIRES_IN):
        request.app.state.config.JWT_EXPIRES_IN = form_data.JWT_EXPIRES_IN

    request.app.state.config.ENABLE_COMMUNITY_SHARING = (
        form_data.ENABLE_COMMUNITY_SHARING
    )
    request.app.state.config.ENABLE_MESSAGE_RATING = form_data.ENABLE_MESSAGE_RATING

    request.app.state.config.ENABLE_USER_WEBHOOKS = form_data.ENABLE_USER_WEBHOOKS

    request.app.state.config.PENDING_USER_OVERLAY_TITLE = (
        form_data.PENDING_USER_OVERLAY_TITLE
    )
    request.app.state.config.PENDING_USER_OVERLAY_CONTENT = (
        form_data.PENDING_USER_OVERLAY_CONTENT
    )

    request.app.state.config.RESPONSE_WATERMARK = form_data.RESPONSE_WATERMARK

    return {
        "SHOW_ADMIN_DETAILS": request.app.state.config.SHOW_ADMIN_DETAILS,
        "WEBUI_URL": request.app.state.config.WEBUI_URL,
        "ENABLE_SIGNUP": request.app.state.config.ENABLE_SIGNUP,
        "ENABLE_SIGNUP_VERIFY": request.app.state.config.ENABLE_SIGNUP_VERIFY,
        "SIGNUP_EMAIL_DOMAIN_WHITELIST": request.app.state.config.SIGNUP_EMAIL_DOMAIN_WHITELIST,
        "ENABLE_API_KEY": request.app.state.config.ENABLE_API_KEY,
        "ENABLE_API_KEY_ENDPOINT_RESTRICTIONS": request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS,
        "API_KEY_ALLOWED_ENDPOINTS": request.app.state.config.API_KEY_ALLOWED_ENDPOINTS,
        "DEFAULT_USER_ROLE": request.app.state.config.DEFAULT_USER_ROLE,
        "JWT_EXPIRES_IN": request.app.state.config.JWT_EXPIRES_IN,
        "ENABLE_COMMUNITY_SHARING": request.app.state.config.ENABLE_COMMUNITY_SHARING,
        "ENABLE_MESSAGE_RATING": request.app.state.config.ENABLE_MESSAGE_RATING,
        "ENABLE_CHANNELS": request.app.state.config.ENABLE_CHANNELS,
        "ENABLE_NOTES": request.app.state.config.ENABLE_NOTES,
        "ENABLE_USER_WEBHOOKS": request.app.state.config.ENABLE_USER_WEBHOOKS,
        "PENDING_USER_OVERLAY_TITLE": request.app.state.config.PENDING_USER_OVERLAY_TITLE,
        "PENDING_USER_OVERLAY_CONTENT": request.app.state.config.PENDING_USER_OVERLAY_CONTENT,
        "RESPONSE_WATERMARK": request.app.state.config.RESPONSE_WATERMARK,
    }


class LdapServerConfig(BaseModel):
    label: str
    host: str
    port: Optional[int] = None
    attribute_for_mail: str = "mail"
    attribute_for_username: str = "uid"
    app_dn: str
    app_dn_password: str
    search_base: str
    search_filters: str = ""
    use_tls: bool = True
    certificate_path: Optional[str] = None
    validate_cert: bool = True
    ciphers: Optional[str] = "ALL"


@router.get("/admin/config/ldap/server", response_model=LdapServerConfig)
async def get_ldap_server(request: Request, user=Depends(get_admin_user)):
    return {
        "label": request.app.state.config.LDAP_SERVER_LABEL,
        "host": request.app.state.config.LDAP_SERVER_HOST,
        "port": request.app.state.config.LDAP_SERVER_PORT,
        "attribute_for_mail": request.app.state.config.LDAP_ATTRIBUTE_FOR_MAIL,
        "attribute_for_username": request.app.state.config.LDAP_ATTRIBUTE_FOR_USERNAME,
        "app_dn": request.app.state.config.LDAP_APP_DN,
        "app_dn_password": request.app.state.config.LDAP_APP_PASSWORD,
        "search_base": request.app.state.config.LDAP_SEARCH_BASE,
        "search_filters": request.app.state.config.LDAP_SEARCH_FILTERS,
        "use_tls": request.app.state.config.LDAP_USE_TLS,
        "certificate_path": request.app.state.config.LDAP_CA_CERT_FILE,
        "validate_cert": request.app.state.config.LDAP_VALIDATE_CERT,
        "ciphers": request.app.state.config.LDAP_CIPHERS,
    }


@router.post("/admin/config/ldap/server")
async def update_ldap_server(
    request: Request, form_data: LdapServerConfig, user=Depends(get_admin_user)
):
    required_fields = [
        "label",
        "host",
        "attribute_for_mail",
        "attribute_for_username",
        "app_dn",
        "app_dn_password",
        "search_base",
    ]
    for key in required_fields:
        value = getattr(form_data, key)
        if not value:
            raise HTTPException(400, detail=f"Required field {key} is empty")

    request.app.state.config.LDAP_SERVER_LABEL = form_data.label
    request.app.state.config.LDAP_SERVER_HOST = form_data.host
    request.app.state.config.LDAP_SERVER_PORT = form_data.port
    request.app.state.config.LDAP_ATTRIBUTE_FOR_MAIL = form_data.attribute_for_mail
    request.app.state.config.LDAP_ATTRIBUTE_FOR_USERNAME = (
        form_data.attribute_for_username
    )
    request.app.state.config.LDAP_APP_DN = form_data.app_dn
    request.app.state.config.LDAP_APP_PASSWORD = form_data.app_dn_password
    request.app.state.config.LDAP_SEARCH_BASE = form_data.search_base
    request.app.state.config.LDAP_SEARCH_FILTERS = form_data.search_filters
    request.app.state.config.LDAP_USE_TLS = form_data.use_tls
    request.app.state.config.LDAP_CA_CERT_FILE = form_data.certificate_path
    request.app.state.config.LDAP_VALIDATE_CERT = form_data.validate_cert
    request.app.state.config.LDAP_CIPHERS = form_data.ciphers

    return {
        "label": request.app.state.config.LDAP_SERVER_LABEL,
        "host": request.app.state.config.LDAP_SERVER_HOST,
        "port": request.app.state.config.LDAP_SERVER_PORT,
        "attribute_for_mail": request.app.state.config.LDAP_ATTRIBUTE_FOR_MAIL,
        "attribute_for_username": request.app.state.config.LDAP_ATTRIBUTE_FOR_USERNAME,
        "app_dn": request.app.state.config.LDAP_APP_DN,
        "app_dn_password": request.app.state.config.LDAP_APP_PASSWORD,
        "search_base": request.app.state.config.LDAP_SEARCH_BASE,
        "search_filters": request.app.state.config.LDAP_SEARCH_FILTERS,
        "use_tls": request.app.state.config.LDAP_USE_TLS,
        "certificate_path": request.app.state.config.LDAP_CA_CERT_FILE,
        "validate_cert": request.app.state.config.LDAP_VALIDATE_CERT,
        "ciphers": request.app.state.config.LDAP_CIPHERS,
    }


@router.get("/admin/config/ldap")
async def get_ldap_config(request: Request, user=Depends(get_admin_user)):
    return {"ENABLE_LDAP": request.app.state.config.ENABLE_LDAP}


class LdapConfigForm(BaseModel):
    enable_ldap: Optional[bool] = None


@router.post("/admin/config/ldap")
async def update_ldap_config(
    request: Request, form_data: LdapConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_LDAP = form_data.enable_ldap
    return {"ENABLE_LDAP": request.app.state.config.ENABLE_LDAP}


############################
# API Key
############################


# create api key
@router.post("/api_key", response_model=ApiKey)
async def generate_api_key(request: Request, user=Depends(get_current_user)):
    if not request.app.state.config.ENABLE_API_KEY:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=ERROR_MESSAGES.API_KEY_CREATION_NOT_ALLOWED,
        )

    api_key = create_api_key()
    success = Users.update_user_api_key_by_id(user.id, api_key)

    if success:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_API_KEY_ERROR)


# delete api key
@router.delete("/api_key", response_model=bool)
async def delete_api_key(user=Depends(get_current_user)):
    success = Users.update_user_api_key_by_id(user.id, None)
    return success


# get api key
@router.get("/api_key", response_model=ApiKey)
async def get_api_key(user=Depends(get_current_user)):
    api_key = Users.get_user_api_key_by_id(user.id)
    if api_key:
        return {
            "api_key": api_key,
        }
    else:
        raise HTTPException(404, detail=ERROR_MESSAGES.API_KEY_NOT_FOUND)


############################
# SMS Verification Code APIs
############################


@router.post("/send-sms-code")
async def send_sms_code(form_data: SendSmsCodeForm):
    """发送短信验证码"""
    try:
        # 验证手机号格式
        import re

        if not re.match(r"^1[3-9]\d{9}$", form_data.phone):
            raise HTTPException(400, detail="Invalid phone number format")

        # 检查短信服务配置
        sms_status = get_sms_config_status()
        if not sms_status.get("configured", False):
            raise HTTPException(400, detail="SMS service not configured")

        # 验证purpose参数
        valid_purposes = ["register", "login", "bind"]
        if form_data.purpose not in valid_purposes:
            raise HTTPException(400, detail="Invalid purpose")

        # 对于注册，检查手机号是否已存在
        if form_data.purpose == "register":
            existing_user = Users.get_user_by_phone(form_data.phone)
            if existing_user:
                raise HTTPException(400, detail="Phone number already registered")

        # 对于登录，检查手机号是否存在
        if form_data.purpose == "login":
            existing_user = Users.get_user_by_phone(form_data.phone)
            if not existing_user:
                raise HTTPException(400, detail="Phone number not registered")

        # 发送验证码
        purpose_enum = VerificationPurpose(form_data.purpose)
        success, message = send_verification_code(form_data.phone, purpose_enum)

        if success:
            return {"success": True, "message": "Verification code sent successfully"}
        else:
            raise HTTPException(400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Send SMS code error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.post("/verify-sms-code")
async def verify_sms_code(phone: str, code: str, purpose: str):
    """验证短信验证码"""
    try:
        # 验证手机号格式
        import re

        if not re.match(r"^1[3-9]\d{9}$", phone):
            raise HTTPException(400, detail="Invalid phone number format")

        # 验证purpose参数
        valid_purposes = ["register", "login", "bind"]
        if purpose not in valid_purposes:
            raise HTTPException(400, detail="Invalid purpose")

        # 验证验证码
        purpose_enum = VerificationPurpose(purpose)
        success, message = verify_verification_code(phone, code, purpose_enum)

        if success:
            return {
                "success": True,
                "message": "Verification code verified successfully",
            }
        else:
            raise HTTPException(400, detail=message)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Verify SMS code error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


############################
# Phone-based Authentication
############################


@router.post("/signup-phone", response_model=SessionUserResponse)
async def signup_phone(
    request: Request, response: Response, form_data: PhoneSignupForm
):
    """手机号注册"""
    if not WEBUI_AUTH:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)

    try:
        # 验证手机号格式
        import re

        if not re.match(r"^1[3-9]\d{9}$", form_data.phone):
            raise HTTPException(400, detail="Invalid phone number format")

        # 检查手机号是否已注册
        if Users.get_user_by_phone(form_data.phone):
            raise HTTPException(400, detail="Phone number already registered")

        # 验证验证码
        success, message = verify_verification_code(
            form_data.phone, form_data.code, VerificationPurpose.REGISTER
        )
        if not success:
            raise HTTPException(400, detail=f"Verification failed: {message}")

        # 加密密码
        hashed = get_password_hash(form_data.password)

        # 创建用户
        role = "admin" if not Users.has_users() else "pending"
        user = Auths.insert_new_auth_with_phone(
            form_data.phone,
            hashed,
            form_data.name,
            form_data.profile_image_url,
            role,
        )

        if user:
            expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
            expires_at = None
            if expires_delta:
                expires_at = int(time.time()) + int(expires_delta.total_seconds())

            token = create_token(
                data={"id": user.id},
                expires_delta=expires_delta,
            )

            # Set the cookie token
            response.set_cookie(
                key="token",
                value=token,
                expires=(
                    datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
                    if expires_at
                    else None
                ),
                httponly=True,
                samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
                secure=WEBUI_AUTH_COOKIE_SECURE,
            )

            user_permissions = get_permissions(
                user.id, request.app.state.config.USER_PERMISSIONS
            )

            credit = Credits.init_credit_by_user_id(user.id)

            return {
                "token": token,
                "token_type": "Bearer",
                "expires_at": expires_at,
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
                "permissions": user_permissions,
                "credit": credit.credit,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Phone signup error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.post("/signin-phone", response_model=SessionUserResponse)
async def signin_phone(
    request: Request, response: Response, form_data: PhoneSigninForm
):
    """手机号验证码登录"""
    if not WEBUI_AUTH:
        raise HTTPException(400, detail=ERROR_MESSAGES.ACCESS_PROHIBITED)

    try:
        # 验证手机号格式
        import re

        if not re.match(r"^1[3-9]\d{9}$", form_data.phone):
            raise HTTPException(400, detail="Invalid phone number format")

        # 验证验证码
        success, message = verify_verification_code(
            form_data.phone, form_data.code, VerificationPurpose.LOGIN
        )
        if not success:
            raise HTTPException(400, detail=f"Verification failed: {message}")

        # 通过手机号认证用户
        user = Auths.authenticate_user_by_phone(form_data.phone)
        if not user:
            raise HTTPException(400, detail="Phone number not registered")

        expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
        expires_at = None
        if expires_delta:
            expires_at = int(time.time()) + int(expires_delta.total_seconds())

        token = create_token(
            data={"id": user.id},
            expires_delta=expires_delta,
        )

        # Set the cookie token
        response.set_cookie(
            key="token",
            value=token,
            expires=(
                datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
                if expires_at
                else None
            ),
            httponly=True,
            samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
            secure=WEBUI_AUTH_COOKIE_SECURE,
        )

        user_permissions = get_permissions(
            user.id, request.app.state.config.USER_PERMISSIONS
        )

        credit = Credits.init_credit_by_user_id(user.id)

        return {
            "token": token,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
            "permissions": user_permissions,
            "credit": credit.credit,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Phone signin error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


############################
# Binding Management APIs
############################


@router.post("/bind-phone")
async def bind_phone(form_data: BindPhoneForm, user=Depends(get_current_user)):
    """绑定手机号到当前用户"""
    try:
        # 验证手机号格式
        import re

        if not re.match(r"^1[3-9]\d{9}$", form_data.phone):
            raise HTTPException(400, detail="Invalid phone number format")

        # 检查手机号是否已被其他用户使用
        existing_user = Users.get_user_by_phone(form_data.phone)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                400, detail="Phone number already bound to another account"
            )

        # 验证验证码
        success, message = verify_verification_code(
            form_data.phone, form_data.code, VerificationPurpose.BIND, user.id
        )
        if not success:
            raise HTTPException(400, detail=f"Verification failed: {message}")

        # 绑定手机号
        bind_success, error_msg = Users.bind_phone_to_user(user.id, form_data.phone)
        if not bind_success:
            raise HTTPException(400, detail=error_msg or "Failed to bind phone number")

        return {"success": True, "message": "Phone number bound successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Bind phone error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.post("/bind-email")
async def bind_email(form_data: BindEmailForm, user=Depends(get_current_user)):
    """绑定邮箱到当前用户"""
    try:
        # 验证邮箱格式
        if not validate_email_format(form_data.email.lower()):
            raise HTTPException(400, detail="Invalid email format")

        # 检查邮箱是否已被其他用户使用
        existing_user = Users.get_user_by_email(form_data.email.lower())
        if existing_user and existing_user.id != user.id:
            raise HTTPException(400, detail="Email already bound to another account")

        # 验证当前用户密码（确保是本人操作）
        current_user_auth = Auths.authenticate_user(user.email, form_data.password)
        if not current_user_auth or current_user_auth.id != user.id:
            raise HTTPException(400, detail="Invalid password")

        # 更新用户邮箱
        updated_user = Users.update_user_by_id(
            user.id, {"email": form_data.email.lower()}
        )
        if not updated_user:
            raise HTTPException(400, detail="Failed to bind email")

        # 同时更新auth表中的邮箱
        Auths.update_email_by_id(user.id, form_data.email.lower())

        return {"success": True, "message": "Email bound successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Bind email error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.delete("/unbind-phone")
async def unbind_phone(user=Depends(get_current_user)):
    """解绑当前用户的手机号"""
    try:
        # 检查用户是否有手机号
        if not user.phone:
            raise HTTPException(400, detail="No phone number to unbind")

        # 解绑手机号
        unbind_success, error_msg = Users.unbind_phone_from_user(user.id)
        if not unbind_success:
            raise HTTPException(
                400, detail=error_msg or "Failed to unbind phone number"
            )

        return {"success": True, "message": "Phone number unbound successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unbind phone error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.delete("/unbind-email")
async def unbind_email(password: str, user=Depends(get_current_user)):
    """解绑当前用户的邮箱"""
    try:
        # 检查用户是否有邮箱
        if not user.email:
            raise HTTPException(400, detail="No email to unbind")

        # 检查用户是否至少有一种登录方式（手机号或邮箱）
        if not user.phone:
            raise HTTPException(
                400, detail="Cannot unbind email when no phone number is set"
            )

        # 验证当前用户密码（确保是本人操作）
        current_user_auth = Auths.authenticate_user(user.email, password)
        if not current_user_auth or current_user_auth.id != user.id:
            raise HTTPException(400, detail="Invalid password")

        # 解绑邮箱（设置为空）
        updated_user = Users.update_user_by_id(user.id, {"email": None})
        if not updated_user:
            raise HTTPException(400, detail="Failed to unbind email")

        # 同时更新auth表中的邮箱（使用手机号替代）
        if user.phone:
            Auths.update_email_by_id(user.id, user.phone)

        return {"success": True, "message": "Email unbound successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unbind email error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.get("/binding-status")
async def get_binding_status(user=Depends(get_current_user)):
    """获取当前用户的绑定状态"""
    try:
        return {
            "email": user.email,
            "phone": user.phone,
            "has_email": bool(user.email),
            "has_phone": bool(user.phone),
            "can_unbind_email": bool(user.phone),  # 有手机号才能解绑邮箱
            "can_unbind_phone": bool(user.email),  # 有邮箱才能解绑手机号
        }

    except Exception as e:
        log.error(f"Get binding status error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


############################
# SMS Configuration APIs (Admin Only)
############################


@router.get("/sms/config")
async def get_sms_config(user=Depends(get_admin_user)):
    """获取短信配置状态（仅管理员）"""
    try:
        config_status = get_sms_config_status()
        # 不返回敏感信息如密码
        return {
            "enabled": config_status.get("enabled", False),
            "configured": config_status.get("configured", False),
            "provider": config_status.get("provider", "smsbao"),
            "username": config_status.get("username", ""),
            "signature": config_status.get("signature", "【验证码】"),
        }
    except Exception as e:
        log.error(f"Get SMS config error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")


@router.post("/sms/config")
async def update_sms_config(config_data: dict, user=Depends(get_admin_user)):
    """更新短信配置（仅管理员）"""
    try:
        from open_webui.utils.sms import update_sms_config

        # 验证必需字段
        required_fields = ["enabled", "username", "signature"]
        for field in required_fields:
            if field not in config_data:
                raise HTTPException(400, detail=f"Missing required field: {field}")

        # 如果启用短信服务，需要验证密码
        if config_data.get("enabled", False) and not config_data.get("password"):
            raise HTTPException(
                400, detail="Password is required when SMS service is enabled"
            )

        # 更新配置
        update_sms_config(config_data)

        return {"success": True, "message": "SMS configuration updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Update SMS config error: {str(e)}")
        raise HTTPException(500, detail="Internal server error")
