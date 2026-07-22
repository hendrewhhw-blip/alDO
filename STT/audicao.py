from __future__ import annotations

import queue
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel


class Audicao:

    DEFAULT_CONFIG={
        "modelo":"tiny",
        "sample_rate":16000,
        "canais":1,
        "bloco":1024,
        "silencio":0.015,
        "tempo_silencio":1.0,
        "tempo_maximo":15.0
    }

    def __init__(self,config,eventos=None,logger=None):

        self.config = self.DEFAULT_CONFIG.copy()

        if config:

            if isinstance(config, dict):
                self.config.update(config)

            else:
                self.config["modelo"] = config.get(
                    "audio.whisper",
                    self.config["modelo"]
                )

                self.config["sample_rate"] = config.get(
                    "audio.sample_rate",
                    self.config["sample_rate"]
                )

                self.config["silencio"] = config.get(
                    "audio.sensibilidade",
                    self.config["silencio"]
                )

                self.config["tempo_silencio"] = config.get(
                    "audio.tempo_silencio",
                    self.config["tempo_silencio"]
                )

        self.eventos=eventos
        self.logger=logger

        self.modelo=None
        self.stream=None

        self.queue=queue.Queue()

        self.buffer=[]

        self.gravando=False
        self.escutando=False
        self.processando=False

        self.inicio_gravacao=0.0
        self.ultimo_som=0.0

        self.ultimo_texto=""

        self.thread=None

        self.tmp=Path(tempfile.gettempdir())/"aldo_stt"
        self.tmp.mkdir(exist_ok=True)

    #--------------------------------------------------

    def carregar_modelo(self):

        if self.modelo is None:

            if self.logger:
                self.logger.info(
                    "Carregando Whisper..."
                )

                nome_do_modelo = self.config["modelo"] 

                self.modelo = WhisperModel(
                    nome_do_modelo, 
                    device="cpu", 
                    compute_type="int8"
                )

        return self.modelo

    #--------------------------------------------------
    def usuario_interrompeu(self) -> bool:
        return self.gravando and not self.processando
    
    def iniciar(self):

        if self.escutando:
            return

        self.carregar_modelo()

        self.stream=sd.InputStream(
            samplerate=self.config["sample_rate"],
            channels=self.config["canais"],
            blocksize=self.config["bloco"],
            callback=self._callback
        )

        self.stream.start()

        self.escutando=True

        if self.eventos:
            self.eventos.emit("inicio_escuta")

    #--------------------------------------------------

    def parar(self):

        if not self.escutando:
            return

        self.escutando=False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream=None

        if self.eventos:
            self.eventos.emit("fim_escuta")

    #--------------------------------------------------

    def _callback(self,indata,frames,time_info,status):

        if status and self.logger:
            self.logger.warning(status)

        self.queue.put(indata.copy())

    #--------------------------------------------------

    @property
    def ocupado(self):
        return self.processando

    #--------------------------------------------------

    def __repr__(self):

        return(
            f"<Audicao modelo={self.config['modelo']} "
            f"escutando={self.escutando}>"
        )
    #--------------------------------------------------

    def _volume(self,audio):

        return float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

    #--------------------------------------------------

    def _iniciar_gravacao(self):

        self.buffer.clear()

        self.gravando=True

        agora=time.time()

        self.inicio_gravacao=agora

        self.ultimo_som=agora

        if self.eventos:
            self.eventos.emit("usuario_falando")

    #--------------------------------------------------

    def _encerrar_gravacao(self):

        self.gravando=False

        if not self.buffer:
            return None

        audio=np.concatenate(self.buffer,axis=0)

        arquivo=self.tmp/"entrada.wav"

        sf.write(
            arquivo,
            audio,
            self.config["sample_rate"]
        )

        return arquivo

    #--------------------------------------------------

    def atualizar(self):

        if not self.escutando:
            return

        while not self.queue.empty():

            bloco=self.queue.get()

            volume=self._volume(bloco)

            agora=time.time()

            if volume>=self.config["silencio"]:

                self.ultimo_som=agora

                if not self.gravando:

                    self._iniciar_gravacao()

            if self.gravando:

                self.buffer.append(bloco)

                if (
                    agora-self.inicio_gravacao
                    >=self.config["tempo_maximo"]
                ):

                    arquivo=self._encerrar_gravacao()

                    if arquivo:

                        self._transcrever(arquivo)

                    return

                if (
                    agora-self.ultimo_som
                    >=self.config["tempo_silencio"]
                ):

                    arquivo=self._encerrar_gravacao()

                    if arquivo:

                        self._transcrever(arquivo)

                    return
    #--------------------------------------------------

    def _transcrever(self,arquivo):

        self.processando=True

        try:

            resultado=self.modelo.transcribe(
                str(arquivo),
                language="pt",
                fp16=False
            )

            texto=resultado["text"].strip()

            self.ultimo_texto=texto

            if texto:

                if self.eventos:
                    self.eventos.emit(
                        "texto_reconhecido",
                        texto=texto
                    )

                return texto

            return ""

        except Exception as erro:

            if self.logger:
                self.logger.exception(erro)

            return ""

        finally:

            self.processando=False

            try:
                arquivo.unlink()
            except Exception:
                pass

    #--------------------------------------------------

    def ouvir(self):

        while self.escutando:

            self.atualizar()

            if self.ultimo_texto:

                texto=self.ultimo_texto

                self.ultimo_texto=""

                return texto

            time.sleep(0.01)

        return ""

    #--------------------------------------------------

    def fechar(self):

        self.parar()

        self.modelo=None

        self.buffer.clear()

        while not self.queue.empty():

            self.queue.get()

    #--------------------------------------------------

    def info(self):

        return{

            "modelo":self.config["modelo"],

            "escutando":self.escutando,

            "gravando":self.gravando,

            "processando":self.processando,

            "ultimo_texto":self.ultimo_texto

        }