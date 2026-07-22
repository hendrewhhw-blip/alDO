from __future__ import annotations

import logging
import time

from core.messages import (
    ChatMessage,
    MessageHistory
)

from core.prompt_builder import PromptBuilder
from core.ollama_client import OllamaClient
from core.resposta import (
    Origem,
    Resposta
)
from core.stream_buffer import StreamBuffer

from plugins.plugin_manager import PluginManager

import re
import random

def extrair_fatos_usuario(texto: str) -> list[str]:
    """
    Analisa a fala do usuário e extrai fatos para a memória
    usando padrões da língua portuguesa.
    """
    texto = texto.lower().strip()
    fatos_extraidos = []

    # 1. Padrões de identidade (Nome, idade, profissão)
    # Ex: "meu nome é João", "sou arquiteto", "tenho 30 anos"
    padroes_identidade = [
        (r'meu nome (?:é|e) ([a-zÀ-ÿ\s]+)', "O nome do usuário é {}"),
        (r'eu me chamo ([a-zÀ-ÿ\s]+)', "O nome do usuário é {}"),
        (r'(?:eu )?sou (?:um |uma )?([a-zÀ-ÿ\s]+) (?:e |mas|\.)', "A profissão/característica do usuário é {}"), # Requer um terminador para não pegar frase inteira
        (r'tenho (\d{1,3}) anos', "O usuário tem {} anos")
    ]

    # 2. Padrões de posse e relacionamento
    # Ex: "minha esposa chama Maria", "meu cachorro morreu"
    padroes_posse = [
        (r'm(?:eu|inha) ([a-zÀ-ÿ]+) (?:chama|se chama|é) ([a-zÀ-ÿ\s]+)', "A/O {} do usuário se chama {}"),
        (r'eu tenho (?:um|uma) ([a-zÀ-ÿ\s]+)', "O usuário tem um/uma {}")
    ]

    # 3. Gostos e desgostos
    # Ex: "eu adoro pizza", "eu odeio acordar cedo"
    padroes_gosto = [
        (r'(?:eu )?(gosto muito de|adoro|amo) ([a-zÀ-ÿ\s]+)', "O usuário adora {}"),
        (r'(?:eu )?(não gosto de|odeio|detesto) ([a-zÀ-ÿ\s]+)', "O usuário odeia {}")
    ]

    # 4. Comandos diretos explícitos (Fallback)
    # Ex: "Aldo, lembre que eu sou alérgico a camarão"
    padroes_comando = [
        (r'(?:lembre que|lembre-se que|guarde que|anote que) (.*)', "O usuário pediu para lembrar que: {}")
    ]

    todas_regras = padroes_identidade + padroes_posse + padroes_gosto + padroes_comando

    # Aplica as regras
    for regex, formato in todas_regras:
        matches = re.finditer(regex, texto)
        for match in matches:
            grupos = match.groups()
            
            # Limpa espaços extras no final da captura
            grupos_limpos = [g.strip() for g in grupos]
            
            # Formata a string final
            fato = formato.format(*grupos_limpos)
            
            # Evita capturas muito longas que provavelmente são falso positivos
            if len(fato) < 100: 
                fatos_extraidos.append(fato)

    return fatos_extraidos


class Brain:
    """
    Cérebro principal do Aldo.

    Responsável por:

    • construir o contexto
    • conversar com o modelo
    • controlar memória
    • emitir eventos
    • coordenar plugins

    Toda regra pesada permanece desacoplada em
    outros módulos.
    """

    # --------------------------------------------------

    def __init__(
        self,
        memoria,
        contexto,
        eventos,
        config,
        falar_fn=None,
        ouvir_fn=None,
        logger=None
    ):

        # Serviços principais

        self.memoria = memoria
        self.contexto = contexto
        self.eventos = eventos
        self.config = config

        self.falar = falar_fn
        self.ouvir = ouvir_fn

        # Logger

        self.logger = logger or logging.getLogger("Aldo")

        # Estado permanente

        self._estado = self.memoria.carregar_estado()

        # Modelo

        self.llm = OllamaClient(

            model=self.config.get(
                "modelo.ollama",
                "gemma2:2b"
            )
        )

        # Histórico

        self.historico = MessageHistory(

            limite=self.config.get(
                "memoria.historico",
                8
            )
        )

        # Prompt Builder

        self.prompt_builder = PromptBuilder(

            memoria=self.memoria,

            contexto=self.contexto
        )

        # Plugins

        self.plugins = PluginManager(

            self.eventos
        )

        self.plugins.carregar()

        # Stream

        self.stream_buffer = StreamBuffer()

        # Controle

        self.iniciado = False

        self.ultima_interacao = time.time()

        self.ultimo_usuario = ""

        self.ultima_resposta = ""
        
        # Carregar emoções
        self.gatilhos = self._carregar_gatilhos()

    # --------------------------------------------------

    @property
    def humor(self):

        return self._estado.get(

            "humor",

            "neutro"
        )

    # --------------------------------------------------

    @property
    def energia(self):

        return self._estado.get(

            "energia",

            5
        )

    # --------------------------------------------------

    @property
    def personalidade(self):

        return self._estado.get(

            "personalidade",

            "normal"
        )

    # --------------------------------------------------

    @property
    def tempo_ocioso(self):

        return time.time() - self.ultima_interacao

    # --------------------------------------------------

    def aquecer(self):

        self.logger.info(

            "Aquecendo modelo..."

        )

        return self.llm.aquecer()

    # --------------------------------------------------

    def iniciar(self):

        """
        Executado apenas uma vez
        quando o Aldo inicia.
        """

        if self.iniciado:

            return

        self.iniciado = True

        self.eventos.emit(

            "startup"
        )

        return self.config.get(

            "mensagem_inicial",

            "Olá."
        )
    def _carregar_gatilhos(self):
        import json
        from pathlib import Path
        
        
        # Garante que busca na raiz do projeto, independente de onde o arquivo está
        caminho_eventos = Path(__file__).resolve().parent.parent / "config" / "eventos.json"
        
        print(f"[DEBUG] Procurando JSON em: {caminho_eventos}")
        
        if not caminho_eventos.exists():
            print(f"[ERRO] ARQUIVO NÃO ENCONTRADO EM: {caminho_eventos}")
            return []
            
        try:
            with open(caminho_eventos, "r", encoding="utf-8") as f:
                dados = json.load(f)
                print(f"[DEBUG] JSON lido com sucesso. Gatilhos: {dados}")
                return dados
        except Exception as e:
            print(f"[ERRO] Falha ao ler JSON: {e}")
            return []

    # --------------------------------------------------

    def registrar_usuario(

        self,

        texto: str

    ):

        self.ultimo_usuario = texto

        self.ultima_interacao = time.time()

        self.historico.user(texto)

    # --------------------------------------------------

    def registrar_resposta(

        self,

        texto: str

    ):

        self.ultima_resposta = texto

        self.historico.assistant(texto)

    # --------------------------------------------------

    def limpar_historico(self):

        self.historico.clear()

    # --------------------------------------------------

    def trocar_modelo(

        self,

        modelo: str

    ):

        self.llm.trocar_modelo(modelo)

    # --------------------------------------------------

    def trocar_personalidade(

        self,

        nome: str

    ):

        self.memoria.trocar_personalidade(nome)

        self._estado["personalidade"] = nome
        # --------------------------------------------------
    # Conversa
    # --------------------------------------------------

    def responder(self, texto: str) -> Resposta:
            texto = texto.strip()

            if not texto:
                return Resposta(texto="", origem=Origem.SISTEMA)

            # 1. Atualiza histórico e registro básico
            self.registrar_usuario(texto)
            texto_lower = texto.lower()
# ------------------------------------------
        # CAPTURA DE GATILHOS (debug com print)
        # ------------------------------------------
            mudancas_estado = {}
            
            # Este print vai aparecer sempre que você enviar uma mensagem
            print(f"[DEBUG] Testando texto: '{texto_lower}'")
            print(f"[DEBUG] Quantidade de gatilhos carregados: {len(self.gatilhos)}")

            for evento in self.gatilhos:
                termo = evento["gatilho"].lower()
                
                # Se o gatilho estiver no texto, faz o match
                if termo in texto_lower:
                    print(f"[DEBUG] MATCH ENCONTRADO! Gatilho: '{termo}' -> Estado: {evento['tipo']}={evento['valor']}")
                    mudancas_estado[evento["tipo"]] = evento["valor"]
            
            if mudancas_estado:
                print(f"[DEBUG] Aplicando mudanças: {mudancas_estado}")
                self.atualizar_estado(**mudancas_estado)

            # ------------------------------------------
            # CAPTURA DE MEMÓRIA (Lembrar disso/Extração)
            # ------------------------------------------
            # Salva contexto anterior ("aldo, guarda isso")
            if "lembra disso" in texto_lower or "guarda isso" in texto_lower:
                if self.ultima_resposta:
                    self.lembrar(f"Contexto salvo de conversa anterior: {self.ultima_resposta}")
                    self.logger.info("Última resposta salva na memória.")

            # Extração automática por padrões
            novos_fatos = extrair_fatos_usuario(texto)
            for fato in novos_fatos:
                self.lembrar(fato)
                self.logger.info(f"Fato salvo na memória: {fato}")

            # ------------------------------------------
            # Plugins de entrada
            # ------------------------------------------
            resposta = self.plugins.entrada(texto, brain=self)
            if resposta is not None:
                if resposta.salvar_historico:
                    self.registrar_resposta(resposta.texto)
                return resposta

            # Evento
            self.eventos.emit("entrada_usuario", texto=texto)

            # ------------------------------------------
            # Montagem do prompt (Incluindo humor atual)
            # ------------------------------------------
            mensagens = self.prompt_builder.build(
                historico=self.historico,
                ultima_resposta=self.ultima_resposta,
                texto_usuario=texto,
                humor_atual=self.humor  # Passando o estado atual para o builder
            )

            # Plugins antes LLM
            self.eventos.emit("antes_llm", mensagens=mensagens)

            # Modelo
            resposta = self._executar_modelo(mensagens)

            # ------------------------------------------
            # CAPTURA DE MUDANÇA DE HUMOR (Tag [HUMOR:...])
            # ------------------------------------------
            match_humor = re.search(r'\[HUMOR:\s*([a-zA-ZÀ-ÿ]+)\]', resposta.texto, re.IGNORECASE)
            if match_humor:
                novo_humor = match_humor.group(1).lower().strip()
                self.atualizar_estado(humor=novo_humor)
                self.logger.info(f"O humor do Aldo mudou para: {novo_humor}")
                
                # Remove a tag da resposta final para o usuário não visualizar
                resposta.texto = re.sub(r'\[HUMOR:\s*[a-zA-ZÀ-ÿ]+\]', '', resposta.texto, flags=re.IGNORECASE).strip()

            # ------------------------------------------
            # Finalização e Eventos
            # ------------------------------------------
            self.eventos.emit("depois_llm", resposta=resposta)

            modificada = self.plugins.saida(resposta, brain=self)
            if modificada is not None:
                resposta = modificada

            if resposta.salvar_historico:
                self.registrar_resposta(resposta.texto)

            self.memoria.salvar_conversa(texto, resposta)
            self.eventos.emit("resposta_pronta", resposta=resposta)

            return resposta
    # --------------------------------------------------

    def pensar(self):
        """
        Chamado continuamente pelo main.

        Permite comportamentos proativos,
        timers e plugins.
        """

        return self.plugins.tick(

            brain=self

        )

    # --------------------------------------------------

    def interrompido(self) -> bool:
        """
        Verifica se o usuário começou
        a falar novamente.
        """

        if self.ouvir is None:

            return False

        try:

            return self.ouvir()

        except Exception:

            return False
        # --------------------------------------------------
    # Modelo
    # --------------------------------------------------

    def _executar_modelo(

        self,

        mensagens

    ) -> Resposta:

        resposta = Resposta()

        resposta.origem = Origem.LLM

        resposta.texto = ""

        inicio = time.perf_counter()

        self.stream_buffer.limpar()

        try:

            stream = self.llm.gerar_stream(

                mensagens

            )

            for token in stream:

                # ----------------------------------
                # Usuário interrompeu
                # ----------------------------------

                if self.interrompido():

                    resposta.interrompida = True

                    resposta.texto = resposta.texto.strip()

                    resposta.tempo = (

                        time.perf_counter()

                        - inicio

                    )

                    self.eventos.emit(

                        "fala_interrompida",

                        resposta=resposta

                    )

                    return resposta

                # ----------------------------------
                # Texto completo
                # ----------------------------------

                resposta.texto += token

                # ----------------------------------
                # Buffer de frases
                # ----------------------------------

                frases = self.stream_buffer.adicionar(

                    token

                )

                for frase in frases:

                    self.eventos.emit(

                        "frase_pronta",

                        frase=frase,

                        resposta=resposta

                    )

                # ----------------------------------
                # Streaming
                # ----------------------------------

                self.eventos.emit(

                    "token_recebido",

                    token=token

                )

            # --------------------------------------
            # Última frase
            # --------------------------------------

            for frase in self.stream_buffer.finalizar():

                self.eventos.emit(

                    "frase_pronta",

                    frase=frase,

                    resposta=resposta

                )

            resposta.texto = resposta.texto.strip()

            resposta.tempo = (

                time.perf_counter()

                - inicio

            )

        except Exception as erro:

            self.logger.exception(erro)

            resposta.origem = Origem.SISTEMA

            resposta.texto = (

                "Ocorreu um erro durante a geração da resposta."

            )

            resposta.adicionar_extra(

                "erro",

                str(erro)

            )

            return resposta

        return resposta

    # --------------------------------------------------

    def info(self):

        return {

            "modelo": self.llm.nome_modelo,

            "humor": self.humor,

            "energia": self.energia,

            "personalidade": self.personalidade,

            "historico": len(

                self.historico

            ),

            "tempo_ocioso": round(

                self.tempo_ocioso,

                2

            ),

            "plugins": len(

                self.plugins.listar()

            )

        }

    # --------------------------------------------------

    def obter_estado(self):

        return self._estado.copy()
        # --------------------------------------------------
    # Estado
    # --------------------------------------------------

    def atualizar_estado(self, **kwargs):

        self._estado.update(kwargs)

        self.memoria.salvar_estado(**kwargs)
        if random.randint(0,1) == 1:
            self.eventos.emit("mudanca_estado", estado="Blink")
            print("|Piscando....            |")
        self.eventos.emit("mudanca_estado", estado=self._estado)

    # --------------------------------------------------

    def lembrar(self, texto):

        self.memoria.lembrar_unico(texto)

    # --------------------------------------------------

    def esquecer(self, texto):

        self.memoria.remover_memoria(texto)

    # --------------------------------------------------

    def procurar_memoria(self, texto):

        return self.memoria.procurar(texto)

    # --------------------------------------------------

    def resetar(self):

        self.historico.clear()

        self.stream_buffer.limpar()

        self.ultimo_usuario = ""

        self.ultima_resposta = ""

        self.ultima_interacao = time.time()

        self._estado = self.memoria.carregar_estado()

    # --------------------------------------------------

    def fechar(self):

        self.eventos.emit("shutdown")

        self.memoria.salvar_estado(

            **self._estado

        )

    # --------------------------------------------------

    def __call__(self, texto):

        return self.responder(texto)

    # --------------------------------------------------

    def __repr__(self):

        return (

            f"<Brain "

            f"modelo={self.llm.nome_modelo} "

            f"personalidade={self.personalidade}>"

        )
