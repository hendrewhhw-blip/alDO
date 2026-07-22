from __future__ import annotations

import os
import sys
import subprocess
import random
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QFrame, QVBoxLayout, QApplication

from interface.interface import Interface
from interface.chatpanel import ChatPanel
from interface.toolbar import ToolBar
from interface.legenda import Legenda
from interface.settings import Settings

class PandaWidget(QFrame):

    def __init__(self, avatar_manager, eventos=None):
        super().__init__()
        self.avatar_manager = avatar_manager
        self.eventos = eventos
        
        self.layout_3d = QVBoxLayout(self)
        self.layout_3d.setContentsMargins(0, 0, 0, 0)
        
        self.processo_panda = None
        self.avatar_view = self  
        
        # --- Variáveis de Estado ---
        self.angry_value = 0          # Permite acumular irritação
        self.is_speaking = False      # Controle de foco (inatividade)
        
        # Timer para sincronizar a posição geométrica da janela em cima do frame
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._sync_position)
        
        # Inicia os comportamentos autônomos (Idle)
        self._agendar_proximo_blink()
        self._agendar_proximo_olhar()
        
        # Sincronia com os eventos do sistema
        if self.eventos:
            self.eventos.on("movimento_boca", self._atualizar_boca_panda)
            self.eventos.on("mudanca_estado", self._processar_mudanca_estado)

    def showEvent(self, event):
        super().showEvent(event)
        if self.processo_panda is not None:
            return

        # Resolve o caminho do script do renderizador com base na estrutura de pastas
        BASE_DIR = Path(__file__).resolve().parent.parent
        script_panda = Path(__file__).resolve().parent / "render_panda.py"

        # Impede a criação de janelas Cmd extras em background no Windows
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        # Dispara o renderizador 3D isolado em outro processo com barramento leve por texto
        self.processo_panda = subprocess.Popen(
            [sys.executable, str(script_panda)],
            stdin=subprocess.PIPE,
            text=True,
            creationflags=creation_flags
        )
        
        self._sync_position()
        self._update_timer.start(20)

    def _sync_position(self):
        if not self.processo_panda or self.processo_panda.poll() is not None:
            return
        if not self.isVisible():
            return
            
        top_left = self.mapToGlobal(self.rect().topLeft())
        self._enviar_comando(f"POS {top_left.x()} {top_left.y()} {self.width()} {self.height()}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_position()

    def _enviar_comando(self, comando: str):
        if self.processo_panda and self.processo_panda.poll() is None:
            try:
                self.processo_panda.stdin.write(f"{comando}\n")
                self.processo_panda.stdin.flush()
            except Exception:
                pass

    def _atualizar_boca_panda(self, volume=0.0):
        # Envia o comando IPC SHAPE para o subprocesso do Panda3D abrir a boca
        self.set_shape("MouthOpen", volume)

    # --- NOVO: Handler do evento de mudança de estado ---
    def _processar_mudanca_estado(self, **kwargs):
        estado = kwargs.get("estado", {})
        
        # Resolve o crash: Trata se o cérebro mandou um dicionário ou apenas uma string ("Blink")
        if isinstance(estado, str):
            humor = estado
        elif isinstance(estado, dict):
            humor = estado.get("humor", "neutro")
        else:
            humor = "neutro"

        self.set_emocao(humor)

    # ==========================================
    # LÓGICA DE INATIVIDADE E ANIMAÇÃO
    # ==========================================

    def _agendar_proximo_blink(self):
        """Agenda o próximo piscar para um momento aleatório entre 3 e 6 segundos."""
        tempo = random.randint(3000, 6000)
        QTimer.singleShot(tempo, self._animar_blink)

    def _abrir_olhos(self):
        """Função dedicada para abrir os olhos (evita que o PySide6 apague da memória)"""
        self.set_shape("Blink", 0.0)

    def _animar_blink(self, autonomo=True):
        """Executa um piscar rápido apenas se não estiver falando."""
        # Trava de segurança: só pisca se a boca estiver fechada (não estiver falando)
        if not self.is_speaking:
            self.set_shape("Blink", 1.0)
            
            # Ao invés do lambda, usamos a função nomeada!
            QTimer.singleShot(150, self._abrir_olhos)
            
        # Se a chamada veio do loop automático, agenda o próximo piscar
        if autonomo:
            self._agendar_proximo_blink()

    def _agendar_proximo_olhar(self):
        """Agenda uma olhada aleatória entre 2 e 5 segundos."""
        tempo = random.randint(2000, 5000)
        QTimer.singleShot(tempo, self._animar_olhar)

    def _animar_olhar(self):
        """Se o Aldo estiver inativo, olha pros lados."""
        if not self.is_speaking:
            direcoes = ["esquerda", "direita", "cima", "baixo", "centro"]
            # Peso maior pro centro pra ele não parecer descontrolado
            direcao = random.choices(
                population=direcoes, 
                weights=[15, 15, 10, 10, 50], 
                k=1
            )[0]
            self.set_olhar(direcao)
        else:
            # Mantém o foco no usuário quando estiver falando
            self.set_olhar("centro")
            
        self._agendar_proximo_olhar()

    # ==========================================
    # CONTROLE DAS EXPRESSÕES (IPC)
    # ==========================================
    def set_shape(self, nome, valor):
        self._enviar_comando(f"SHAPE {nome} {valor}")

    def limpar_expressoes(self):
        # O "Blink" foi adicionado para garantir que os olhos sempre abram caso ocorra algum travamento
        mapeamento = ["MouthOpen", "HappyExpression", "SadExpression", "AngryExpression", "SurpriseExpression", "EyebrownUp", "Blink"]
        for nome in mapeamento:
            self.set_shape(nome, 0.0)

    def set_emocao(self, emocao):
        # Não zera mais a angry_value aqui dentro, usa a variável da classe!
        self.limpar_expressoes()
        
        if emocao == "feliz":
            if self.angry_value > 5:
                self.angry_value -= random.randint(5, self.angry_value)
                print(f"[APP] Reduzindo irritação --> {self.angry_value}")
            self.set_shape("HappyExpression", 1.0)
            
        elif emocao == "triste":
            self.set_shape("SadExpression", 0.5)
            
        elif emocao == "irritado":
            if self.angry_value < 5:
                valor_irritacao = 1.0 if random.randint(1, 2) == 1 else 0.5
                self.set_shape("AngryExpression", valor_irritacao)
                self.angry_value += random.randint(1, 3) # Aumenta a raiva aos poucos
            else:
                self.angry_value += random.randint(5, 10)
                print(f"[APP] Muito irritado! Nível de raiva --> {self.angry_value}")
                self.set_shape("AngryExpression", 1.0)
                
        elif emocao == "confuso":
            self.set_shape("DeformFace", 0.5)
            
        elif emocao == "surpreso":
            self.set_shape("SurpriseExpression", 1.0)
            self.set_shape("EyebrownUp", 1.0)
            
        elif emocao == "curioso":
            self.set_shape("EyebrownUp", 0.7)
            
        elif emocao == "animado":
            self.set_shape("HappyExpression", 0.5)
            self.set_shape("EyebrownUp", 0.4)
            
        elif emocao == "Blink":
            # Delega para a função com timer, sem usar time.sleep e sem criar clones do loop
            self._animar_blink(autonomo=False)

    def falando(self, estado):
        # Atualiza a flag de inatividade
        self.is_speaking = estado
        
        # Se parar de falar, fecha a boca e foca a visão no centro
        if not estado:
            self.set_shape("MouthOpen", 0.0)
            self.set_olhar("centro")

    def set_olhar(self, direcao):
        self._enviar_comando(f"OLHAR {direcao}")

    def set_estado(self, estado):
        try:
            self.avatar_manager._trocar_estado(estado)
        except Exception:
            pass

    def closeEvent(self, event):
        if self.processo_panda:
            self.processo_panda.terminate()
        super().closeEvent(event)


# ==========================================================
# App
# ==========================================================

class App(Interface):

    mensagem_enviada = Signal(str)
    microfone_ativado = Signal()
    microfone_desativado = Signal()
    encerrando = Signal()

    def __init__(
        self,
        brain,
        avatar,
        tts=None,
        stt=None,
        memoria=None,
        eventos=None,
        config=None
    ):
        super().__init__()

        self.brain = brain
        self.avatar_manager = avatar
        self.tts = tts
        self.stt = stt
        self.memoria = memoria
        self.eventos = eventos
        self.config = config

        self.panda = PandaWidget(self.avatar_manager, self.eventos)
        self.adicionarAvatar(self.panda)

        self.toolbar = ToolBar()
        self.chat = ChatPanel()
        self.legenda = Legenda()
        self.settings = Settings(config)

        self.adicionarWidgets(
            self.toolbar,
            self.legenda,
            self.chat
        )

        self.chat.enviar.connect(self._enviar)
        self.toolbar.iniciar.connect(self.microfone_ativado.emit)
        self.toolbar.parar.connect(self.microfone_desativado.emit)
        self.toolbar.limpar.connect(self.chat.limpar)

    @property
    def avatar(self):
        return self.panda.avatar_view

    def _enviar(self, texto):
        # CORREÇÃO DO ECO: A linha abaixo foi comentada para evitar texto duplicado
        # assumindo que os eventos de stt/entrada_usuario já alimentam a interface
        # self.chat.adicionar_usuario(texto)
        
        self.mensagem_enviada.emit(texto)

    def receber(self, texto):
        self.chat.adicionar_aldo(texto)

    def closeEvent(self, event):
        self.encerrando.emit()
        if hasattr(self, 'panda') and self.panda:
            self.panda.closeEvent(event)
        super().closeEvent(event)