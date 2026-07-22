from __future__ import annotations

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton
)


class Settings(QWidget):

    salvar = Signal(dict)

    def __init__(self,config):

        super().__init__()

        self.config=config

        self._montar()

    # -------------------------------------------------

    def _montar(self):

        layout=QFormLayout(self)

        self.modelo=QComboBox()

        self.modelo.addItems([
            "gemma2:2b",
            "gemma3:4b",
            "mistral",
            "phi4"
        ])

        self.historico=QSpinBox()

        self.historico.setRange(2,30)

        self.temperatura=QDoubleSpinBox()

        self.temperatura.setRange(0,2)

        self.temperatura.setSingleStep(0.05)

        self.microfone=QCheckBox()

        self.legendas=QCheckBox()

        self.avatar=QCheckBox()

        layout.addRow("Modelo",self.modelo)

        layout.addRow("Histórico",self.historico)

        layout.addRow("Temperatura",self.temperatura)

        layout.addRow("Usar microfone",self.microfone)

        layout.addRow("Mostrar legendas",self.legendas)

        layout.addRow("Avatar",self.avatar)

        self.btSalvar=QPushButton("Salvar")

        layout.addRow(self.btSalvar)

        self.btSalvar.clicked.connect(

            self._salvar

        )

        self.carregar()

    # -------------------------------------------------

    def carregar(self):

        self.modelo.setCurrentText(

            self.config.get(
                "modelo",
                "gemma2:2b"
            )
        )

        self.historico.setValue(

            self.config.get(
                "historico",
                8
            )
        )

        self.temperatura.setValue(

            self.config.get(
                "temperature",
                0.7
            )
        )

        self.microfone.setChecked(

            self.config.get(
                "microfone",
                True
            )
        )

        self.legendas.setChecked(

            self.config.get(
                "legendas",
                True
            )
        )

        self.avatar.setChecked(

            self.config.get(
                "avatar",
                True
            )
        )

    # -------------------------------------------------

    def _salvar(self):

        dados={

            "modelo":
                self.modelo.currentText(),

            "historico":
                self.historico.value(),

            "temperature":
                self.temperatura.value(),

            "microfone":
                self.microfone.isChecked(),

            "legendas":
                self.legendas.isChecked(),

            "avatar":
                self.avatar.isChecked()

        }

        self.salvar.emit(dados)