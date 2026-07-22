from abc import ABC, abstractmethod


class BasePlugin(ABC):

    nome = "Plugin"
    descricao = ""
    versao = "1.0"
    autor = ""
    prioridade = 0
    habilitado = True

    def iniciar(self, ctx):
        return

    def finalizar(self, ctx):
        return

    @abstractmethod
    def aceita(self, texto: str) -> bool:
        pass

    @abstractmethod
    def run(self, ctx, texto: str):
        pass

    def __repr__(self):
        return f"<Plugin {self.nome} v{self.versao}>"