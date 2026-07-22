from __future__ import annotations

import re


class StreamBuffer:
    """
    Recebe tokens do modelo e libera frases completas.

    Exemplo:

    Entrada:
        "Olá "
        "como "
        "vai?"
        " Tudo "
        "bem."

    Saída:
        "Olá como vai?"
        "Tudo bem."
    """

    _SEPARADOR = re.compile(r"(?<=[.!?:])\s+")

    def __init__(self):

        self.buffer = ""

    # -------------------------------------------------

    def adicionar(self, token):

        self.buffer += token

        frases = self._SEPARADOR.split(self.buffer)

        if len(frases) <= 1:
            return []

        self.buffer = frases[-1]

        return [

            f.strip()

            for f in frases[:-1]

            if f.strip()

        ]

    # -------------------------------------------------

    def finalizar(self):

        resto = self.buffer.strip()

        self.buffer = ""

        if resto:

            return [resto]

        return []

    # -------------------------------------------------

    def limpar(self):

        self.buffer = ""