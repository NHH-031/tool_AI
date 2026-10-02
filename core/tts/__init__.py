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

# EdgeTTSProvider is exported conditionally if edge_tts is available
try:
    from .edge import EdgeTTSProvider
    __all__.append("EdgeTTSProvider")
except ImportError:
    pass
