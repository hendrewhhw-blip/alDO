import re
from core.messages import ChatMessage


class PromptBuilder:

    def __init__(self, memoria, contexto):

        self.memoria = memoria

        self.contexto = contexto

    # -------------------------------------------------

    def build(
        self,
        historico,
        ultima_resposta="",
        texto_usuario="",
        humor_atual="neutro"  # <--- Recebe o humor do Brain
    ):

        prompt = self.contexto.gerar(
            historico,
            ultima_resposta
        )

        # 2. Busca Inteligente de Memória (Zero RAM)
        if texto_usuario:

            # Extrai palavras com 4 ou mais letras
            palavras = set(re.findall(r'\b[a-zÀ-ÿ0-9]{4,}\b', texto_usuario.lower()))

            memorias_relevantes = set()

            # Varre o memoria.md atrás de cada palavra-chave
            for palavra in palavras:
                resultados = self.memoria.procurar(palavra)
                memorias_relevantes.update(resultados)

            # Se encontrou algo, injeta no prompt
            if memorias_relevantes:
                fatos = "\n".join(f"- {m}" for m in memorias_relevantes)
                prompt += (
                    "\n\n--- INFORMAÇÕES RELEVANTES DA MEMÓRIA ---\n"
                    "Considere os seguintes fatos de conversas passadas para responder:\n"
                    f"{fatos}\n"
                )

        # ====== MOTOR DE EMOÇÕES (A parte que faltava) ======
        prompt += (
            f"\n\n--- SEU ESTADO EMOCIONAL ---\n"
            f"Seu humor atual é: {humor_atual.upper()}.\n"
            "Aja e responda de acordo com esse humor. Se a fala do usuário mudar os seus sentimentos "
            "(ex: ele te elogiou, te xingou, ou contou algo triste), você DEVE sinalizar a mudança"
            "adicionando a seguinte tag no FINAL da sua resposta: [HUMOR: estado]\n"
            "Estados permitidos: feliz, triste, irritado, neutro, animado, confuso, surpresso.\n"
            "Exemplo: 'Poxa, isso que você disse me deixou chateado. [HUMOR: triste]'"
        )

        # 3. Monta a estrutura final de mensagens para a LLM
        mensagens = [
            ChatMessage.system(prompt)
        ]

        mensagens.extend(
            historico.copy()
        )

        return mensagens

    # -------------------------------------------------

    def rapido(self):

        return [
            ChatMessage.system(
                self.contexto.gerar_curto()
            )
        ]