from pathlib import Path
import json
import threading


class Config:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):

        with cls._lock:

            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()

        return cls._instance

    # ----------------------------------------------------

    def _init(self):

        self.base = Path(__file__).parent
        self.path = self.base / "config.json"

        if not self.path.exists():
            self.criar_padrao()

        self.recarregar()

    # ----------------------------------------------------

    def criar_padrao(self):

        dados = {

            "modelo": {
                "ollama": "gemma2:2b",
                "temperatura": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 100
            },

            "audio": {
                "whisper": "tiny",
                "sample_rate": 16000,
                "sensibilidade": 0.01,
                "tempo_silencio": 1.0
            },

            "tts": {
                "voice": "pt_BR-faber-medium.onnx",
                "speed": 1.0,
                "volume": 1.0
            },

            "avatar": {
                "ativo": True,
                "fps": 60,
                "boca_min": 5,
                "boca_max": 40
            },

            "memoria": {
                "historico": 6,
                "salvar_conversas": True,
                "contexto_maximo": 10
            },

            "interface": {
                "tema": "dark",
                "mostrar_whisper": True
            },

            "debug": False

        }

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                dados,
                f,
                indent=4,
                ensure_ascii=False
            )

    # ----------------------------------------------------

    def recarregar(self):

        with open(self.path, encoding="utf-8") as f:
            self.dados = json.load(f)

    # ----------------------------------------------------

    def salvar(self):

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                self.dados,
                f,
                indent=4,
                ensure_ascii=False
            )

    # ----------------------------------------------------

    def get(self, caminho, default=None):

        atual = self.dados

        for chave in caminho.split("."):

            if isinstance(atual, dict) and chave in atual:
                atual = atual[chave]
            else:
                return default

        return atual

    # ----------------------------------------------------

    def set(self, caminho, valor):

        atual = self.dados

        partes = caminho.split(".")

        for chave in partes[:-1]:

            if chave not in atual:
                atual[chave] = {}

            atual = atual[chave]

        atual[partes[-1]] = valor

        self.salvar()

    # ----------------------------------------------------

    def existe(self, caminho):

        return self.get(caminho) is not None

    # ----------------------------------------------------

    def remover(self, caminho):

        partes = caminho.split(".")

        atual = self.dados

        for chave in partes[:-1]:

            if chave not in atual:
                return

            atual = atual[chave]

        atual.pop(partes[-1], None)

        self.salvar()

    # ----------------------------------------------------

    def atualizar(self, dicionario):

        self.dados.update(dicionario)

        self.salvar()

    # ----------------------------------------------------

    def imprimir(self):

        print(json.dumps(
            self.dados,
            indent=4,
            ensure_ascii=False
        ))

    # ----------------------------------------------------

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, item, valor):
        self.set(item, valor)