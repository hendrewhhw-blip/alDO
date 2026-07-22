from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
)

from PySide6.QtCore import Qt


class Interface(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Aldo")

        self.resize(1500, 900)

        self._montar()

    # -------------------------------------------------

    def _montar(self):

        central = QWidget()

        self.setCentralWidget(central)

        self.root = QHBoxLayout(central)

        self.root.setContentsMargins(8, 8, 8, 8)

        self.root.setSpacing(8)

        # ==================================================
        # Avatar
        # ==================================================

        self.avatar_frame = QFrame()

        self.avatar_frame.setObjectName("Avatar")

        self.avatar_frame.setMinimumWidth(700)

        self.avatar_layout = QVBoxLayout(self.avatar_frame)

        self.avatar_layout.setContentsMargins(0, 0, 0, 0)

        self.avatar_layout.setSpacing(0)

        self.root.addWidget(
            self.avatar_frame,
            3
        )

        # ==================================================
        # Painel direito
        # ==================================================

        self.side_panel = QWidget()

        self.side_panel.setMaximumWidth(430)

        self.side_layout = QVBoxLayout(self.side_panel)

        self.side_layout.setContentsMargins(0, 0, 0, 0)

        self.side_layout.setSpacing(8)

        self.root.addWidget(
            self.side_panel,
            1
        )

        self.side_layout.addStretch()

        # ==================================================

        self.setStyleSheet("""
        QWidget{
            background:#1d1f23;
            color:white;
            font-size:12pt;
        }

        #Avatar{
            background:#101114;
            border:1px solid #404040;
            border-radius:10px;
        }
        """)

    # -------------------------------------------------

    def adicionarAvatar(self, widget):

        self.avatar_layout.addWidget(widget)

    # -------------------------------------------------

    def adicionarWidget(self, widget):

        self.side_layout.insertWidget(

            self.side_layout.count() - 1,

            widget

        )

    # -------------------------------------------------

    def adicionarWidgets(self, *widgets):

        for widget in widgets:

            self.adicionarWidget(widget)