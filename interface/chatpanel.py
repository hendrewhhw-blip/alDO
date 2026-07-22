from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QTextBrowser,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)


class ChatPanel(QWidget):

    enviar = Signal(str)

    def __init__(self):

        super().__init__()

        self._montar()

    # -------------------------------------------------

    def _montar(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0,0,0,0)

        layout.setSpacing(8)

        # Histórico

        self.chat = QTextBrowser()

        self.chat.setOpenExternalLinks(True)

        layout.addWidget(self.chat)

        # Entrada

        self.entrada = QTextEdit()

        self.entrada.setFixedHeight(90)

        self.entrada.setPlaceholderText(
            "Digite uma mensagem..."
        )

        layout.addWidget(self.entrada)

        # Botões

        linha = QHBoxLayout()

        self.bt_enviar = QPushButton("Enviar")

        self.bt_limpar = QPushButton("Limpar")

        linha.addWidget(self.bt_limpar)

        linha.addStretch()

        linha.addWidget(self.bt_enviar)

        layout.addLayout(linha)

        # Eventos

        self.bt_enviar.clicked.connect(
            self._enviar
        )

        self.bt_limpar.clicked.connect(
            self.chat.clear
        )

    # -------------------------------------------------

    def _enviar(self):

        texto = self.texto()

        if not texto:

            return

        self.enviar.emit(texto)

        self.entrada.clear()

    # -------------------------------------------------

    def texto(self):

        return self.entrada.toPlainText().strip()

    # -------------------------------------------------

    def adicionar_usuario(self, texto):

        self.chat.append(
            f"<b>Você:</b> {texto}"
        )

    # -------------------------------------------------

    def adicionar_aldo(self, texto):

        self.chat.append(
            f"<span style='color:#6fd3ff'><b>Aldo:</b></span> {texto}"
        )

    # -------------------------------------------------

    def adicionar_sistema(self, texto):

        self.chat.append(
            f"<span style='color:gray'>{texto}</span>"
        )

    # -------------------------------------------------

    def adicionar_plugin(self, nome, texto):

        self.chat.append(
            f"<span style='color:#ffc857'><b>{nome}:</b></span> {texto}"
        )

    # -------------------------------------------------

    def limpar(self):

        self.chat.clear()

    # -------------------------------------------------

    def focar(self):

        self.entrada.setFocus()

    # -------------------------------------------------

    def set_enabled(self, estado):

        self.entrada.setEnabled(estado)

        self.bt_enviar.setEnabled(estado)

    # -------------------------------------------------

    def keyPressEvent(self, event):

        if (
            event.key() == Qt.Key_Return
            and not event.modifiers()
        ):

            self._enviar()

            return

        super().keyPressEvent(event)