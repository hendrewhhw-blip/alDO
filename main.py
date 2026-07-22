from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path
import os
"""if sys.platform.startswith("linux"):
    os.environ["QT_QPA_PLATAFORM"] = "xcb"
    os.environ["QT_RHI_BACKEND"] = "opengl"
    os.environ["QSG_RENDER_LOOP"] = "basic"
    os.environ["LIBGL_ALWAYS_SOFTWARE"] = "0"    
 """   
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config.config_manager import Config

from memoria.memoria import Memoria
from memoria.contexto import Contexto

from plugins.eventos import EventBus
from plugins.contexto_plugin import PluginContext

from avatar.avatar_manager import AvatarManager

from tts.piper import PiperTTS
from STT.audicao import Audicao

from core.brain import Brain

from interface.app import App
import random


# ==========================================================
# Main
# ==========================================================

class Main:

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.logger = logging.getLogger("Aldo")

        self._carregar_estilo()

        # ---------------------------------------------
        # Configuração
        # ---------------------------------------------

        self.config = Config()

        self.memoria = Memoria(

            self.config

        )

        self.contexto = Contexto(

            self.memoria

        )

        self.eventos = EventBus(

            logger=self.logger

        )

        # ---------------------------------------------
        # Serviços
        # ---------------------------------------------

        self.avatar = AvatarManager(

            config=self.config,

            eventos=self.eventos,

            logger=self.logger

        )

        self.tts = PiperTTS(

            config=self.config,

            eventos=self.eventos,

            logger=self.logger

        )

        self.stt = Audicao(

            config=self.config,

            eventos=self.eventos,

            logger=self.logger

        )

        # ---------------------------------------------
        # Brain
        # ---------------------------------------------

        self.brain = Brain(

            memoria=self.memoria,

            contexto=self.contexto,

            eventos=self.eventos,

            config=self.config,

            falar_fn=self.tts.falar,

            ouvir_fn=self.stt.usuario_interrompeu,

            logger=self.logger

        )

        # ---------------------------------------------
        # Plugins
        # ---------------------------------------------

        self.plugin_context = PluginContext(

            eventos=self.eventos,

            memoria=self.memoria,

            brain=self.brain,

            config=self.config,

            avatar=self.avatar,

            tts=self.tts,

            stt=self.stt,

            interface=None,

            logger=self.logger,

            ollama=self.brain.llm

        )

        # ---------------------------------------------
        # Interface
        # ---------------------------------------------

        self.window = App(

            brain=self.brain,

            avatar=self.avatar,

            tts=self.tts,

            stt=self.stt,

            memoria=self.memoria,

            eventos=self.eventos,

            config=self.config

        )

        self.plugin_context.interface = self.window

        self.timer = QTimer()

        signal.signal(

            signal.SIGINT,

            self._encerrar

        )
    # =====================================================
    # Configuração
    # =====================================================

    def _carregar_estilo(self):

        arquivo = Path(

            "interface/styles.qss"

        )

        if arquivo.exists():

            self.app.setStyleSheet(

                arquivo.read_text(

                    encoding="utf-8"

                )

            )

    # =====================================================
    # Inicialização
    # =====================================================

    def setup(self):

        self._conectar_eventos()

        self.brain.plugins.iniciar(

            self.plugin_context

        )

        self.brain.aquecer()

        self.timer.timeout.connect(

            self._update

        )

        self.timer.start(

            16

        )

    # =====================================================
    # Atualização
    # =====================================================

    def _update(self):

        dt = 0.016

        try:

            self.avatar.update(dt)

        except Exception:

            self.logger.exception(

                "Erro no Avatar."

            )

        try:

            self.tts.atualizar()

        except Exception:

            self.logger.exception(

                "Erro no TTS."

            )

        try:

            self.stt.atualizar()

        except Exception:

            self.logger.exception(

                "Erro no STT."

            )

        try:

            self.brain.pensar()

        except Exception:

            self.logger.exception(

                "Erro no Brain."

            )
    # =====================================================
    # Eventos
    # =====================================================

    def _conectar_eventos(self):

        # ---------------------------------------------
        # Interface
        # ---------------------------------------------

        self.window.mensagem_enviada.connect(

            self._processar_texto

        )

        self.window.microfone_ativado.connect(

            self.stt.iniciar

        )

        self.window.microfone_desativado.connect(

            self.stt.parar

        )

        self.window.encerrando.connect(

            self._encerrar

        )

        # ---------------------------------------------
        # STT
        # ---------------------------------------------

        self.eventos.on(

            "texto_reconhecido",

            self._texto_reconhecido

        )

        # ---------------------------------------------
        # Streaming
        # ---------------------------------------------

        self.eventos.on(

            "token_recebido",

            self._token_recebido

        )

        self.eventos.on(

            "frase_pronta",

            self._frase_pronta

        )

        # ---------------------------------------------
        # Brain
        # ---------------------------------------------

        self.eventos.on(

            "resposta_pronta",

            self._resposta_pronta

        )

        # ---------------------------------------------
        # Avatar
        # ---------------------------------------------

        self.eventos.on(

            "avatar_estado",

            self._avatar_estado

        )

        self.eventos.on(

            "avatar_emocao",

            self._avatar_emocao

        )

        self.eventos.on(

            "avatar_olhar",

            self._avatar_olhar

        )

        # ---------------------------------------------
        # TTS
        # ---------------------------------------------

        self.eventos.on(

            "inicio_fala",

            self._inicio_fala

        )

        self.eventos.on(

            "fim_fala",

            self._fim_fala

        )

        self.eventos.on(

            "fala_interrompida",

            self._fala_interrompida

        )

        # ---------------------------------------------
        # Sistema
        # ---------------------------------------------

        self.eventos.on(

            "startup",

            self._startup

        )

        self.eventos.on(

            "shutdown",

            self._shutdown

        )
    # =====================================================
    # Entrada
    # =====================================================

    def _texto_reconhecido(
        self,
        texto=None,
        **kwargs
    ):

        if texto:

            self._processar_texto(

                texto

            )

    # -----------------------------------------------------

    def _processar_texto(
        self,
        texto
    ):

        texto = texto.strip()

        if not texto:

            return

        self.window.chat.adicionar_usuario(

            texto

        )

        resposta = self.brain.responder(

            texto

        )

        if resposta.texto:

            self.window.chat.adicionar_aldo(

                resposta.texto

            )

        if resposta.falar:

            self.tts.falar(

                resposta.texto

            )

        if resposta.finalizar:

            self._encerrar()

    # =====================================================
    # Streaming
    # =====================================================

    def _token_recebido(
        self,
        token=None,
        **kwargs
    ):

        if not token:

            return

        self.window.legenda.adicionar(

            token

        )

    # -----------------------------------------------------

    def _frase_pronta(
        self,
        frase=None,
        **kwargs
    ):

        if not frase:

            return

        self.window.legenda.mostrar(

            frase

        )

    # =====================================================
    # Brain
    # =====================================================

    def _resposta_pronta(
        self,
        resposta=None,
        **kwargs
    ):

        if resposta is None:

            return

        if hasattr(

            self.window,

            "toolbar"

        ):

            self.window.toolbar.setStatus(

                "Pronto"

            )

    # =====================================================
    # Avatar
    # =====================================================

    def _avatar_estado(
        self,
        estado=None,
        **kwargs
    ):
        # 1. Garante que a janela e o avatar já existem na tela
        if self.window.avatar is not None:
            if estado is not None:
                self.window.avatar.set_estado(estado)

    # -----------------------------------------------------

    def _avatar_emocao(
        self,
        emocao=None,
        **kwargs
    ):
        # 2. Garante que a janela e o avatar já existem na tela
        if self.window.avatar is not None:
            if emocao is not None:
                self.window.avatar.set_emocao(emocao)

    # -----------------------------------------------------

    def _avatar_olhar(
        self,
        direcao=None,
        **kwargs
    ):
        # 3. Garante que a janela e o avatar já existem na tela
        if self.window.avatar is not None:
            if direcao is not None:
                self.window.avatar.set_olhar(direcao)

    # =====================================================
    # TTS
    # =====================================================

    def _inicio_fala(
        self,
        texto=None,
        **kwargs
    ):
        # Só ativa a animação de fala se o avatar já tiver nascido
        if self.window.avatar is not None and hasattr(self.window.avatar, "falando"):
            self.window.avatar.falando(True)

    # -----------------------------------------------------

    def _fim_fala(
        self,
        **kwargs
    ):
        if self.window.avatar is not None and hasattr(self.window.avatar, "falando"):
            self.window.avatar.falando(False)

    # -----------------------------------------------------

    def _fala_interrompida(
        self,
        **kwargs
    ):
        if self.window.avatar is not None and hasattr(self.window.avatar, "falando"):
            self.window.avatar.falando(False)

    # =====================================================
    # Sistema
    # =====================================================

    def _startup(
        self,
        **kwargs
    ):

        self.logger.info(

            "Aldo iniciado."

        )

    # -----------------------------------------------------

    def _shutdown(
        self,
        **kwargs
    ):

        self.logger.info(

            "Encerrando Aldo."

        )
    # =====================================================
    # Inicialização
    # =====================================================

    def iniciar(self):

        self.setup()

        mensagem = self.brain.iniciar()

        if mensagem:

            self.window.chat.adicionar_aldo(

                mensagem

            )

            self.tts.falar(

                mensagem

            )

        if self.config.get(

            "audio.microfone",

            False

        ):

            self.stt.iniciar()

        self.window.show()

    # =====================================================
    # Encerramento
    # =====================================================

    def _encerrar(self,*args):

        self.timer.stop()

        try:

            self.brain.plugins.finalizar(

                self.plugin_context

            )

        except Exception:

            self.logger.exception(

                "Erro ao finalizar plugins."

            )

        try:

            self.brain.fechar()

        except Exception:

            self.logger.exception(

                "Erro ao finalizar Brain."

            )

        try:

            self.tts.fechar()

        except Exception:

            self.logger.exception(

                "Erro ao finalizar TTS."

            )

        try:

            self.stt.fechar()

        except Exception:

            self.logger.exception(

                "Erro ao finalizar STT."

            )

        try:

            self.avatar.fechar()

        except Exception:

            self.logger.exception(

                "Erro ao finalizar Avatar."

            )

        self.eventos.limpar()

        self.app.quit()

    # =====================================================
    # Execução
    # =====================================================

    def run(self):

        self.iniciar()

        return self.app.exec()


# =========================================================
# Entrada
# =========================================================

def main():

    programa = Main()

    return programa.run()


if __name__ == "__main__":

    raise SystemExit(

        main()

    )