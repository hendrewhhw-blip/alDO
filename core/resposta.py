from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import perf_counter
from contextlib import contextmanager
from typing import Any


# ==========================================================
# Origem da resposta
# ==========================================================

class Origem(Enum):

    LLM = "llm"

    PLUGIN = "plugin"

    MEMORIA = "memoria"

    SISTEMA = "sistema"

    EVENTO = "evento"


# ==========================================================
# Resposta
# ==========================================================

@dataclass(slots=True)
class Resposta:
    def __post_init__(self):
        if not isinstance(self.origem, Origem):
            raise TypeError(
              f"origem deve ser Origem, recebeu {type(self.origem).__name__}"
            )
    # Texto que será retornado
    texto: str = ""

    # Quem produziu
    origem: Origem = Origem.LLM

    # Deve falar utilizando o TTS?
    falar: bool = True

    # Deve salvar no histórico?
    salvar_historico: bool = True

    # Deve salvar na memória?
    salvar_memoria: bool = True

    # A resposta foi interrompida?
    interrompida: bool = False

    # Solicita encerramento do programa?
    finalizar: bool = False

    # Tempo gasto para produzir
    tempo: float = 0.0

    # Nome do plugin responsável (opcional)
    plugin: str | None = None

    # Dados extras
    extras: dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------

    @property
    def vazia(self) -> bool:

        return self.texto.strip() == ""

    # -----------------------------------------------------

    @property
    def sucesso(self) -> bool:

        return not self.vazia and not self.interrompida

    # -----------------------------------------------------

    def adicionar_extra(self, chave, valor):

        self.extras[chave] = valor

    # -----------------------------------------------------

    def obter(self, chave, padrao=None):

        return self.extras.get(chave, padrao)

    # -----------------------------------------------------

    def copiar(self):

        return Resposta(

            texto=self.texto,

            origem=self.origem,

            falar=self.falar,

            salvar_historico=self.salvar_historico,

            salvar_memoria=self.salvar_memoria,

            interrompida=self.interrompida,

            finalizar=self.finalizar,

            tempo=self.tempo,

            plugin=self.plugin,

            extras=self.extras.copy()

        )

    # -----------------------------------------------------

    def __bool__(self):

        return not self.vazia


# ==========================================================
# Cronômetro
# ==========================================================

@contextmanager
def medir():

    inicio = perf_counter()

    resposta = Resposta()

    yield resposta

    resposta.tempo = perf_counter() - inicio