from __future__ import annotations

from typing import Iterator

import ollama

from core.messages import ChatMessage


class OllamaClient:

    DEFAULT_OPTIONS = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_predict": 120,
        "keep_alive": "15m",
    }

    def __init__(self, model="gemma2:2b", options=None):

        self.model = model

        self.options = self.DEFAULT_OPTIONS.copy()

        if options:
            self.options.update(options)

    # -------------------------------------------------

    def aquecer(self):

        try:

            ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": "oi"
                    }
                ],
                options={
                    "num_predict": 1,
                    "keep_alive": self.options["keep_alive"]
                }
            )

            return True

        except Exception as e:

            self.logger.exception(e)

            return False

    # -------------------------------------------------

    def trocar_modelo(self, nome):

        self.model = nome
    
    @property
    def nome_modelo(self):
        return self.model
    # -------------------------------------------------

    def atualizar_opcoes(self, **kwargs):
        VALID_OPTIONS = {
            "temperature",
            "top_p",
            "top_k",
            "num_predict",
            "keep_alive"
        }
        for chave in kwargs:

            if chave not in VALID_OPTIONS:
                raise ValueError(
                    f"Opção inválida: {chave}"
                )
            self.options.update(kwargs)
    # -------------------------------------------------

    def _converter(self, mensagens):

        convertido = []

        for msg in mensagens:

            if isinstance(msg, ChatMessage):

                convertido.append(msg.to_dict())

            elif isinstance(msg, dict):

                convertido.append(msg)

            else:

                raise TypeError(
                    f"Tipo inválido: {type(msg)}"
                )

        return convertido

    # -------------------------------------------------

    def gerar(self, mensagens, stream=False):

        mensagens = self._converter(mensagens)

        return ollama.chat(

            model=self.model,

            messages=mensagens,

            stream=stream,

            options=self.options

        )

    # -------------------------------------------------

    def gerar_texto(self, mensagens):

        resposta = self.gerar(
            mensagens,
            stream=False
        )

        return resposta["message"]["content"]

    # -------------------------------------------------

    def gerar_stream(
        self,
        mensagens
    ) -> Iterator[str]:

        stream = self.gerar(
            mensagens,
            stream=True
        )

        for chunk in stream:

            token = chunk.get(
                "message",
                {}
            ).get(
                "content",
                ""
            )

            if token:

                yield token

    # -------------------------------------------------

    def ping(self):

        try:

            ollama.list()

            return True

        except Exception:

            return False

    # -------------------------------------------------

    def info(self):

        return {

            "modelo": self.model,

            "opcoes": self.options.copy()

        }