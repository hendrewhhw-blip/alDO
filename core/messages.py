from __future__ import annotations

from dataclasses import dataclass
from typing import List, ClassVar


# ---------------------------------------------------------
# Mensagem
# ---------------------------------------------------------

@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    VALIDOS: ClassVar[set[str]] = {
        "system",
        "user",
        "assistant",
        "tool"
    }
    # -----------------------------------------------------
    def __post_init__(self):
        if self.role not in self.VALIDOS:
            raise ValueError(
                f"Role inválido: {self.role}"
            )
    @classmethod
    def system(cls, texto: str):
        return cls("system", texto)

    # -----------------------------------------------------

    @classmethod
    def user(cls, texto: str):
        return cls("user", texto)

    # -----------------------------------------------------

    @classmethod
    def assistant(cls, texto: str):
        return cls("assistant", texto)

    # -----------------------------------------------------

    @classmethod
    def tool(cls, texto: str):
        return cls("tool", texto)

    # -----------------------------------------------------

    def to_dict(self):

        return {
            "role": self.role,
            "content": self.content
        }

    # -----------------------------------------------------

    @classmethod
    def from_dict(cls, data):

        return cls(
            role=data["role"],
            content=data["content"]
        )

# ---------------------------------------------------------
# Histórico
# ---------------------------------------------------------

class MessageHistory:

    def __init__(self, limite=10):

        self.limite = limite

        self._messages: List[ChatMessage] = []

    # -----------------------------------------------------

    def add(self, message: ChatMessage):

        self._messages.append(message)

        self._trim()

    # -----------------------------------------------------

    def system(self, texto):

        self.add(ChatMessage.system(texto))

    # -----------------------------------------------------

    def user(self, texto):

        self.add(ChatMessage.user(texto))

    # -----------------------------------------------------

    def assistant(self, texto):

        self.add(ChatMessage.assistant(texto))

    # -----------------------------------------------------

    def tool(self, texto):

        self.add(ChatMessage.tool(texto))

    # -----------------------------------------------------

    def _trim(self):

        if len(self._messages) > self.limite:

            excesso = len(self._messages) - self.limite

            self._messages = self._messages[excesso:]

    # -----------------------------------------------------

    def clear(self):

        self._messages.clear()

    # -----------------------------------------------------

    def copy(self):

        return [
            ChatMessage(
                msg.role,
                msg.content
            )
            for msg in self._messages
        ]
    # -----------------------------------------------------

    def to_ollama(self):

        return [

            msg.to_dict()

            for msg in self._messages

        ]

    # -----------------------------------------------------

    def export(self):

        return self.to_ollama()

    # -----------------------------------------------------

    def importar(self, mensagens):

        self._messages = [

            ChatMessage.from_dict(m)

            for m in mensagens

        ]
        self._trim()

    # -----------------------------------------------------

    def ultimo(self):

        if self._messages:

            return self._messages[-1]

        return None

    # -----------------------------------------------------

    def ultimo_usuario(self):

        for msg in reversed(self._messages):

            if msg.role == "user":

                return msg

        return None

    # -----------------------------------------------------

    def ultimo_assistente(self):

        for msg in reversed(self._messages):

            if msg.role == "assistant":

                return msg

        return None

    # -----------------------------------------------------

    def __len__(self):

        return len(self._messages)

    # -----------------------------------------------------

    def __iter__(self):

        return iter(self._messages)

    # -----------------------------------------------------

    def __getitem__(self, index):

        return self._messages[index]