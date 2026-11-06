"""SquelchGrip Voice OS request/response models."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

VoiceDomain = Literal["f1ndr", "dealr"]


class VoiceRoomCreateRequest(BaseModel):
    room_id: str = Field(..., min_length=1, max_length=128)
    initial_topic: str = Field(..., min_length=1, max_length=200)
    domain: VoiceDomain = "f1ndr"


class VoiceRoomOut(BaseModel):
    room_id: str
    root_node_id: str
    current_node_id: str
    is_ai_speaking: bool
    lexicon_pack_ids: List[str]


class VoiceTurnRequest(BaseModel):
    raw_utterance: str = Field(..., min_length=1, max_length=4000)
    vad_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    rms_db: float = -20.0
    new_tangent_topic: Optional[str] = Field(None, max_length=200)


class VoiceTurnOut(BaseModel):
    room_id: str
    resolved_speaker_id: str
    speaker_tier: str
    normalized_utterance: str
    active_node_id: str
    branched_tangent: bool
    barge_in_command: Optional[str] = None
    barge_in_action: Optional[str] = None


class VoicePromptOut(BaseModel):
    room_id: str
    active_node_id: str
    active_topic: str
    lineage_breadcrumbs: List[str]
    recent_utterances: List[str]
    unresolved_tangent_topics: List[str]
    system_prompt_markdown: str
