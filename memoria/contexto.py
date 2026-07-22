# config/contexto.py

from pathlib import Path
import time


class Contexto:

    def __init__(self, memoria):

        self.memoria = memoria

    # ----------------------------------------------------
    # Histórico recente
    # ----------------------------------------------------

    def historico_texto(self, historico, limite=8):

        if not historico:
            return ""

        texto = []

        for msg in historico[-limite:]:

            if isinstance(msg, dict):
                role = msg["role"]
                content = msg["content"]
            else:
                role = msg.role
                content = msg.content

            if role == "user":
                role = "Usuário"
            elif role == "assistant":
                role = "Aldo"

            texto.append(f"{role}: {content}")

        return "\n".join(texto)

    # ----------------------------------------------------
    # Monta o prompt completo
    # ----------------------------------------------------

    def gerar(
        self,
        historico,
        ultima_resposta=""
    ):

        estado = self.memoria.carregar_estado()

        prompt = []

        # ------------------------------
        # Sistema
        # ------------------------------

        sistema = self.memoria.ler_prompt("sistema.md")

        if sistema:

            prompt.append(sistema)

        # ------------------------------
        # Comportamento
        # ------------------------------

        comportamento = self.memoria.ler_prompt(
            "comportamento.md"
        )

        if comportamento:

            prompt.append(comportamento)

        # ------------------------------
        # Ferramentas
        # ------------------------------

        ferramentas = self.memoria.ler_prompt(
            "ferramentas.md"
        )

        if ferramentas:

            prompt.append(ferramentas)

        # ------------------------------
        # Personalidade
        # ------------------------------

        personalidade = self.memoria.personalidade()

        if personalidade:

            prompt.append(personalidade)

        # ------------------------------
        # Memória permanente
        # ------------------------------

        memoria = self.memoria.ler_memoria()

        if memoria:

            prompt.append(
                "# Memórias\n"
                + memoria
            )

        # ------------------------------
        # Estado atual
        # ------------------------------

        prompt.append(
            f"""
# Estado Atual

Humor: {estado.get("humor","neutro")}
Energia: {estado.get("energia",5)}/10
Personalidade: {estado.get("personalidade","normal")}
""".strip()
        )

        # ------------------------------
        # Evitar repetição
        # ------------------------------

        if ultima_resposta:

            prompt.append(
                f"""
# Última resposta

Evite repetir literalmente:

{ultima_resposta}
""".strip()
            )

        # ------------------------------
        # Histórico
        # ------------------------------

        hist = self.historico_texto(historico)

        if hist:

            prompt.append(
                "# Conversa recente\n"
                + hist
            )

        return "\n\n".join(prompt)

    # ----------------------------------------------------
    # Prompt resumido (modo rápido)
    # ----------------------------------------------------

    def gerar_curto(self):

        estado = self.memoria.carregar_estado()

        partes = [

            self.memoria.personalidade(),

            self.memoria.ler_memoria(),

            f"Humor: {estado.get('humor','neutro')}",

            f"Energia: {estado.get('energia',5)}/10"

        ]

        return "\n\n".join(
            p for p in partes if p
        )