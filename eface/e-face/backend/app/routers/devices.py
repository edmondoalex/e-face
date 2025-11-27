from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..core import read_config, require_token, fetch_ha_rooms
import requests

router = APIRouter()


@router.get("")
def list_devices(token_payload=Depends(require_token)):
    data = read_config()
    adv = data.get('advanced', {}) or {}
    integration = adv.get('integration')
    if not integration or not integration.get('enabled'):
        raise HTTPException(status_code=503, detail='integration_missing')
    try:
        rooms = fetch_ha_rooms(integration)
        devices = []
        for r in rooms:
            for d in r.get('devices', []):
                devices.append(d)
        return {"devices": devices}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"integration_failed:{e}")


@router.get("/{device_id}")
def get_device(device_id: str, token_payload=Depends(require_token)):
    data = read_config()
    adv = data.get('advanced', {}) or {}
    integration = adv.get('integration')
    if not integration or not integration.get('enabled'):
        raise HTTPException(status_code=503, detail='integration_missing')
    try:
        rooms = fetch_ha_rooms(integration)
        for r in rooms:
            for d in r.get('devices', []):
                if d.get('id') == device_id:
                    return d
        raise HTTPException(status_code=404, detail='Not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"integration_failed:{e}")


class BrightnessPayload(BaseModel):
    brightness: int


class TurnOnPayload(BaseModel):
    brightness: Optional[int] = None


class ColorPayload(BaseModel):
    rgb_color: Optional[List[int]] = None
    brightness: Optional[int] = None


class TriggerPayload(BaseModel):
    service: str
    domain: Optional[str] = None
    data: Optional[dict] = None


def _require_integration():
    data = read_config()
    adv = data.get('advanced', {}) or {}
    integration = adv.get('integration')
    if not integration or not integration.get('enabled'):
        raise HTTPException(status_code=503, detail='integration_missing')
    host = integration.get('host')
    token = integration.get('token')
    if not host or not token:
        raise HTTPException(status_code=503, detail='integration_missing')
    return integration


def _call_ha_service(domain: str, service: str, payload: dict | None = None):
    integration = _require_integration()
    host = integration.get('host')
    token = integration.get('token')
    body = payload or {}
    try:
        r = requests.post(
            host.rstrip('/') + f"/api/services/{domain}/{service}",
            headers={'Authorization': f"Bearer {token}", 'Content-Type': 'application/json'},
            json=body,
            timeout=8
        )
        r.raise_for_status()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"service_failed:{e}")


def _call_light_service(device_id: str, service: str, extra: dict | None = None):
    payload = {"entity_id": device_id}
    if extra:
        payload.update(extra)
    return _call_ha_service('light', service, payload)


@router.post("/{device_id}/brightness")
def set_brightness(device_id: str, payload: BrightnessPayload, token_payload=Depends(require_token)):
    return _call_light_service(device_id, 'turn_on', {"brightness": int(payload.brightness)})


@router.post("/{device_id}/toggle")
def toggle_device(device_id: str, token_payload=Depends(require_token)):
    return _call_light_service(device_id, 'toggle')


@router.post("/{device_id}/turn_on")
def turn_on_device(device_id: str, payload: TurnOnPayload | None = None, token_payload=Depends(require_token)):
    extra = {}
    if payload and payload.brightness is not None:
        extra['brightness'] = int(payload.brightness)
    return _call_light_service(device_id, 'turn_on', extra)


@router.post("/{device_id}/turn_off")
def turn_off_device(device_id: str, token_payload=Depends(require_token)):
    return _call_light_service(device_id, 'turn_off')


@router.post("/{device_id}/color")
def set_color(device_id: str, payload: ColorPayload, token_payload=Depends(require_token)):
    extra = {}
    if payload.rgb_color:
        rgb = list(payload.rgb_color)
        if len(rgb) != 3:
            raise HTTPException(status_code=400, detail='invalid_rgb_color')
        try:
            rgb = [max(0, min(255, int(c))) for c in rgb]
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail='invalid_rgb_color')
        extra['rgb_color'] = rgb
    if payload.brightness is not None:
        extra['brightness'] = int(payload.brightness)
    if not extra:
        raise HTTPException(status_code=400, detail='missing_parameters')
    return _call_light_service(device_id, 'turn_on', extra)


@router.post("/{entity_id}/trigger")
def trigger_entity(entity_id: str, payload: TriggerPayload, token_payload=Depends(require_token)):
    if not payload.service:
        raise HTTPException(status_code=400, detail='missing_service')
    domain = payload.domain
    if not domain:
        if '.' not in entity_id:
            raise HTTPException(status_code=400, detail='invalid_entity_id')
        domain = entity_id.split('.', 1)[0]
    data = {'entity_id': entity_id}
    if isinstance(payload.data, dict):
        data.update(payload.data)
    return _call_ha_service(domain, payload.service, data)
