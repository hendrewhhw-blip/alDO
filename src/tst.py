import ollama
import subprocess
import platform
import os
import re
import queue
import sounddevice as sd
import json
import random
import numpy as np
from faster_whisper import WhisperModel
from auxiliares import *

#MODEL_OLLAMA = "gemma2:2b"
MODEL_OLLAMA = "tinyllama:1.1b"  #setar arquivos necesários. o modelo deve ser modificado para melhor resposta :3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sistema = platform.system()

# caminhos referente ao sistema. Não há suporte a macOS (nunca terá, user de apple pode pagar pela alexa -_-)
if sistema == "Windows":
    PIPER_PATH = os.path.join(BASE_DIR, "piper", "piper.exe")
    FFPLAY_PATH = "ffplay"
else:
    PIPER_PATH = os.path.join(BASE_DIR, "piper", "piper")
    FFPLAY_PATH = "ffplay"

VOICE_MODEL = os.path.join(BASE_DIR, "pt_BR-faber-medium.onnx")

# prompt de personalidade e regras para melhor resposta

SYSTEM_PROMPT = """
Toda vez que lhe for feito uma pergunta sobre sentimentos humanos. Imagine-se como um humano, porém não adimita que é um humano
Regras obrigatórias:
- Sempre responda em português do Brasil.
- Respostas curtas e objetivas.
"""

def limpar_texto(texto):# filtro
    # remove asteriscos
    texto = texto.replace("*", "")
    # remove emojis/caracteres estranhos
    texto = re.sub(r'[^\w\s.,!?-]', '', texto)
    # remove emojis/caracteres estranhos
    texto = re.sub(r'[^\w\s.,!?-]', '', texto)
    return texto

    return texto

def falar(texto): # Text to Speech(tts)
    try:
        # 1. gera áudio com piper
        piper = subprocess.Popen(
            [
                PIPER_PATH,
                "--model", VOICE_MODEL,
                "--output-raw"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

        audio_data, _ = piper.communicate(input=texto.encode("utf-8"))

        # 2. toca com ffplay
        ffplay = subprocess.Popen(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-f", "s16le",
                "-ar", "22050",
                "-i", "-"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

        ffplay.communicate(input=audio_data)

    except Exception as e:
        print("Erro no áudio:", e)

frase = ""
model = WhisperModel("base", compute_type="int8")
device = 6
gravando = False

# loop principal
while True:
    arquivo = gravar_audio()
    prompt = transcribe_audio(arquivo,model)
    
    if prompt.strip() == "":
        continue
    
    print(f"Você: {prompt}")
    

    if prompt.lower() in ["sair", "exit", "quit","saindo"]:
        goodbye = ["tchau!","Adeus!","Até logo!","Tenha um bom dia!","Obrigado!","*****✍️🔥***** Rosto sorridente com olhos sorridentes***jocélio****"]
        c = random.choice(goodbye)
        print(f"IA: {c}")
        falar(c)
        break

    print("IA: ", end="", flush=True)

    resposta = ollama.generate(
        model=MODEL_OLLAMA,
        prompt=prompt,
        system=SYSTEM_PROMPT,
        stream=True,
        options={
            "num_predict": 120,
            "temperature": 0.6,
            "top_k": 40,
            "top_p": 0.9,
            "num_thread": 4,
            "keep_alive": "5m"
        }
    )

    txt = ""

    for chunk in resposta:
        parte = chunk["response"]
        print(parte, end="", flush=True)
        txt += parte

    fil_txt = limpar_texto(txt.strip())
    print("\n")
    print(f"Filtro: {fil_txt}")
    falar(fil_txt)