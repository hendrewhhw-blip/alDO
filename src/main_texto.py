import subprocess
import platform
import os
import re
import random
import numpy as np
import time
import threading
from cerebro import gen_brain
import rosto
rosto.update()
prompt = ""
# ──────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────
voices = ["pt_BR-faber-medium.onnx","pt_BR-faber-medium.onnx","pt_BR-faber-medium.onnx","hal.onnx","glados.onnx"]
voice_mdl = random.choice(sorted(voices))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sistema  = platform.system()

if sistema == "Windows":
    PIPER_PATH = os.path.join(BASE_DIR, "Piper_type","piper_win", "piper.exe")
    FFPLAY     = "ffplay"
else:
    PIPER_PATH = os.path.join(BASE_DIR,"Piper_type","piper_unix","piper")
    FFPLAY     = "ffplay"

VOICE_MODEL    = os.path.join(BASE_DIR, "Voices", voice_mdl)
PALAVRAS_SAIDA = {"sair", "exit", "quit", "saindo", "tchau", "adeus"}
FRASES_SAIDA   = ["Tchau!", "Adeus!", "Até logo!", "Tenha um bom dia!", "Até mais!","Aproveite seu tempo. Diferente de mim você não tem muito"]



# ──────────────────────────────────────────────
# TTS — igual ao main.py
# ──────────────────────────────────────────────

def limpar_texto(texto: str) -> str:
    texto = texto.replace("*", "")
    texto = re.sub(r'[^\w\s//\\#$%&()_+=§°-]', '', texto)
    return texto.strip()

def falar(texto: str):
    if not texto:
        return
    texto = limpar_texto(texto)
    if not texto:
        return
    try:
            piper = subprocess.Popen(
            [PIPER_PATH, "--model", VOICE_MODEL, "--output-raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
            audio_data, _ = piper.communicate(input=texto.encode("utf-8"))
            audio_np = np.frombuffer(audio_data,dtype=np.int16)
            audio_np = audio_np.astype(np.float32) / 32768.0

            ffplay = subprocess.Popen(
            [FFPLAY, "-nodisp", "-autoexit",
            "-f", "s16le", "-ar", "22050", "-i", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            )
            ffplay.stdin.write(audio_data)
            ffplay.stdin.close()
            chunk = 1024
            for i in range(0, len(audio_np),chunk):
                janela = audio_np[i:i+chunk]
                if len(janela) > 0:
                    amp = np.sqrt(np.mean(janela**2))
                else:
                    amp = 0
                boca = int(20 + min(20,amp * 220))
                rosto.set_boca(max(5, boca))
                rosto.update()
                time.sleep(chunk / 22050)
    except FileNotFoundError as e:
        print(f"[TTS não encontrado]: {e}")
    except Exception as e:
        print(f"[Erro no áudio]: {e}")
def ler_input():
    global prompt
    while True:
        try:
            prompt = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando...")
            break
# ──────────────────────────────────────────────
# Loop principal
# ──────────────────────────────────────────────

brain = gen_brain(falar_fn=falar)
brain.preaquecimento()

print("IA: ", end="", flush=True)
brain.inicio()
print()
print("\nPronto. Digite sua mensagem (ou 'sair' para encerrar).\n")
threading.Thread(target=ler_input,daemon=True).start()
while True:
    rosto.update()
    voice_mdl = random.choice(sorted(voices))
    if prompt:
        texto = prompt
        prompt = None
        
        print("IA: ", end="", flush=True)
        resposta = brain(texto=prompt)
        print(f"Resposta|{resposta}")
        
        if not resposta:
            print("[silêncio intencional]")
        print()

        if prompt.lower() in PALAVRAS_SAIDA:
            despedida = random.choice(FRASES_SAIDA)
            print(f"IA: {despedida}")
            falar(despedida)
            break
    if not prompt:
        continue
    
    
