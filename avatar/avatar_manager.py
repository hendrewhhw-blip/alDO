from __future__ import annotations

import random
import time

from enum import Enum


# ==========================================================
# Estados
# ==========================================================

class EstadoAvatar(Enum):

    DESLIGADO = "desligado"

    OCIOSO = "ocioso"

    OUVINDO = "ouvindo"

    PENSANDO = "pensando"

    FALANDO = "falando"

    DORMINDO = "dormindo"


# ==========================================================
# Emoções
# ==========================================================

class EmocaoAvatar(Enum):

    NEUTRO = "neutro"

    FELIZ = "feliz"

    TRISTE = "triste"

    CURIOSO = "curioso"

    SURPRESO = "surpreso"

    IRRITADO = "irritado"


# ==========================================================
# Direção do olhar
# ==========================================================

class DirecaoOlhar(Enum):

    CENTRO = "centro"

    ESQUERDA = "esquerda"

    DIREITA = "direita"

    CIMA = "cima"

    BAIXO = "baixo"


# ==========================================================
# Avatar
# ==========================================================

class AvatarManager:
    """
    Controlador completo do avatar.

    NÃO desenha.

    NÃO usa OpenGL.

    NÃO conhece Panda3D.

    Apenas controla o estado lógico do rosto.

    O renderizador apenas consulta essas informações.
    """

    # ------------------------------------------------------

    def __init__(

        self,

        eventos,

        config=None,

        logger=None

    ):

        self.eventos = eventos

        self.config = config

        self.logger = logger

        # ----------------------------------------------
        # Estado
        # ----------------------------------------------

        self.estado = EstadoAvatar.DESLIGADO

        self.emocao = EmocaoAvatar.NEUTRO

        self.olhar = DirecaoOlhar.CENTRO

        # ----------------------------------------------
        # Face
        # ----------------------------------------------

        self.boca = 0.0

        self.olhos = 1.0

        self.inclinacao = 0.0

        # ----------------------------------------------
        # Controle
        # ----------------------------------------------

        self.falando = False

        self.pensando = False

        self.ouvindo = False

        self.dormindo = False

        # ----------------------------------------------
        # Tempo
        # ----------------------------------------------

        agora = time.time()

        self.inicio = agora

        self.ultima_interacao = agora

        self.ultima_mudanca = agora

        self.ultimo_piscar = agora

        self.proximo_piscar = agora + self._novo_intervalo_piscar()

        # ----------------------------------------------
        # Configuração
        # ----------------------------------------------

        self.piscar_automatico = True

        self.olhar_automatico = True

        self.animacoes = True

        # ----------------------------------------------
        # Registro
        # ----------------------------------------------

        self._registrar_eventos()

        if self.logger:
            self.logger.info("AvatarManager iniciado.")
        # ------------------------------------------------------

    def _registrar_eventos(self):

        self.eventos.on(

            "startup",

            self._startup

        )

        self.eventos.on(

            "shutdown",

            self._shutdown

        )

        self.eventos.on(

            "entrada_usuario",

            self._usuario_falando

        )

        self.eventos.on(

            "antes_llm",

            self._pensando

        )

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
        # ------------------------------------------------------

    def _novo_intervalo_piscar(self):

        """
        Tempo até o próximo piscar.

        Entre 3 e 7 segundos.
        """

        return random.uniform(

            3.0,

            7.0

        )

    # ------------------------------------------------------

    def _marcar_interacao(self):

        agora = time.time()

        self.ultima_interacao = agora

        self.ultima_mudanca = agora
        # ------------------------------------------------------

    def _trocar_estado(

        self,

        estado

    ):

        if estado == self.estado:

            return

        self.estado = estado

        self.ultima_mudanca = time.time()

        self.eventos.emit(

            "avatar_estado",

            estado=estado

        )

        if self.logger:

            self.logger.debug(

                f"Avatar -> {estado.value}"

            )
        # ------------------------------------------------------

    def _startup(self):

        self._trocar_estado(

            EstadoAvatar.OCIOSO

        )

    # ------------------------------------------------------

    def _shutdown(self):

        self._trocar_estado(

            EstadoAvatar.DESLIGADO

        )

    # ------------------------------------------------------

    def _usuario_falando(

        self,

        **kwargs

    ):

        self._marcar_interacao()

        self.ouvindo = True

        self.pensando = False

        self.falando = False

        self._trocar_estado(

            EstadoAvatar.OUVINDO

        )
        # ======================================================
    # Eventos de fala
    # ======================================================

    def _pensando(self, **kwargs):

        self._marcar_interacao()

        self.pensando = True
        self.ouvindo = False
        self.falando = False

        self._trocar_estado(

            EstadoAvatar.PENSANDO

        )

    # ------------------------------------------------------

    def _inicio_fala(self, **kwargs):

        self._marcar_interacao()

        self.falando = True
        self.pensando = False
        self.ouvindo = False

        self._trocar_estado(

            EstadoAvatar.FALANDO

        )

    # ------------------------------------------------------

    def _fim_fala(self, **kwargs):

        self.falando = False

        self.boca = 0.0

        self._trocar_estado(

            EstadoAvatar.OCIOSO

        )

    # ------------------------------------------------------

    def _fala_interrompida(self, **kwargs):

        self.falando = False

        self.boca = 0.0

        self._trocar_estado(

            EstadoAvatar.OUVINDO

        )

    # ======================================================
    # Emoções
    # ======================================================

    def definir_emocao(

        self,

        emocao

    ):

        if isinstance(emocao, str):

            emocao = EmocaoAvatar(

                emocao.lower()

            )

        if emocao == self.emocao:

            return

        self.emocao = emocao

        self.eventos.emit(

            "avatar_emocao",

            emocao=emocao

        )

    # ======================================================
    # Olhar
    # ======================================================

    def olhar_para(

        self,

        direcao

    ):

        if isinstance(direcao, str):

            direcao = DirecaoOlhar(

                direcao.lower()

            )

        if direcao == self.olhar:

            return

        self.olhar = direcao

        self.eventos.emit(

            "avatar_olhar",

            direcao=direcao

        )

    # ======================================================
    # Boca
    # ======================================================

    def abrir_boca(

        self,

        intensidade=1.0

    ):

        intensidade = max(

            0.0,

            min(

                intensidade,

                1.0

            )

        )

        self.boca = intensidade

    # ------------------------------------------------------

    def fechar_boca(self):

        self.boca = 0.0

    # ======================================================
    # Piscar
    # ======================================================

    def piscar(self):

        self.olhos = 0.0

        self.eventos.emit(

            "avatar_piscou"

        )

    # ------------------------------------------------------

    def abrir_olhos(self):

        self.olhos = 1.0

    # ======================================================
    # Idle
    # ======================================================

    def mover_cabeca(

        self,

        valor

    ):

        self.inclinacao = max(

            -1.0,

            min(

                valor,

                1.0

            )

        )

    # ------------------------------------------------------

    def parar_movimento(self):

        self.inclinacao = 0.0
        # ======================================================
    # Atualização
    # ======================================================

    def update(self, dt):
        """
        Deve ser chamado continuamente pelo main.

        dt = tempo desde a última atualização.
        """

        agora = time.time()

        # ----------------------------------------------
        # Piscar automático
        # ----------------------------------------------

        if self.piscar_automatico:

            if agora >= self.proximo_piscar:

                self.olhos = 0.0

                self.eventos.emit("avatar_piscou")

                self.ultimo_piscar = agora

                self.proximo_piscar = (

                    agora +

                    self._novo_intervalo_piscar()

                )

            elif self.olhos < 1.0:

                self.olhos += dt * 8.0

                if self.olhos > 1.0:

                    self.olhos = 1.0

        # ----------------------------------------------
        # Boca
        # ----------------------------------------------

        if not self.falando:

            if self.boca > 0:

                self.boca -= dt * 5

                if self.boca < 0:

                    self.boca = 0

        # ----------------------------------------------
        # Idle
        # ----------------------------------------------

        if self.estado == EstadoAvatar.OCIOSO:

            self.inclinacao *= 0.98

        else:

            self.inclinacao *= 0.92

    # ======================================================
    # Estado
    # ======================================================

    def resetar(self):

        self.estado = EstadoAvatar.OCIOSO

        self.emocao = EmocaoAvatar.NEUTRO

        self.olhar = DirecaoOlhar.CENTRO

        self.boca = 0.0

        self.olhos = 1.0

        self.inclinacao = 0.0

        self.falando = False

        self.pensando = False

        self.ouvindo = False

        self.dormindo = False

        agora = time.time()

        self.ultima_interacao = agora

        self.ultima_mudanca = agora

        self.ultimo_piscar = agora

        self.proximo_piscar = (

            agora +

            self._novo_intervalo_piscar()

        )

    # ======================================================
    # API pública
    # ======================================================

    @property
    def esta_falando(self):

        return self.falando

    @property
    def esta_ouvindo(self):

        return self.ouvindo

    @property
    def esta_pensando(self):

        return self.pensando

    @property
    def esta_ocioso(self):

        return self.estado == EstadoAvatar.OCIOSO

    # ======================================================
    # Informações
    # ======================================================

    def info(self):

        return {

            "estado": self.estado.value,

            "emocao": self.emocao.value,

            "olhar": self.olhar.value,

            "boca": round(self.boca, 2),

            "olhos": round(self.olhos, 2),

            "inclinacao": round(self.inclinacao, 2),

            "falando": self.falando,

            "pensando": self.pensando,

            "ouvindo": self.ouvindo,

            "tempo_desde_interacao":

                round(

                    time.time()

                    - self.ultima_interacao,

                    2

                )

        }

    # ======================================================
    # Encerramento
    # ======================================================

    def fechar(self):

        self.eventos.off("startup", self._startup)
        self.eventos.off("shutdown", self._shutdown)
        self.eventos.off("entrada_usuario", self._usuario_falando)
        self.eventos.off("antes_llm", self._pensando)
        self.eventos.off("inicio_fala", self._inicio_fala)
        self.eventos.off("fim_fala", self._fim_fala)
        self.eventos.off("fala_interrompida", self._fala_interrompida)

        self.resetar()

        self._trocar_estado(
            EstadoAvatar.DESLIGADO
    )
    # ======================================================

    def __repr__(self):

        return (

            f"<AvatarManager "

            f"estado={self.estado.value} "

            f"emocao={self.emocao.value}>"

        )