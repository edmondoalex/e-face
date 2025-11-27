from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..core import API_TOKEN, read_config, write_config, verify_user_password, create_access_token, get_user

router = APIRouter()


class AuthPayload(BaseModel):
    # support either token-based login or username/password
    token: str | None = None
    username: str | None = None
    password: str | None = None
    remote_host: str | None = None
    remote_token: str | None = None


@router.post("/login")
def login(payload: AuthPayload):
    # username/password login (internal panel)
    if payload.username and payload.password:
        # allow admin stored in config to login
        data = read_config()
        admin = data.get('admin', {})
        if payload.username == admin.get('username'):
            from ..core import verify_admin_password
            if verify_admin_password(payload.password):
                token = create_access_token(payload.username, is_admin=True, must_change=False)
                return {"access_token": token, "token_type": "bearer", "is_admin": True, "must_change": False}

        # verify against users list
        if verify_user_password(payload.username, payload.password):
            u = get_user(payload.username)
            is_admin = bool(u.get('is_admin'))
            must_change = bool(u.get('must_change'))
            token = create_access_token(payload.username, is_admin=is_admin, must_change=must_change)
            return {"access_token": token, "token_type": "bearer", "is_admin": is_admin, "must_change": must_change}
        raise HTTPException(status_code=401, detail="Bad credentials")

    # token-based login (legacy/dev)
    if payload.token and payload.token == API_TOKEN:
        # legacy token flow: persist remote integration if provided and return legacy token for compatibility
        if payload.remote_host:
            data = read_config()
            adv = data.get("advanced", {}) or {}
            adv["integration"] = {
                "host": payload.remote_host,
                "token": payload.remote_token,
                "enabled": True,
            }
            data["advanced"] = adv
            write_config(data)
        return {"access_token": API_TOKEN, "token_type": "bearer", "is_admin": False}

    raise HTTPException(status_code=401, detail="Bad token")
