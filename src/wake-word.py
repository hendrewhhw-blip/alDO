import queue
import sounddevice as sd
import vosk
import json

def esperar_ww():
    q = queue.Queue()

    WAKE_WORD = ["computador","aldo"] # palavra para acordar

    def callback(indata, frames, time, status):
        q.put(bytes(indata))

    model = vosk.Model("vosk-model-small-pt-0.3")

    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        rec = vosk.KaldiRecognizer(model, 16000)

        print("Escutando...")

        while True:
            data = q.get()

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                texto = result.get("text", "")

                if texto:
                    print("Ouvido:", texto)

                    if WAKE_WORD[0] in texto or WAKE_WORD[1] in texto:
                        print(" WAKE WORD DETECTADA!")
                        break
esperar_ww()