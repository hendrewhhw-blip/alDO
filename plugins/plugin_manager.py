from __future__ import annotations

from pathlib import Path
import importlib.util
import traceback

from plugins.base_plugin import BasePlugin


class PluginManager:

    def __init__(self,eventos,pasta=None):

        self.eventos=eventos

        self.pasta=Path(
            pasta or Path(__file__).parent
        )

        self.plugins=[]

    # -------------------------------------------------

    def carregar(self):

        self.plugins.clear()

        for arquivo in sorted(self.pasta.glob("*.py")):

            if arquivo.stem.startswith("_"):
                continue

            if arquivo.stem in (
                "pluginmanager",
                "plugin_manager",
                "base_plugin",
                "contexto_plugin",
                "contexto",
                "eventos"
            ):
                continue

            try:

                spec=importlib.util.spec_from_file_location(
                    arquivo.stem,
                    arquivo
                )

                modulo=importlib.util.module_from_spec(spec)

                spec.loader.exec_module(modulo)
                if not hasattr(modulo,"Plugin"):
                    continue
                plugin=modulo.Plugin()

                if not isinstance(plugin,BasePlugin):
                    raise TypeError(
                        f"{arquivo.name} não herda BasePlugin."
                    )

                self.plugins.append(plugin)

            except Exception:

                traceback.print_exc()

        self.plugins.sort(
            key=lambda p:p.prioridade,
            reverse=True
        )

    # -------------------------------------------------

    def iniciar(self,ctx):

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:

                plugin.iniciar(ctx)

            except Exception:

                traceback.print_exc()

    # -------------------------------------------------

    def finalizar(self,ctx):

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:

                plugin.finalizar(ctx)

            except Exception:

                traceback.print_exc()

    # -------------------------------------------------

    def entrada(self,texto,**kwargs):

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:

                resposta=plugin.entrada(
                    texto,
                    **kwargs
                )

                if resposta is not None:
                    return resposta

            except Exception:

                traceback.print_exc()

        return None

    # -------------------------------------------------

    def saida(self,resposta,**kwargs):

        atual=resposta

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:

                nova=plugin.saida(
                    atual,
                    **kwargs
                )

                if nova is not None:
                    atual=nova

            except Exception:

                traceback.print_exc()

        return atual

    # -------------------------------------------------

    def tick(self,**kwargs):

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:
                if hasattr (plugin,"tick"):
                    plugin.tick(**kwargs)

            except Exception:

                traceback.print_exc()

    # -------------------------------------------------

    def executar(self,texto,ctx):

        for plugin in self.plugins:

            if not plugin.habilitado:
                continue

            try:

                if plugin.aceita(texto):

                    resposta=plugin.run(
                        ctx,
                        texto
                    )

                    if resposta is not None:
                        return resposta

            except Exception:

                traceback.print_exc()

        return None

    # -------------------------------------------------

    def listar(self):

        return self.plugins

    # -------------------------------------------------

    def nomes(self):

        return [p.nome for p in self.plugins]

    # -------------------------------------------------

    def existe(self,nome):

        return any(
            p.nome.lower()==nome.lower()
            for p in self.plugins
        )

    # -------------------------------------------------

    def obter(self,nome):

        for plugin in self.plugins:

            if plugin.nome.lower()==nome.lower():
                return plugin

        return None

    # -------------------------------------------------

    def __len__(self):

        return len(self.plugins)

    # -------------------------------------------------

    def __repr__(self):

        return f"<PluginManager plugins={len(self.plugins)}>"