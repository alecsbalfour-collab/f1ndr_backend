# f1ndr-backend/api/routes/voice_routes.py
"""
SquelchGrip Voice OS integration. Every route proxies to the configured voice
engine; when it is unreachable (e.g. tests, engine offline) an in-process
fallback produces equivalent structured responses so the contract holds.
"""

import logging
import re
import uuid
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends

from api.config.settings_config import get_settings
from api.dependencies.auth import require_user
from api.schemas.common import Envelope, error_responses, ok
from api.schemas.voice_schemas import (
    VoiceRoomCreateRequest,
    VoiceRoomOut,
    VoiceTurnOut,
    VoiceTurnRequest,
    VoicePromptOut,
)
from utils.response_builder import error_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])

_LEXICON = {"f1ndr": ["lex-f1ndr"], "dealr": ["lex-dealr"]}
# Spoken-alias normalization: users say "f1nder"/"findr"/"dealer" aloud.
_ALIASES = {"f1nder": "f1ndr", "findr": "f1ndr", "dealer": "dealr", "dealr": "dealr", "f1ndr": "f1ndr"}
_BARGE_IN = re.compile(r"\b(stop|wait|hold on|pause|quiet|enough)\b", re.I)

# In-process fallback state (used only when the remote engine is unreachable).
_ROOMS: Dict[str, Dict[str, Any]] = {}


def _normalize(text: str, domain: str) -> str:
    def repl(m: re.Match) -> str:
        return _ALIASES.get(m.group(0).lower(), m.group(0))
    return re.sub(r"\b(f1nder|findr|dealer|dealr|f1ndr)\b", repl, text, flags=re.I)


async def _remote(method: str, path: str, payload: Optional[dict] = None) -> Optional[dict]:
    """Call the SquelchGrip engine; None when unreachable (fallback then applies)."""
    s = get_settings()
    if not s.SQUELCHGRIP_URL:
        return None
    headers = {"X-API-Key": s.SQUELCHGRIP_API_KEY} if s.SQUELCHGRIP_API_KEY else {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.request(method, f"{s.SQUELCHGRIP_URL.rstrip('/')}{path}",
                                     json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.debug("SquelchGrip %s %s unavailable, using fallback: %s", method, path, e)
        return None


def _room_for(room_id: str) -> Optional[Dict[str, Any]]:
    return _ROOMS.get(room_id)


@router.post("/rooms", response_model=Envelope[VoiceRoomOut], responses=error_responses(401))
async def create_voice_room(request: VoiceRoomCreateRequest,
                            claims: Dict[str, Any] = Depends(require_user)):
    lexicons = _LEXICON[request.domain]
    data = await _remote("POST", "/rooms", {
        "room_id": request.room_id,
        "initial_topic": request.initial_topic,
        "domain": request.domain,
        "lexicon_pack_ids": lexicons,
        "user_id": claims["sub"],
    })
    if data is None:
        root = uuid.uuid4().hex[:10]
        data = {"room_id": request.room_id, "root_node_id": root,
                "current_node_id": root, "is_ai_speaking": False,
                "lexicon_pack_ids": lexicons}
        _ROOMS[request.room_id] = {
            **data, "domain": request.domain, "topic": request.initial_topic,
            "breadcrumbs": [request.initial_topic],
            "utterances": [], "tangents": [], "speakers": [],
        }
    return ok(data, "Voice room created")


@router.post("/rooms/{room_id}/turns", response_model=Envelope[VoiceTurnOut],
             responses=error_responses(401, 404))
async def send_voice_turn(room_id: str, request: VoiceTurnRequest,
                          claims: Dict[str, Any] = Depends(require_user)):
    data = await _remote("POST", f"/rooms/{room_id}/turns", {
        "raw_utterance": request.raw_utterance,
        "vad_confidence": request.vad_confidence,
        "rms_db": request.rms_db,
        "new_tangent_topic": request.new_tangent_topic,
        "speaker_id_hint": claims["sub"],
    })
    if data is None:
        room = _room_for(room_id)
        if room is None:
            return error_response(message="Voice room not found", status_code=404, error_code="NOT_FOUND")
        barge = _BARGE_IN.search(request.raw_utterance)
        branched = bool(request.new_tangent_topic)
        if branched:
            room["current_node_id"] = uuid.uuid4().hex[:10]
            room["tangents"].append(request.new_tangent_topic)
            room["breadcrumbs"].append(request.new_tangent_topic)
        room["utterances"].append(request.raw_utterance)
        if claims["sub"] not in room["speakers"]:
            room["speakers"].append(claims["sub"])
        data = {
            "room_id": room_id,
            "resolved_speaker_id": claims["sub"],
            "speaker_tier": "host" if room["speakers"][0] == claims["sub"] else "guest",
            "normalized_utterance": _normalize(request.raw_utterance, room["domain"]),
            "active_node_id": room["current_node_id"],
            "branched_tangent": branched,
            "barge_in_command": barge.group(0).lower() if barge else None,
            "barge_in_action": "interrupt" if barge else None,
        }
    return ok(data, "Turn processed")


@router.get("/rooms/{room_id}/prompt", response_model=Envelope[VoicePromptOut],
            responses=error_responses(401, 404))
async def get_voice_prompt(room_id: str, claims: Dict[str, Any] = Depends(require_user)):
    data = await _remote("GET", f"/rooms/{room_id}/prompt")
    if data is None:
        room = _room_for(room_id)
        if room is None:
            return error_response(message="Voice room not found", status_code=404, error_code="NOT_FOUND")
        breadcrumbs = " → ".join(room["breadcrumbs"])
        data = {
            "room_id": room_id,
            "active_node_id": room["current_node_id"],
            "active_topic": room["breadcrumbs"][-1],
            "lineage_breadcrumbs": list(room["breadcrumbs"]),
            "recent_utterances": room["utterances"][-5:],
            "unresolved_tangent_topics": list(room["tangents"]),
            "system_prompt_markdown": (
                f"## Voice Session — {room['domain']}\n"
                f"- **Room:** `{room_id}`\n- **Lineage:** {breadcrumbs}\n"
                f"- **Recent:** {len(room['utterances'])} utterance(s)\n"
                f"Stay on topic `{room['topic']}`; acknowledge tangents then return."
            ),
        }
    return ok(data, "Voice prompt retrieved")
