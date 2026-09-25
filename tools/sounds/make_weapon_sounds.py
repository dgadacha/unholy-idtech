#!/usr/bin/env python3
"""
Sons du fusil et de la cible, synthetises : bruit filtre, chocs et resonances.

Le pack d'armes n'a aucun son, et le prototype synthetisait deja les siens. Ce
sont des sons de travail : ils disent ce qui se passe (le coup, le clic a vide,
le chargeur qui sort puis rentre, le levier d'armement, l'impact selon la
matiere), en attendant une vraie prise de son.

Sortie : content/sound/unholy/*.wav, 44,1 kHz, 16 bits, mono. Le tirage est
fixe : le script redonne toujours les memes fichiers.
"""

import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'content' / 'sound' / 'unholy'
RATE = 44100


def seconds(duration):
    return np.arange(int(duration * RATE)) / RATE


def band_noise(rng, duration, low, high):
    """Du bruit blanc ramene a une bande de frequences, par transformee."""
    n = int(duration * RATE)
    spectrum = np.fft.rfft(rng.standard_normal(n))
    freqs = np.fft.rfftfreq(n, 1 / RATE)
    mask = (freqs >= low) & (freqs <= high)
    signal = np.fft.irfft(spectrum * mask, n)
    return signal / (np.abs(signal).max() + 1e-9)


def decay(duration, tau, delay=0.0):
    t = seconds(duration) - delay
    env = np.exp(-np.clip(t, 0, None) / tau)
    env[t < 0] = 0.0
    return env


def sweep(duration, start, end, tau):
    """Une sinusoide qui glisse de `start` a `end` Hz en s'eteignant."""
    t = seconds(duration)
    freq = end + (start - end) * np.exp(-t / tau)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    return np.sin(phase)


def click(rng, duration, at, low, high, tau, gain=1.0):
    """Un choc bref : du bruit dans une bande, qui s'eteint en `tau`."""
    return gain * band_noise(rng, duration, low, high) * decay(duration, tau, at)


def ring(duration, at, freq, tau, gain=1.0):
    """Une resonance de metal ou de bois."""
    t = seconds(duration) - at
    signal = np.sin(2 * np.pi * freq * np.clip(t, 0, None))
    return gain * signal * decay(duration, tau, at)


def finish(signal, peak=0.89):
    signal = np.tanh(signal * 1.4)
    signal = signal / (np.abs(signal).max() + 1e-9) * peak
    # Un fondu d'une milliseconde a chaque bout : pas de claquement a la coupe.
    fade = min(len(signal) // 2, int(0.001 * RATE))
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    return signal


def write(name, signal):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (finish(signal) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data.tobytes())
    print(f'{path.relative_to(ROOT)} : {len(signal) / RATE:.2f} s')


def gunshot(seed):
    """
    Le coup : un claquement tres bref, le souffle, un coup sourd qui descend,
    et la queue que renvoie une piece fermee.
    """
    rng = np.random.default_rng(seed)
    d = 0.6
    crack = band_noise(rng, d, 1500, 12000) * decay(d, 0.004)
    blast = band_noise(rng, d, 80, 2500) * decay(d, 0.045)
    thump = sweep(d, 160 + 15 * rng.random(), 42, 0.05) * decay(d, 0.07)
    tail = band_noise(rng, d, 120, 900) * decay(d, 0.22, 0.02) * 0.35
    return 0.9 * crack + 1.0 * blast + 1.2 * thump + tail


def main():
    for index, seed in enumerate((11, 23, 37), start=1):
        write(f'weapons/rifle_fire_{index}.wav', gunshot(seed))

    rng = np.random.default_rng(5)
    d = 0.12
    write('weapons/rifle_dry.wav',
          click(rng, d, 0.0, 2000, 9000, 0.003) + 0.6 * click(rng, d, 0.012, 1200, 6000, 0.006))

    d = 0.35
    write('weapons/rifle_magout.wav',
          click(rng, d, 0.0, 1500, 8000, 0.004)
          + 0.5 * band_noise(rng, d, 2000, 6000) * decay(d, 0.05, 0.01)
          + ring(d, 0.0, 1850, 0.03, 0.4))

    write('weapons/rifle_magin.wav',
          click(rng, d, 0.0, 800, 7000, 0.006, 1.2)
          + click(rng, d, 0.035, 600, 5000, 0.01)
          + ring(d, 0.0, 210, 0.05, 0.6)
          + ring(d, 0.035, 1600, 0.04, 0.4))

    write('weapons/rifle_chargepull.wav',
          0.7 * band_noise(rng, d, 1500, 7000) * decay(d, 0.06)
          + click(rng, d, 0.07, 1000, 8000, 0.004))

    write('weapons/rifle_chargerelease.wav',
          click(rng, d, 0.0, 600, 9000, 0.005, 1.3)
          + ring(d, 0.0, 2300, 0.06, 0.5)
          + ring(d, 0.0, 340, 0.05, 0.5))

    d = 0.4
    for index, seed in enumerate((41, 43), start=1):
        rng = np.random.default_rng(seed)
        write(f'impacts/stone_{index}.wav',
              click(rng, d, 0.0, 1000, 10000, 0.006, 1.2)
              + 0.4 * band_noise(rng, d, 300, 4000) * decay(d, 0.08, 0.005))
    rng = np.random.default_rng(47)
    write('impacts/metal.wav',
          click(rng, d, 0.0, 2000, 12000, 0.003)
          + ring(d, 0.0, 2900, 0.12, 0.7) + ring(d, 0.0, 4100, 0.08, 0.4))
    write('impacts/wood.wav',
          click(rng, d, 0.0, 400, 5000, 0.008, 1.2) + ring(d, 0.0, 260, 0.05, 0.7))

    d = 0.5
    write('target/hit.wav', click(rng, d, 0.0, 200, 3000, 0.012, 1.2) + ring(d, 0.0, 180, 0.07, 0.8))
    write('target/fall.wav',
          click(rng, d, 0.0, 100, 2500, 0.03, 1.3) + ring(d, 0.0, 95, 0.12, 0.9)
          + 0.3 * band_noise(rng, d, 200, 1500) * decay(d, 0.1, 0.01))


if __name__ == '__main__':
    main()
