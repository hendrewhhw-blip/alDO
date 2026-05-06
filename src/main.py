import subprocess
import platform
import os
import re
import random
import time
import threading
from faster_whisper import WhisperModel
from audicao import gravar_audio, transcribe_audio, pegar_volume
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
# Interrupção por voz
# Retorna True se o microfone detectar fala durante TTS
# ──────────────────────────────────────────────

_interrompido = False

def ouvir_interrupcao() -> bool:
    """Retorna True se o volume atual sugere que alguém está falando."""
    return pegar_volume() > 0.05

# ──────────────────────────────────────────────
# TTS
# ──────────────────────────────────────────────

_tts_lock = threading.Lock()

def limpar_texto(texto: str) -> str:
    texto = texto.replace("*", "")
    texto = re.sub(r'[^\w\s.,!?àáâãéêíóôõúüçÀÁÂÃÉÊÍÓÔÕÚÜÇ-]', '', texto)
    return texto.strip()

def falar(texto: str):
    """TTS síncrono — bloqueia até terminar de falar."""
    if not texto:
        return
    texto = limpar_texto(texto)
    if not texto:
        return

    with _tts_lock:
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
# Transcrição em thread separada
# ──────────────────────────────────────────────

def transcrever_async(arquivo: str, model, callback):
    def _run():
        texto = transcribe_audio(arquivo, model)
        if texto:
            callback(texto)
    t = threading.Thread(target=_run, daemon=True)
    t.start()

# ──────────────────────────────────────────────
# Loop principal
# ──────────────────────────────────────────────

print("Carregando Whisper tiny...")
whisper_model = WhisperModel("tiny", compute_type="int8")

print("Iniciando cérebro...")
brain = gen_brain(falar_fn=falar, ouvir_fn=ouvir_interrupcao)

brain.preaquecimento()

# Cumprimento inicial — brain.inicio() agora (era brain._inicio antes)
print("IA: ", end="", flush=True)
resposta_inicio = brain.inicio()
if resposta_inicio:
    print(resposta_inicio)

ultimo_verificacao_evento = time.time()
em_processamento = False

print("\nPronto. Ouvindo...\n")

def processar_fala(prompt: str):
    global em_processamento
    print(f"Você: {prompt}")

    if prompt.lower().strip() in PALAVRAS_SAIDA:
        despedida = random.choice(FRASES_SAIDA)
        print(f"IA: {despedida}")
        falar(despedida)
        os._exit(0)

    print("IA: ", end="", flush=True)
    # passa o volume atual pro brain detectar eventos de ambiente
    resposta = brain(texto=prompt, volume=pegar_volume())
    if resposta:
        print(resposta)
    else:
        print("[silêncio intencional]")

    em_processamento = False

while True:
    # ── Verificação proativa a cada 10s ──
    if not em_processamento and (time.time() - ultimo_verificacao_evento) > 10:
        ultimo_verificacao_evento = time.time()
        resposta_proativa = brain(volume=pegar_volume())
        if resposta_proativa:
            print(f"\nIA (proativo): {resposta_proativa}\n")

    # ── Captura de áudio ──
    arquivo = gravar_audio()
    if arquivo is None:
        continue

    em_processamento = True
    transcrever_async(arquivo, whisper_model, processar_fala)
