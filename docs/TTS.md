# TTS & Narration Timing Subsystem

## 1. Overview & Architectural Principles

The **TTS & Narration Timing Subsystem** connects narrative video scripts with real acoustic execution.
Key design principles:
- **Provider Agnostic**: The architecture does not hard-code a single provider. All engines adhere to the [`TTSProvider`](file:///d:/Tool/core/tts/base.py) abstract interface.
- **Strict Timing Integrity**: Word-level and phoneme-level alignments are prioritized. When a provider lacks native word boundary timestamps, the system transparently activates the [`TimingEstimator`](file:///d:/Tool/core/tts/timing.py) and **explicitly flags** `is_fallback = True` and `timing_level = "fallback_estimated"`. The engine **never pretends** estimated timestamps are native ground truth.
- **Resilience & Fault Tolerance**: Built-in retry and failover capabilities through [`ResilientTTSProvider`](file:///d:/Tool/core/tts/resilient.py).
- **Deterministic Testing**: Powered by an isolated [`MockTTSProvider`](file:///d:/Tool/core/tts/mock.py) that generates playable PCM audio and configurable word/fallback timings without external network dependencies.

```
                    ┌─────────────────────────────────┐
                    │        Production Script        │
                    │   (Narration Segments / Text)   │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │   NarrationAgent    │
                          └──────────┬──────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │           TTSProvider           │
                    │   generate() / get_timing()     │
                    └────────────────┬────────────────┘
                                     │
             ┌───────────────────────┼───────────────────────┐
             ▼                       ▼                       ▼
   ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
   │  MockTTSProvider  │   │  EdgeTTSProvider  │   │ResilientTTSProvider│
   │ (Deterministic)   │   │  (Neural Cloud)   │   │ (Retry + Failover)│
   └─────────┬─────────┘   └─────────┬─────────┘   └───────────────────┘
             │                       │
             └───────────┬───────────┘
                         ▼
             ┌───────────────────────┐
             │ Word Timing Available?│
             └───────────┬───────────┘
                    YES  │   NO
             ┌───────────┘   └───────────┐
             ▼                           ▼
   ┌───────────────────┐       ┌───────────────────┐
   │ Native WordTiming │       │  TimingEstimator  │
   │is_fallback=False  │       │ is_fallback=True  │
   │timing_level="word"│       │fallback_estimated │
   └─────────┬─────────┘       └─────────┬─────────┘
             │                           │
             └───────────┬───────────────┘
                         ▼
             ┌───────────────────────┐
             │    TTSAudioResult     │
             │- audio_bytes          │
             │- duration             │
             │- timing               │
             │- metadata             │
             └───────────────────────┘
```

---

## 2. Voice Configuration Model

Defined in [`core/schemas/tts.py`](file:///d:/Tool/core/schemas/tts.py):

```python
class VoiceConfig(BaseModel):
    voice_id: str = Field(default="vi-VN-HoaiMyNeural", alias="voiceId")
    language: str = Field(default="vi-VN")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=0.0, ge=-50.0, le=50.0)
```

- Both `voiceId` (camelCase) and `voice_id` (snake_case) are supported.
- `speed`: Scale factor where $1.0$ is normal reading cadence, $>1.0$ accelerates, $<1.0$ decelerates.
- `pitch`: Pitch offset in Hertz or semitones.

---

## 3. Core Provider Interface

The abstract base class [`TTSProvider`](file:///d:/Tool/core/tts/base.py) enforces 5 primary methods:

```python
class TTSProvider(ABC):
    @abstractmethod
    async def generate(self, text: str, voice_config: Optional[VoiceConfig] = None) -> TTSAudioResult:
        """Synthesize audio bytes, calculate duration, and attach timing."""
        ...

    @abstractmethod
    async def get_duration(self, text: str, voice_config: Optional[VoiceConfig] = None) -> float:
        """Calculate spoken audio duration in seconds."""
        ...

    @abstractmethod
    async def get_timing(self, text: str, voice_config: Optional[VoiceConfig] = None) -> NarrationTiming:
        """Retrieve word/sentence timing structure."""
        ...

    @abstractmethod
    async def preview(self, text: str, voice_config: Optional[VoiceConfig] = None) -> TTSAudioResult:
        """Fast preview generation (e.g. first sentence only)."""
        ...

    @abstractmethod
    def get_supported_voices(self) -> List[str]:
        """Return list of valid voice identifiers."""
        ...
```

---

## 4. Audio Output & Result Model

Synthesized results are returned as a [`TTSAudioResult`](file:///d:/Tool/core/schemas/tts.py):

- `audio_bytes`: Raw binary audio data (PCM WAV or MP3).
- `duration`: Float duration in seconds.
- `duration_ms`: Integer duration in milliseconds.
- `format`: Audio container format (`"wav"`, `"mp3"`).
- `sample_rate`: Sampling frequency (default: 24,000 Hz).
- `channels`: Channel layout ($1 = \text{mono}$, $2 = \text{stereo}$).
- `voice_config`: The exact configuration applied during synthesis.
- `timing`: Optional [`NarrationTiming`](file:///d:/Tool/core/schemas/tts.py) object containing word and sentence schedules.
- `metadata`: Dictionary containing provider-specific instrumentation.
- `save_to_file(path)`: Built-in utility to persist audio bytes to disk and update `audio_path`.

---

## 5. Timing Hierarchy & Fallback Policy

### Ground-Truth Rule
> **Under NO circumstances should the engine disguise an estimated timestamp as native ground truth.**

### Hierarchy Levels
1. **Word Timing (`timing_level = "word"`, `is_fallback = False`)**:
   - Each word has precise start and end timestamps recorded directly from acoustic alignment or neural synthesis events.
2. **Fallback Estimated Timing (`timing_level = "fallback_estimated"`, `is_fallback = True`)**:
   - Generated by [`TimingEstimator`](file:///d:/Tool/core/tts/timing.py).
   - Evaluates linguistic features: sentence boundaries, character counts, punctuation pause weights (comma pauses, sentence-ending periods).
   - Normalizes word durations to match the total measured audio length.
   - Sets `confidence = 0.5` on all estimated words and specifies `fallback_reason`.

---

## 6. Provider Implementations

### `MockTTSProvider` ([`core/tts/mock.py`](file:///d:/Tool/core/tts/mock.py))
- Generates real playable 16-bit mono 24kHz PCM WAV bytes using Python's standard `wave` and `struct` modules with gentle window envelope smoothing.
- Configurable `supports_word_timing = True | False` to verify both native and fallback pipelines.
- Configurable `fail_times` to simulate transient network timeouts and test retry logic.
- Voice validation raising [`InvalidVoiceError`](file:///d:/Tool/core/tts/base.py) upon unrecognized voice IDs.

### `EdgeTTSProvider` ([`core/tts/edge.py`](file:///d:/Tool/core/tts/edge.py))
- Production-grade integration with Microsoft Edge Neural Cloud TTS.
- Supported voices:
  - Vietnamese: `vi-VN-HoaiMyNeural` (Female), `vi-VN-NamMinhNeural` (Male).
  - English: `en-US-AriaNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-SoniaNeural`.
- Rate and pitch string formatting (`+10%`, `-15Hz`).
- Stream decoder extracting `WordBoundary` events with automatic fallback to [`TimingEstimator`](file:///d:/Tool/core/tts/timing.py) if boundaries are missing.

### `ResilientTTSProvider` ([`core/tts/resilient.py`](file:///d:/Tool/core/tts/resilient.py))
- Transparent decorator wrapping any primary provider.
- Automatic exponential backoff retries (`max_retries = 2`, `initial_delay = 0.05s`).
- Immediate failover to `fallback_provider` if the primary service becomes permanently unavailable.
