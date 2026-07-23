"""
GRE Pace Trainer — Sound Asset Generator

Generates 6 notification WAV files into assets/sounds/ using only
the Python standard library (struct, math, wave).

Usage:
    python generate_sounds.py
"""

import math
import os
import struct
import wave

SAMPLE_RATE = 44100
MAX_AMP = 32767  # 16-bit signed max

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")


# ── Helpers ──────────────────────────────────────────────────────

def _write_wav(filename: str, samples: list[int]) -> None:
    """Write 16-bit mono PCM samples to a WAV file."""
    filepath = os.path.join(SOUNDS_DIR, filename)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        raw = b"".join(struct.pack("<h", max(-MAX_AMP, min(MAX_AMP, s))) for s in samples)
        wf.writeframes(raw)
    print(f"  [OK] {filename} ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.3f}s)")


def _sine(freq: float, t: float) -> float:
    """Return a sine value at frequency *freq* and time *t*."""
    return math.sin(2.0 * math.pi * freq * t)


def _smooth_envelope(t: float, duration: float, attack: float = 0.01, decay: float = 0.05) -> float:
    """Smooth fade-in / fade-out envelope."""
    if t < attack:
        return t / attack
    if t > duration - decay:
        return max(0.0, (duration - t) / decay)
    return 1.0


# ── Sound generators ─────────────────────────────────────────────

def generate_classic_beep() -> None:
    """Simple sine wave beep at ~800 Hz, 200 ms."""
    duration = 0.20
    freq = 800.0
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _smooth_envelope(t, duration, attack=0.005, decay=0.03)
        val = _sine(freq, t) * env * 0.85
        samples.append(int(val * MAX_AMP))
    _write_wav("classic_beep.wav", samples)


def generate_bell() -> None:
    """Bell-like tone at ~523 Hz with exponential-decay harmonics, 500 ms."""
    duration = 0.50
    fundamental = 523.0
    n = int(SAMPLE_RATE * duration)
    # Harmonics: (freq_multiplier, amplitude, decay_rate)
    harmonics = [
        (1.0, 1.0, 4.0),
        (2.0, 0.55, 5.5),
        (3.0, 0.30, 7.0),
        (4.76, 0.18, 9.0),   # inharmonic partial — gives bell character
        (6.2, 0.08, 11.0),
    ]
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0
        for mult, amp, decay in harmonics:
            val += amp * math.exp(-decay * t) * _sine(fundamental * mult, t)
        # Soft attack
        if t < 0.003:
            val *= t / 0.003
        val *= 0.55  # overall level
        samples.append(int(max(-1.0, min(1.0, val)) * MAX_AMP))
    _write_wav("bell.wav", samples)


def generate_chime() -> None:
    """Two-tone ascending chime: C5 (523 Hz) → E5 (659 Hz), 300 ms total."""
    note_dur = 0.15
    freq1 = 523.25  # C5
    freq2 = 659.25  # E5
    n_note = int(SAMPLE_RATE * note_dur)
    samples = []

    for note_idx, freq in enumerate((freq1, freq2)):
        for i in range(n_note):
            t = i / SAMPLE_RATE
            env = _smooth_envelope(t, note_dur, attack=0.005, decay=0.04)
            # Add a subtle second harmonic for warmth
            val = (_sine(freq, t) * 0.85 + _sine(freq * 2, t) * 0.12) * env * 0.80
            samples.append(int(val * MAX_AMP))

    _write_wav("chime.wav", samples)


def generate_digital_alarm() -> None:
    """Sharp square wave pattern at ~1000 Hz with rapid on/off, 300 ms."""
    duration = 0.30
    freq = 1000.0
    n = int(SAMPLE_RATE * duration)
    pulse_on = 0.035   # 35 ms on
    pulse_off = 0.025   # 25 ms off
    cycle = pulse_on + pulse_off
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        # Determine if we're in an "on" or "off" portion of the pulse
        phase_in_cycle = t % cycle
        if phase_in_cycle >= pulse_on:
            samples.append(0)
            continue

        # Band-limited square-ish wave (sum of odd harmonics, tapered)
        val = 0.0
        for h in range(1, 8, 2):  # 1, 3, 5, 7
            val += _sine(freq * h, t) / h
        val *= (4.0 / math.pi)  # normalize

        # Micro envelope per pulse
        env = _smooth_envelope(phase_in_cycle, pulse_on, attack=0.002, decay=0.005)
        # Overall envelope
        env *= _smooth_envelope(t, duration, attack=0.003, decay=0.02)
        val = max(-1.0, min(1.0, val * env * 0.65))
        samples.append(int(val * MAX_AMP))

    _write_wav("digital_alarm.wav", samples)


def generate_soft_ding() -> None:
    """Gentle high sine at ~1047 Hz, 150 ms with smooth fade."""
    duration = 0.15
    freq = 1047.0  # C6
    n = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        # Smooth exponential decay for a gentle ding
        env = math.exp(-8.0 * t)
        # Soft attack
        if t < 0.004:
            env *= t / 0.004
        val = _sine(freq, t) * env * 0.75
        # Tiny harmonic for shimmer
        val += _sine(freq * 2.0, t) * env * 0.08
        samples.append(int(max(-1.0, min(1.0, val)) * MAX_AMP))

    _write_wav("soft_ding.wav", samples)


def generate_short_buzzer() -> None:
    """Low-frequency buzz at ~200 Hz, 250 ms."""
    duration = 0.25
    freq = 200.0
    n = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        env = _smooth_envelope(t, duration, attack=0.008, decay=0.04)
        # Buzzy tone: fundamental + several harmonics
        val = 0.0
        val += _sine(freq, t) * 1.0
        val += _sine(freq * 2, t) * 0.5
        val += _sine(freq * 3, t) * 0.35
        val += _sine(freq * 5, t) * 0.15
        val *= env * 0.40  # keep overall level moderate
        samples.append(int(max(-1.0, min(1.0, val)) * MAX_AMP))

    _write_wav("short_buzzer.wav", samples)


# ── Main ─────────────────────────────────────────────────────────

def main() -> None:
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    print(f"Generating sounds into {SOUNDS_DIR}\n")

    generate_classic_beep()
    generate_bell()
    generate_chime()
    generate_digital_alarm()
    generate_soft_ding()
    generate_short_buzzer()

    print("\nDone — 6 sound files generated.")


if __name__ == "__main__":
    main()
