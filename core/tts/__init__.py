from __future__ import annotations

from core.schemas.tts import (
    NarrationTiming,
    SentenceTiming,
    TTSAudioResult,
    VoiceConfig,
    WordTiming,
)
from .base import (
    InvalidVoiceError,
    TTSConnectionError,
    TTSError,
    TTSProvider,
    TTSSynthesisError,
)
from .mock import MockTTSProvider
from .timing import TimingEstimator
from .resilient import ResilientTTSProvider

__all__ = [
    "VoiceConfig",
    "WordTiming",
    "SentenceTiming",
    "NarrationTiming",
    "TTSAudioResult",
    "TTSError",
    "InvalidVoiceError",
    "TTSConnectionError",
    "TTSSynthesisError",
    "TTSProvider",
    "MockTTSProvider",
    "TimingEstimator",
    "ResilientTTSProvider",
]

try:
    from .edge import EdgeTTSProvider
    __all__.append("EdgeTTSProvider")
except ImportError:
    pass

try:
    from .local import LocalTTSProvider
    __all__.append("LocalTTSProvider")
except ImportError:
    pass

try:
    from .elevenlabs import ElevenLabsTTSProvider, ELEVENLABS_VOICE_MAP
    __all__.extend(["ElevenLabsTTSProvider", "ELEVENLABS_VOICE_MAP"])
except ImportError:
    pass

