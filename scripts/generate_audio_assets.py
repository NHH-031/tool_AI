"""
Audio Asset Generator for AI Whiteboard Video Studio.
Generates high-quality royalty-free background music (BGM) tracks
and whiteboard drawing sound effects (SFX) using procedural acoustic synthesis.
"""

from __future__ import annotations

import math
from pathlib import Path
import numpy as np
import av


SAMPLE_RATE = 44100


def save_mp3(audio_data: np.ndarray, sample_rate: int, out_path: Path, bit_rate: int = 192000):
    """Lưu numpy audio array (float32, shape (samples, channels) hoặc (samples,)) ra MP3."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(out_path), mode="w", format="mp3")
    channels = 2 if audio_data.ndim > 1 and audio_data.shape[1] == 2 else 1
    stream = container.add_stream("libmp3lame", rate=sample_rate)
    stream.bit_rate = bit_rate
    layout = "stereo" if channels == 2 else "mono"
    stream.layout = layout
    stream.format = "fltp"

    if channels == 2:
        if audio_data.shape[0] != 2:
            audio_data = audio_data.T
    else:
        if audio_data.ndim == 2:
            audio_data = audio_data.squeeze()
        audio_data = audio_data.reshape(1, -1)

    # Normalize to prevent clipping, leaving 1.5dB headroom
    peak = np.max(np.abs(audio_data))
    if peak > 0.001:
        audio_data = (audio_data / peak) * 0.85

    audio_data = np.ascontiguousarray(audio_data, dtype=np.float32)
    chunk_size = 1152
    num_samples = audio_data.shape[1]

    for i in range(0, num_samples, chunk_size):
        chunk = audio_data[:, i : i + chunk_size]
        if chunk.shape[1] < chunk_size:
            pad = np.zeros((channels, chunk_size - chunk.shape[1]), dtype=np.float32)
            chunk = np.hstack([chunk, pad])
        frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout=layout)
        frame.rate = sample_rate
        frame.pts = i
        for pkt in stream.encode(frame):
            container.mux(pkt)

    for pkt in stream.encode(None):
        container.mux(pkt)
    container.close()
    print(f"  [OK] Saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


# =========================================================================
# SYNTHESIS INSTRUMENT PRIMITIVES
# =========================================================================

def note_freq(midi_note: float) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))


def synth_kick(sr: int, duration: float = 0.4) -> np.ndarray:
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Pitch envelope drops from 140Hz down to 45Hz
    freq = 45.0 + 95.0 * np.exp(-t * 28.0)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t * 9.0)
    sig = np.sin(phase) * env
    # Add click transient
    click = np.random.randn(n_samples) * np.exp(-t * 120.0) * 0.3
    return (sig + click).astype(np.float32)


def synth_snare(sr: int, duration: float = 0.35) -> np.ndarray:
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Tonal body
    body = np.sin(2 * np.pi * 185.0 * t) * np.exp(-t * 18.0)
    # White noise snare rattle
    noise = np.random.randn(n_samples)
    # Simple highpass
    noise_hp = noise - np.convolve(noise, np.ones(5) / 5, mode="same")
    noise_env = np.exp(-t * 14.0)
    sig = body * 0.4 + noise_hp * noise_env * 0.6
    return sig.astype(np.float32)


def synth_hihat(sr: int, duration: float = 0.12, open_hat: bool = False) -> np.ndarray:
    decay = 18.0 if open_hat else 45.0
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    noise = np.random.randn(n_samples)
    # Differentiating gives bright metallic highpass
    hp = np.diff(noise, prepend=0)
    hp2 = np.diff(hp, prepend=0)
    env = np.exp(-t * decay)
    return (hp2 * env * 0.25).astype(np.float32)


def synth_marimba_pluck(sr: int, midi_note: float, duration: float = 1.2) -> np.ndarray:
    """Marimba / wooden bar sound with rapid transient and warm woody resonance."""
    f0 = note_freq(midi_note)
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Fundamental + 4th harmonic overtone typical of rosewood marimba bars
    f1 = f0 * 3.85
    env0 = np.exp(-t * (4.0 + f0 * 0.008))
    env1 = np.exp(-t * (18.0 + f0 * 0.02))
    # Woody mallet click at onset
    click = np.random.randn(n_samples) * np.exp(-t * 180.0) * 0.4
    sig = (
        np.sin(2 * np.pi * f0 * t) * env0 * 0.7
        + np.sin(2 * np.pi * f1 * t) * env1 * 0.25
        + click
    )
    return sig.astype(np.float32)


def synth_electric_piano_note(sr: int, midi_note: float, duration: float = 2.0) -> np.ndarray:
    """Rhodes / Wurlitzer style warm electric piano chord note with gentle vibrato."""
    f0 = note_freq(midi_note)
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Tremolo & subtle pitch vibrato
    vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 5.2 * t)
    tremolo = 1.0 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    env = np.exp(-t * (1.2 + f0 * 0.002))
    # Pure bell tine + warm body
    sig = (
        np.sin(2 * np.pi * f0 * vibrato * t) * 0.65
        + np.sin(2 * np.pi * 2 * f0 * vibrato * t) * 0.25
        + np.sin(2 * np.pi * 3 * f0 * vibrato * t) * 0.08
    ) * env * tremolo
    return sig.astype(np.float32)


def synth_ukulele_strum(sr: int, midi_note: float, duration: float = 1.5) -> np.ndarray:
    """Plucked nylon acoustic ukulele string."""
    f0 = note_freq(midi_note)
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    env = np.exp(-t * (3.5 + f0 * 0.005))
    sig = (
        np.sin(2 * np.pi * f0 * t) * 0.6
        + np.sin(2 * np.pi * 2 * f0 * t) * 0.25
        + np.sin(2 * np.pi * 3 * f0 * t) * 0.1
        + np.sin(2 * np.pi * 4 * f0 * t) * 0.05
    ) * env
    return sig.astype(np.float32)


# =========================================================================
# 5 BGM TRACK GENERATORS (Duration ~ 60s - 90s, perfectly loopable)
# =========================================================================

def generate_lofi_chill(sr: int = SAMPLE_RATE, duration_sec: float = 64.0) -> np.ndarray:
    """Late Night Whiteboard Lofi (85 BPM, Warm Rhodes Chords + Chill Boom-Bap + Vinyl Crackle)."""
    bpm = 85.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4.0
    total_samples = int(sr * duration_sec)
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # 1. Vinyl crackle / tape hiss bed
    noise = np.random.randn(total_samples).astype(np.float32) * 0.015
    crackle_hits = np.random.rand(total_samples) > 0.9997
    crackle = np.zeros(total_samples, dtype=np.float32)
    crackle[crackle_hits] = np.random.randn(np.sum(crackle_hits)) * 0.08
    left += noise + crackle
    right += noise + crackle

    # Chords: Cmaj7 (60, 64, 67, 71), Am7 (57, 60, 64, 67), Dm7 (62, 65, 69, 72), G7 (55, 59, 62, 65)
    chord_progression = [
        [60, 64, 67, 71],  # Cmaj7
        [57, 60, 64, 67],  # Am7
        [62, 65, 69, 72],  # Dm7
        [55, 59, 62, 65],  # G7
    ]
    bass_notes = [36, 33, 38, 31]  # Root notes for bass

    num_bars = int(duration_sec / bar_dur)
    for bar_idx in range(num_bars):
        bar_start_s = bar_idx * bar_dur
        chord = chord_progression[bar_idx % len(chord_progression)]
        root = bass_notes[bar_idx % len(bass_notes)]

        # Rhodes chords on beat 1 and beat 3
        for beat_offset in [0.0, beat_dur * 2.0]:
            chord_time = bar_start_s + beat_offset
            chord_start = int(chord_time * sr)
            for idx, note in enumerate(chord):
                n_sig = synth_electric_piano_note(sr, note, duration=beat_dur * 2.2)
                end = min(total_samples, chord_start + len(n_sig))
                chunk_len = end - chord_start
                if chunk_len > 0:
                    pan_l = 0.5 - 0.2 * (idx / len(chord))
                    pan_r = 0.5 + 0.2 * (idx / len(chord))
                    left[chord_start:end] += n_sig[:chunk_len] * pan_l * 0.45
                    right[chord_start:end] += n_sig[:chunk_len] * pan_r * 0.45

        # Sub-bass line
        bass_start = int(bar_start_s * sr)
        f_bass = note_freq(root)
        t_bass = np.linspace(0, bar_dur, int(sr * bar_dur), endpoint=False)
        bass_sig = (
            np.sin(2 * np.pi * f_bass * t_bass) * 0.5
            + np.sin(2 * np.pi * 2 * f_bass * t_bass) * 0.15
        ) * np.exp(-t_bass * 0.4)
        end_b = min(total_samples, bass_start + len(bass_sig))
        left[bass_start:end_b] += bass_sig[: end_b - bass_start] * 0.5
        right[bass_start:end_b] += bass_sig[: end_b - bass_start] * 0.5

        # Drums for the bar
        for beat in range(4):
            t_beat = bar_start_s + beat * beat_dur
            idx_beat = int(t_beat * sr)

            # Kick on 1 and 2.5
            if beat == 0 or beat == 2:
                k = synth_kick(sr)
                e = min(total_samples, idx_beat + len(k))
                left[idx_beat:e] += k[: e - idx_beat] * 0.65
                right[idx_beat:e] += k[: e - idx_beat] * 0.65
            if beat == 2:
                # offbeat kick
                k_off_idx = int((t_beat + beat_dur * 0.5) * sr)
                k = synth_kick(sr)
                e = min(total_samples, k_off_idx + len(k))
                left[k_off_idx:e] += k[: e - k_off_idx] * 0.5
                right[k_off_idx:e] += k[: e - k_off_idx] * 0.5

            # Snare on 2 and 4
            if beat == 1 or beat == 3:
                sn = synth_snare(sr)
                e = min(total_samples, idx_beat + len(sn))
                left[idx_beat:e] += sn[: e - idx_beat] * 0.5
                right[idx_beat:e] += sn[: e - idx_beat] * 0.5

            # Hi-hat on every 8th note
            for sub in [0.0, beat_dur * 0.5]:
                h_idx = int((t_beat + sub) * sr)
                hh = synth_hihat(sr, open_hat=(beat == 3 and sub > 0))
                e = min(total_samples, h_idx + len(hh))
                left[h_idx:e] += hh[: e - h_idx] * 0.25
                right[h_idx:e] += hh[: e - h_idx] * 0.28

    return np.column_stack([left, right])


def generate_whimsical_play(sr: int = SAMPLE_RATE, duration_sec: float = 64.0) -> np.ndarray:
    """Playful Forest Marimba (124 BPM, Bouncy Pentatonic Marimba + Woodblock + Pizzicato)."""
    bpm = 124.0
    beat_dur = 60.0 / bpm
    total_samples = int(sr * duration_sec)
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # Pentatonic melody motives
    scale = [60, 62, 64, 67, 69, 72, 74, 76]  # C Major pentatonic
    pattern = [0, 2, 4, 2, 3, 5, 4, 1, 0, 4, 3, 2, 5, 4, 2, 0]

    step_dur = beat_dur * 0.5  # 8th notes
    total_steps = int(duration_sec / step_dur)

    for step in range(total_steps):
        t_step = step * step_dur
        idx_step = int(t_step * sr)
        note_idx = pattern[step % len(pattern)]
        note = scale[note_idx]

        m_sig = synth_marimba_pluck(sr, note, duration=0.8)
        end = min(total_samples, idx_step + len(m_sig))
        c_len = end - idx_step
        if c_len > 0:
            pan = 0.3 if (step % 2 == 0) else 0.7
            left[idx_step:end] += m_sig[:c_len] * (1.0 - pan) * 0.5
            right[idx_step:end] += m_sig[:c_len] * pan * 0.5

        # Light woodblock / percussion on main beats
        if step % 2 == 0:
            wb_freq = 900.0 if ((step // 2) % 2 == 0) else 1350.0
            t_wb = np.linspace(0, 0.08, int(sr * 0.08), endpoint=False)
            wb_sig = np.sin(2 * np.pi * wb_freq * t_wb) * np.exp(-t_wb * 60.0) * 0.25
            end_wb = min(total_samples, idx_step + len(wb_sig))
            left[idx_step:end_wb] += wb_sig[: end_wb - idx_step] * 0.2
            right[idx_step:end_wb] += wb_sig[: end_wb - idx_step] * 0.2

    # Bassline on quarter notes
    quarter_steps = int(duration_sec / beat_dur)
    bass_scale = [48, 48, 45, 43, 41, 41, 43, 45]
    for q in range(quarter_steps):
        t_q = q * beat_dur
        idx_q = int(t_q * sr)
        b_note = bass_scale[q % len(bass_scale)]
        b_sig = synth_marimba_pluck(sr, b_note, duration=1.0)
        end = min(total_samples, idx_q + len(b_sig))
        left[idx_q:end] += b_sig[: end - idx_q] * 0.4
        right[idx_q:end] += b_sig[: end - idx_q] * 0.4

    return np.column_stack([left, right])


def generate_acoustic_uplift(sr: int = SAMPLE_RATE, duration_sec: float = 64.0) -> np.ndarray:
    """Sunny Morning Ukulele (110 BPM, Strummed Ukulele + Cheerful Acoustic Whistle)."""
    bpm = 110.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4.0
    total_samples = int(sr * duration_sec)
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # Chords: C (60, 64, 67, 72), G (59, 62, 67, 71), Am (57, 60, 64, 69), F (57, 60, 65, 69)
    chords = [
        [60, 64, 67, 72],
        [59, 62, 67, 71],
        [57, 60, 64, 69],
        [57, 60, 65, 69],
    ]

    num_bars = int(duration_sec / bar_dur)
    for bar_idx in range(num_bars):
        bar_start_s = bar_idx * bar_dur
        chord = chords[bar_idx % len(chords)]

        # Strumming pattern: down, down-up, up-down-up
        strum_subbeats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        for sb in strum_subbeats:
            t_strum = bar_start_s + sb * beat_dur
            idx_s = int(t_strum * sr)
            # Strum each string slightly delayed by 12ms (raking)
            for str_idx, note in enumerate(chord):
                n_delay = int(str_idx * 0.012 * sr)
                cur_idx = idx_s + n_delay
                if cur_idx < total_samples:
                    u_sig = synth_ukulele_strum(sr, note, duration=0.6)
                    end = min(total_samples, cur_idx + len(u_sig))
                    left[cur_idx:end] += u_sig[: end - cur_idx] * 0.18
                    right[cur_idx:end] += u_sig[: end - cur_idx] * 0.22

        # Handclaps on beats 2 and 4
        for beat in [1, 3]:
            t_clap = bar_start_s + beat * beat_dur
            idx_clap = int(t_clap * sr)
            t_c = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
            clap_sig = np.random.randn(len(t_c)) * np.exp(-t_c * 40.0) * 0.35
            end = min(total_samples, idx_clap + len(clap_sig))
            left[idx_clap:end] += clap_sig[: end - idx_clap]
            right[idx_clap:end] += clap_sig[: end - idx_clap]

    return np.column_stack([left, right])


def generate_corporate_inspire(sr: int = SAMPLE_RATE, duration_sec: float = 64.0) -> np.ndarray:
    """Inspiring Innovation (118 BPM, Crisp Acoustic Piano Pattern + Swelling Ambient Strings)."""
    bpm = 118.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4.0
    total_samples = int(sr * duration_sec)
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # Piano 8th note arpeggios
    # Progression: F - G - Am - C
    chords = [
        [53, 57, 60, 65],  # F
        [55, 59, 62, 67],  # G
        [57, 60, 64, 69],  # Am
        [48, 52, 55, 60],  # C
    ]

    num_bars = int(duration_sec / bar_dur)
    for bar_idx in range(num_bars):
        bar_start_s = bar_idx * bar_dur
        chord = chords[bar_idx % len(chords)]

        for eighth in range(8):
            t_note = bar_start_s + eighth * (beat_dur * 0.5)
            idx_note = int(t_note * sr)
            pitch = chord[eighth % len(chord)] + 12  # Higher register piano
            p_sig = synth_electric_piano_note(sr, pitch, duration=0.7)
            end = min(total_samples, idx_note + len(p_sig))
            left[idx_note:end] += p_sig[: end - idx_note] * 0.25
            right[idx_note:end] += p_sig[: end - idx_note] * 0.28

        # Swelling warm string pad over the whole bar
        t_bar = np.linspace(0, bar_dur, int(sr * bar_dur), endpoint=False)
        pad_env = (np.sin(np.pi * t_bar / bar_dur) ** 2) * 0.35
        root_f = note_freq(chord[0])
        pad_sig = (
            np.sin(2 * np.pi * root_f * t_bar) * 0.5
            + np.sin(2 * np.pi * root_f * 1.5 * t_bar) * 0.3
            + np.sin(2 * np.pi * root_f * 2.0 * t_bar) * 0.2
        ) * pad_env
        idx_b = int(bar_start_s * sr)
        end_b = min(total_samples, idx_b + len(pad_sig))
        left[idx_b:end_b] += pad_sig[: end_b - idx_b]
        right[idx_b:end_b] += pad_sig[: end_b - idx_b]

    return np.column_stack([left, right])


def generate_ambient_minimal(sr: int = SAMPLE_RATE, duration_sec: float = 64.0) -> np.ndarray:
    """Subtle Clarity Wave (70 BPM, Zen Ambient Drone, Evolving Stereo Harmonics)."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    # Detuned fundamental drone at D (146.8 Hz)
    f0 = 146.83
    # Gentle breathing LFO (0.1 Hz)
    lfo1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t)
    lfo2 = 0.5 + 0.5 * np.cos(2 * np.pi * 0.05 * t)

    drone_l = (
        np.sin(2 * np.pi * f0 * t) * 0.35
        + np.sin(2 * np.pi * (f0 * 1.5 + 0.2) * t) * 0.25 * lfo1
        + np.sin(2 * np.pi * (f0 * 2.0 - 0.3) * t) * 0.15 * lfo2
        + np.sin(2 * np.pi * (f0 * 3.0) * t) * 0.08
    )
    drone_r = (
        np.sin(2 * np.pi * (f0 + 0.4) * t) * 0.35
        + np.sin(2 * np.pi * (f0 * 1.5 - 0.2) * t) * 0.25 * lfo2
        + np.sin(2 * np.pi * (f0 * 2.0 + 0.3) * t) * 0.15 * lfo1
        + np.sin(2 * np.pi * (f0 * 3.0) * t) * 0.08
    )

    # Occasional singing bowl / glass chime strikes every 8 seconds
    chime_interval = int(sr * 8.0)
    for c_start in range(0, total_samples - int(sr * 4.0), chime_interval):
        t_c = np.linspace(0, 4.0, int(sr * 4.0), endpoint=False)
        c_env = np.exp(-t_c * 0.8)
        chime = (
            np.sin(2 * np.pi * 880.0 * t_c) * 0.15
            + np.sin(2 * np.pi * 1760.0 * t_c) * 0.08
            + np.sin(2 * np.pi * 2640.0 * t_c) * 0.04
        ) * c_env
        end = c_start + len(chime)
        drone_l[c_start:end] += chime * 0.4
        drone_r[c_start:end] += chime * 0.6

    return np.column_stack([drone_l, drone_r]).astype(np.float32)


# =========================================================================
# 3 DRAWING SFX GENERATORS
# =========================================================================

def generate_marker_draw_sfx(sr: int = SAMPLE_RATE, duration_sec: float = 10.0) -> np.ndarray:
    """Whiteboard Marker Friction SFX (Squeaks, felt-tip strokes on smooth whiteboard)."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    np.random.seed(101)
    noise = np.random.randn(total_samples).astype(np.float32)
    # Bandpass around 2500Hz - 4500Hz
    diff1 = np.diff(noise, prepend=0)
    diff2 = np.diff(diff1, prepend=0)
    marker_texture = diff1 + 0.7 * diff2

    # Natural drawing cadence: ~3.2 strokes per second with micro-pauses
    stroke_rate = 3.2
    stroke_cadence = (0.5 + 0.5 * np.cos(2 * np.pi * stroke_rate * t)) ** 2.5

    # Marker friction squeak (dry erase marker tip squeak on porcelain/melamine board)
    squeak_freq = 2800.0 + 800.0 * np.sin(2 * np.pi * 1.5 * t)
    squeak = np.sin(2 * np.pi * squeak_freq * t) * (np.random.rand(total_samples) > 0.985) * 0.2

    combined = (marker_texture * 0.7 + squeak) * stroke_cadence
    # Smooth start and end
    fade_len = int(sr * 0.05)
    fade = np.linspace(0, 1, fade_len)
    combined[:fade_len] *= fade
    combined[-fade_len:] *= fade[::-1]

    return combined.astype(np.float32)


def generate_pencil_sketch_sfx(sr: int = SAMPLE_RATE, duration_sec: float = 10.0) -> np.ndarray:
    """Graphite Pencil on Paper SFX (Fine granular paper tooth friction, rapid hatching)."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    np.random.seed(202)
    noise = np.random.randn(total_samples).astype(np.float32)
    # High frequency paper tooth texture
    d = np.diff(noise, prepend=0)
    
    # Rapid cross-hatching strokes (4.8 strokes/sec)
    stroke_cadence = (0.5 + 0.5 * np.sin(2 * np.pi * 4.8 * t)) ** 3.0
    pressure_variation = 0.7 + 0.3 * np.sin(2 * np.pi * 0.8 * t)

    combined = d * stroke_cadence * pressure_variation
    fade_len = int(sr * 0.05)
    fade = np.linspace(0, 1, fade_len)
    combined[:fade_len] *= fade
    combined[-fade_len:] *= fade[::-1]

    return combined.astype(np.float32)


def generate_chalk_board_sfx(sr: int = SAMPLE_RATE, duration_sec: float = 10.0) -> np.ndarray:
    """Chalk on Slate Board SFX (Grainy porous scrape with resonant low-mid drag)."""
    total_samples = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)

    np.random.seed(303)
    noise = np.random.randn(total_samples).astype(np.float32)
    # Lower frequency scrape + chalk drag
    scrape = np.convolve(noise, np.ones(8) / 8, mode="same")
    chalk_tone = np.sin(2 * np.pi * 1250.0 * t) * (np.random.rand(total_samples) > 0.99) * 0.3

    stroke_cadence = (0.5 + 0.5 * np.cos(2 * np.pi * 2.2 * t)) ** 2.0
    combined = (scrape * 0.8 + chalk_tone) * stroke_cadence
    fade_len = int(sr * 0.05)
    fade = np.linspace(0, 1, fade_len)
    combined[:fade_len] *= fade
    combined[-fade_len:] *= fade[::-1]

    return combined.astype(np.float32)


# =========================================================================
# MAIN EXECUTION
# =========================================================================

def main():
    root = Path(__file__).resolve().parent.parent
    music_dir = root / "assets" / "audio" / "music"
    sfx_dir = root / "assets" / "audio" / "sfx"

    music_dir.mkdir(parents=True, exist_ok=True)
    sfx_dir.mkdir(parents=True, exist_ok=True)

    print("=== Sinh kho nhạc nền BGM (Task 1.1) ===")
    tracks = [
        ("lofi_chill.mp3", generate_lofi_chill, 64.0),
        ("whimsical_play.mp3", generate_whimsical_play, 64.0),
        ("acoustic_uplift.mp3", generate_acoustic_uplift, 64.0),
        ("corporate_inspire.mp3", generate_corporate_inspire, 64.0),
        ("ambient_minimal.mp3", generate_ambient_minimal, 64.0),
    ]

    for filename, gen_fn, dur in tracks:
        p = music_dir / filename
        print(f"Generating {filename} ({dur}s)...")
        audio = gen_fn(sr=SAMPLE_RATE, duration_sec=dur)
        save_mp3(audio, SAMPLE_RATE, p)

    print("\n=== Sinh bộ hiệu ứng âm thanh vẽ bút SFX (Task 1.3) ===")
    sfx_tracks = [
        ("marker_draw.mp3", generate_marker_draw_sfx, 12.0),
        ("pencil_sketch.mp3", generate_pencil_sketch_sfx, 12.0),
        ("chalk_board.mp3", generate_chalk_board_sfx, 12.0),
    ]

    for filename, gen_fn, dur in sfx_tracks:
        p = sfx_dir / filename
        print(f"Generating SFX {filename} ({dur}s)...")
        audio = gen_fn(sr=SAMPLE_RATE, duration_sec=dur)
        save_mp3(audio, SAMPLE_RATE, p)

    print("\n[SUCCESS] Hoàn tất sinh toàn bộ audio assets cho Phase 1!")


if __name__ == "__main__":
    main()
