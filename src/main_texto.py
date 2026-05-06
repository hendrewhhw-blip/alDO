import subprocess
import platform
import os
import re
import random
from cerebro import gen_brain

# ──────────────────────────────────────────────
# Configurações
# ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sistema  = platform.system()

if sistema == "Windows":
    PIPER_PATH = os.path.join(BASE_DIR, "piper", "piper.exe")
    FFPLAY     = "ffplay"
else:
    PIPER_PATH = os.path.join(BASE_DIR, "piper", "piper")
    FFPLAY     = "ffplay"

VOICE_MODEL    = os.path.join(BASE_DIR, "pt_BR-faber-medium.onnx")
PALAVRAS_SAIDA = {"sair", "exit", "quit", "saindo", "tchau", "adeus"}
FRASES_SAIDA   = ["Tchau!", "Adeus!", "Até logo!", "Tenha um bom dia!", "Até mais!"]

# ──────────────────────────────────────────────
# TTS — igual ao main.py
# ──────────────────────────────────────────────

def limpar_texto(texto: str) -> str:
    texto = texto.replace("*", "")
    texto = re.sub(r'[^\w\s.,!?àáâãéêíóôõúüçÀÁÂÃÉÊÍÓÔÕÚÜÇ-]', '', texto)
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

        ffplay = subprocess.Popen(
            [FFPLAY, "-nodisp", "-autoexit",
             "-f", "s16le", "-ar", "22050", "-i", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        ffplay.communicate(input=audio_data)

    except FileNotFoundError as e:
        print(f"[TTS não encontrado]: {e}")
    except Exception as e:
        print(f"[Erro no áudio]: {e}")

# ──────────────────────────────────────────────
# Loop principal
# ──────────────────────────────────────────────

brain = gen_brain(falar_fn=falar)
brain.preaquecimento()

print("IA: ", end="", flush=True)
brain.inicio()
print()

print("\nPronto. Digite sua mensagem (ou 'sair' para encerrar).\n")

while True:
    try:
        prompt = input("Você: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nEncerrando...")
        break

    if not prompt:
        continue

    if prompt.lower() in PALAVRAS_SAIDA:
        despedida = random.choice(FRASES_SAIDA)
        print(f"IA: {despedida}")
        falar(despedida)
        break

    print("IA: ", end="", flush=True)
    resposta = brain(texto=prompt)
    if not resposta:
        print("[silêncio intencional]")
    print()
