from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel


class Legenda(QLabel):

    def __init__(self):

        super().__init__()

        self.setAlignment(Qt.AlignCenter)

        self.setWordWrap(True)

        self.setText("")

        self.setVisible(False)

        self.setStyleSheet("""
            QLabel{
                background:rgba(0,0,0,180);
                color:white;
                border-radius:12px;
                padding:12px;
                font-size:18px;
                font-weight:bold;
            }
        """)

        self.timer = QTimer(self)

        self.timer.setSingleShot(True)

        self.timer.timeout.connect(self.ocultar)

    # -------------------------------------------------

    def mostrar(self,texto,tempo=None):

        self.setVisible(True)

        self.setText(texto)

        if tempo is None:

            tempo=max(
                2000,
                len(texto)*60
            )

        self.timer.start(tempo)

    # -------------------------------------------------

    def adicionar(self,token):

        self.setVisible(True)

        self.setText(self.text()+token)

    # -------------------------------------------------

    def finalizar(self):

        self.timer.start(2000)

    # -------------------------------------------------

    def ocultar(self):

        self.timer.stop()

        self.clear()

        self.setVisible(False)