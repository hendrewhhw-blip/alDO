import sounddevice as sd
import numpy as np
import wave
import time

# volume global inicializado para evitar NameError antes do primeiro callback
volume: float = 0.0


def gravar_audio(filename: str = "audio.wav", samplerate: int = 16000) -> str | None:
    global volume

    gravando = False
    frames = []
    ultimo_som = time.time()

    SENSIBILIDADE = 0.01
    TEMPO_SILENCIO = 1.0

    def callback(indata, frames_count, time_info, status):
        nonlocal gravando, ultimo_som
        global volume

        vol = float(np.max(np.abs(indata)))
        volume = vol  # atualiza o volume global

        if vol > SENSIBILIDADE:
            gravando = True
            ultimo_som = time.time()

        if gravando:
            frames.append(indata.copy())

    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        while True:
            time.sleep(0.05)
            if gravando and (time.time() - ultimo_som) > TEMPO_SILENCIO and frames:
                break

    if not frames:
        return None

    audio = np.concatenate(frames, axis=0)

    # filtro de ruído
    if np.max(np.abs(audio)) < 0.01:
        return None

    # normalização
    audio = audio / max(float(np.max(np.abs(audio))), 1e-6)

    with wave.open(filename, "wb") as f:
        f.setnchannels(1)           # mono — stereo causava bug de velocidade no Whisper
        f.setsampwidth(2)
        f.setframerate(samplerate)  # linha estava quebrada no original
        f.writeframes((audio * 32767).astype(np.int16).tobytes())

    return filename


def transcribe_audio(path: str, model) -> str:
    print("Transcrevendo...")           # movido para antes do return
    segments, _ = model.transcribe(path, language="pt")
    return " ".join([seg.text for seg in segments]).strip()


def pegar_volume() -> float:
    return volume
