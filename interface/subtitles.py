from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel


class Subtitles(QLabel):

    def __init__(self):

        super().__init__()

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setWordWrap(True)

        self.setMinimumHeight(70)

        self.setText("")

        self.setStyleSheet("""
            QLabel{
                color:white;
                background:rgba(0,0,0,170);
                border-radius:12px;
                padding:12px;
                font-size:18px;
                font-weight:bold;
            }
        """)

        self.timer = QTimer()

        self.timer.setSingleShot(True)

        self.timer.timeout.connect(
            self.clear
        )

    # -------------------------------------------------

    def mostrar(
        self,
        texto,
        tempo=None
    ):

        self.setText(texto)

        self.show()

        if tempo is None:

            tempo = max(
                2500,
                len(texto) * 65
            )

        self.timer.start(tempo)

    # -------------------------------------------------

    def ocultar(self):

        self.timer.stop()

        self.clear()

    # -------------------------------------------------

    def adicionarToken(self, token):

        self.setText(
            self.text() + token
        )

    # -------------------------------------------------

    def finalizar(self):

        self.timer.start(2500)