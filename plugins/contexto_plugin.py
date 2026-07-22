from dataclasses import dataclass, field


@dataclass(slots=True)
class PluginContext:

    # Núcleo

    eventos: object

    memoria: object

    brain: object

    config: object

    # Serviços

    avatar: object = None

    tts: object = None

    stt: object = None

    interface: object = None

    logger: object = None

    ollama: object = None

    # Compartilhamento entre plugins

    shared: dict = field(default_factory=dict)

    # ------------------------------------------

    def emitir(self, evento):

        return self.eventos.emit(evento)

    # ------------------------------------------

    def lembrar(self, texto):

        return self.memoria.lembrar_unico(texto)

    # ------------------------------------------

    def esquecer(self, texto):

        return self.memoria.remover_memoria(texto)

    # ------------------------------------------

    def trocar_personalidade(self, nome):

        return self.memoria.trocar_personalidade(nome)

    # ------------------------------------------

    def salvar_estado(self, **kwargs):

        return self.memoria.salvar_estado(**kwargs)

    # ------------------------------------------

    def responder(self, texto):
        if not self.brain:
            raise RuntimeError("Brain não inicializado")
        return self.brain.responder(texto)

    # ------------------------------------------

    def falar(self, texto):

        if self.tts:

            return self.tts.falar(texto)
        else:
            print("[Plugin] TTS não disponível")

    # ------------------------------------------

    def log(self, *args):

        if self.logger:

            self.logger.info(" ".join(map(str, args)))

        else:

            print("[Plugin]", " ".join(map(str, args)))