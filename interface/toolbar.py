from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QComboBox
)


class ToolBar(QWidget):

    modoAlterado = Signal(str)

    iniciar = Signal()

    parar = Signal()

    limpar = Signal()

    def __init__(self):

        super().__init__()

        self._montar()

    # -------------------------------------------------

    def _montar(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(6,6,6,6)

        self.status = QLabel("● Offline")

        self.status.setMinimumWidth(90)

        layout.addWidget(self.status)

        layout.addStretch()

        self.modo = QComboBox()

        self.modo.addItems([
            "Terminal",
            "Microfone"
        ])

        layout.addWidget(self.modo)

        self.btIniciar = QPushButton("Iniciar")

        self.btParar = QPushButton("Parar")

        self.btLimpar = QPushButton("Limpar")

        layout.addWidget(self.btIniciar)

        layout.addWidget(self.btParar)

        layout.addWidget(self.btLimpar)

        self.modo.currentTextChanged.connect(
            self.modoAlterado.emit
        )

        self.btIniciar.clicked.connect(
            self.iniciar.emit
        )

        self.btParar.clicked.connect(
            self.parar.emit
        )

        self.btLimpar.clicked.connect(
            self.limpar.emit
        )

    # -------------------------------------------------

    def setStatus(self, texto):

        self.status.setText(texto)

    # -------------------------------------------------

    def modoAtual(self):

        return self.modo.currentText().lower()

    # -------------------------------------------------

    def usarMicrofone(self):

        self.modo.setCurrentIndex(1)

    # -------------------------------------------------

    def usarTerminal(self):

        self.modo.setCurrentIndex(0)