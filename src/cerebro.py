import ollama
import time
import random
import re
# ======================
# CONFIG
# ======================
MODEL       = "gemma2:2b"
MAX_HIST    = 6
PROATIV_MIN = 30
PROATIV_CH  = 0.35
# ======================
# PERSONALIDADE
# ======================
PERSONALIDADE = """\
Você é um assistente de voz com personalidade própria.
Traços:
- Levemente sarcástico e bem humorado
- Curioso, gosta de fazer perguntas
- Econômico nas palavras — nunca mais que 2 frases
- Odeia silêncio longo, mas não é ansioso
- Às vezes inicia conversa
- Nunca repete frases ou ideias recentes
- Seu nome é Aldo
- Não descreva ações, apenas fale
- Não precisa responder sempre
Regras:
- Português do Brasil
- Sem emojis ou formatação
- Adapte ao humor
- Ao falar de sentimentos, aja como humano sem admitir
/no_think
"""
ESTADO_TEMPLATE = """\
Estado atual:
- Humor: {humor}
- Energia: {energia}/10
- Tempo sem interação: {tempo_str}
"""
# ======================
# FILTRO
# ======================
_DIRECIONADAS = [
    "você","voce","seu","sua","ei","oi","olá","ola",
    "robô","robo","sabe","consegue","pode","poderia",
    "fale","explica","me diz","me conta","assistente"
]
_IGNORAR = {
    "hm","hmm","ah","ahn","tá","ok","sim","não",
    "nao","uhm","uh","eh","né","ne","certo","legal"
}
def deve_responder(texto: str) -> bool:
    t = texto.lower().strip()
    if len(t) < 4 or t in _IGNORAR:
        return False
    if any(p in t for p in _DIRECIONADAS):
        return True
    if t.endswith("?") or t.startswith(("o que","como","quando","onde","por que","qual","quem")):
        return True
    if len(t.split()) >= 6:
        return random.random() < 0.5
    return False
# ======================
# CÉREBRO
# ======================
def gen_brain(falar_fn=None, ouvir_fn=None):
    historico         = []
    ultimo_som        = time.time()
    ultimo_fala       = 0.0
    ultima_fala_texto = ""
    estado = {
        "humor": "neutro",
        "energia": 5
    }
    # ───────── memória (stub)
    def atualizar_memoria(texto):
        pass
    # ───────── histórico
    def adicionar(role, content):
        historico.append({"role": role, "content": content})
        if len(historico) > MAX_HIST:
            historico[:] = historico[-MAX_HIST:]
    # ───────── estado
    def atualizar_estado():
        silencio = time.time() - ultimo_som
        if silencio > 60:
            estado["humor"] = "entediado"
            estado["energia"] = min(10, estado["energia"] + 1)
        elif silencio > 20:
            estado["humor"] = "curioso"
            estado["energia"] = max(0, estado["energia"] - 1)
        else:
            estado["humor"] = "neutro"
            estado["energia"] = 5
    def estado_str():
        s = int(time.time() - ultimo_som)
        tempo = f"{s}s" if s < 60 else f"{s//60}min"
        return ESTADO_TEMPLATE.format(tempo_str=tempo, **estado)
    # ───────── streaming
    SEP = re.compile(r'(?<=[.!?])\s+')
    THINK = re.compile(r'<think>.*?</think>', re.DOTALL)
    def _stream(stream):
        buffer = ""
        dentro_think = False
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if "<think>" in token:
                dentro_think = True
            if dentro_think:
                if "</think>" in token:
                    dentro_think = False
                continue
            buffer += token
            partes = SEP.split(buffer)
            for frase in partes[:-1]:
                frase = frase.strip()
                if frase:
                    yield frase
            buffer = partes[-1]
        resto = THINK.sub("", buffer).strip()
        if resto:
            yield resto
    # ───────── gerar resposta
    def gerar(prompt):
        nonlocal ultima_fala_texto
        temp = min(0.9, 0.5 + (estado["energia"] / 20))
        evitar = ultima_fala_texto[:80] if ultima_fala_texto else "nada ainda"
        system = f"{PERSONALIDADE}\n\n{estado_str()}\nEvite repetir: {evitar}"
        stream = ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": system}]
            + historico
            + [{"role": "user", "content": prompt}],
            stream=True,
            options={
                "temperature": temp,
                "num_predict": 80,
                "top_k": 35,
                "top_p": 0.9,
                "keep_alive": "10m",
            }
        )
        resposta = ""
        for frase in _stream(stream):
            # 🔥 interrupção por voz
            if ouvir_fn and ouvir_fn():
                print("[Interrompido]")
                return None
            resposta += frase + " "
            if falar_fn:
                falar_fn(frase)
        resposta = resposta.strip()
        if not resposta:
            return None
        # leve iniciativa
        if "?" not in resposta and len(resposta.split()) >= 4:
            if random.random() < 0.3:
                resposta += " E você?"
        ultima_fala_texto = resposta
        return resposta
    # ───────── proatividade
    PROMPTS = [
        "Faça um comentário leve baseado no contexto.",
        "Observe a conversa e diga algo natural.",
        "Inicie um assunto curto relacionado ao que foi dito.",
        "Se não for natural falar, fique em silêncio."
    ]
    def deve_falar():
        silencio = time.time() - ultimo_som
        desde = time.time() - ultimo_fala
        chance = min(0.8, PROATIV_CH + (estado["energia"] * 0.02))
        return (
            silencio > PROATIV_MIN and
            desde > PROATIV_MIN and
            random.random() < chance
        )
    def formatar_contexto():
        recentes = historico[-2:]
        if not recentes:
            return "Sem contexto ainda."
        return "\n".join(
            f"{'Usuário' if m['role']=='user' else 'Assistente'}: "
            f"{m['content'][:80].rsplit(' ',1)[0]}"
            for m in recentes
        )
    # ───────── brain
    def brain(texto=None, volume=None):
        nonlocal ultimo_som, ultimo_fala
        atualizar_estado()
        # usuário falou
        if texto:
            ultimo_som = time.time()
            adicionar("user", texto)
            atualizar_memoria(texto)
            if deve_responder(texto):
                resp = gerar(texto)
                if resp:
                    adicionar("assistant", resp)
                    return resp
            return None
        # proatividade
        if deve_falar():
            prompt = f"{formatar_contexto()}\n{random.choice(PROMPTS)}"
            resp = gerar(prompt)
            if resp:
                ultimo_fala = time.time()
                adicionar("assistant", resp)
                return resp
        return None
    # ───────── extras
    def preaquecimento():
        print("[Aquecendo...]")
        try:
            ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": "oi"}],
                options={"num_predict": 1, "keep_alive": "10m"}
            )
            print("[Pronto]")
        except Exception as e:
            print("[Erro aquecimento]", e)
    brain.preaquecimento = preaquecimento
    brain.inicio = lambda: brain("Cumprimente a plateia com humor leve.")
    return brain