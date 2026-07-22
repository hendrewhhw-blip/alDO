from collections import defaultdict
import logging
import traceback


class EventBus:
    """
    Barramento de eventos do Aldo.

    Permite comunicação desacoplada entre módulos.
    """

    def __init__(self, logger=None):

        self._callbacks = defaultdict(list)

        self.logger = logger or logging.getLogger("EventBus")

    # --------------------------------------------------

    def on(self, evento, callback):
        """Registra um callback."""

        if callback not in self._callbacks[evento]:
            self._callbacks[evento].append(callback)

    # --------------------------------------------------

    def once(self, evento, callback):
        """Executa apenas uma vez."""

        def wrapper(*args, **kwargs):

            self.off(evento, wrapper)

            return callback(*args, **kwargs)

        self.on(evento, wrapper)

    # --------------------------------------------------

    def off(self, evento, callback):
        """Remove um callback."""

        try:
            self._callbacks[evento].remove(callback)

            if not self._callbacks[evento]:
                del self._callbacks[evento]

        except (ValueError, KeyError):
            pass

    # --------------------------------------------------

    def emit(self, evento, *args, **kwargs):
        """
        Emite um evento.

        Retorna uma lista com todos os retornos
        dos callbacks.
        """

        respostas = []

        callbacks = list(self._callbacks.get(evento, []))

        for callback in callbacks:

            try:

                respostas.append(

                    callback(*args, **kwargs)

                )

            except Exception:

                self.logger.exception(

                    f"Erro no evento '{evento}'"

                )

        return respostas

    # --------------------------------------------------

    def existe(self, evento):

        return evento in self._callbacks

    # --------------------------------------------------

    def quantidade(self, evento=None):

        if evento is None:

            return sum(

                len(x)

                for x in self._callbacks.values()

            )

        return len(

            self._callbacks.get(evento, [])

        )

    # --------------------------------------------------

    def limpar(self):

        self._callbacks.clear()

    # --------------------------------------------------

    def listar(self):

        return {

            evento: [

                cb.__name__

                for cb in callbacks

            ]

            for evento, callbacks

            in self._callbacks.items()

        }

    # --------------------------------------------------

    def __len__(self):

        return self.quantidade()

    # --------------------------------------------------

    def __contains__(self, evento):

        return evento in self._callbacks

    # --------------------------------------------------

    def __repr__(self):

        return (

            f"<EventBus "

            f"eventos={len(self._callbacks)} "

            f"callbacks={self.quantidade()}>"

        )