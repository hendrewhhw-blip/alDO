from __future__ import annotations

import json

from pathlib import Path


class Memoria:

    def __init__(self,config):

        self.config=config

        self.base=Path(__file__).parent

        self.prompts=self.base/"prompts"

        self.personalidades=self.prompts/"personalidades"

        self.dados=self.base/"dados"

        self.estado_path=self.dados/"estado.json"

        self.memoria_path=self.dados/"memoria.md"

        self.conversas_path=self.dados/"conversas.md"

        self.personalidade_path=self.dados/"personalidade.txt"

        self.prompts.mkdir(exist_ok=True)

        self.personalidades.mkdir(exist_ok=True)

        self.dados.mkdir(exist_ok=True)

        self._criar_padrao()

    # -------------------------------------------------

    def _criar_padrao(self):

        if not self.estado_path.exists():

            self.estado_path.write_text(

                json.dumps({

                    "humor":"neutro",

                    "energia":5,

                    "personalidade":"normal"

                },indent=4,ensure_ascii=False),

                encoding="utf-8"

            )

        if not self.memoria_path.exists():

            self.memoria_path.write_text(

                "",

                encoding="utf-8"

            )

        if not self.conversas_path.exists():

            self.conversas_path.write_text(

                "",

                encoding="utf-8"

            )

        if not self.personalidade_path.exists():

            self.personalidade_path.write_text(

                "normal",

                encoding="utf-8"

            )

    # -------------------------------------------------

    def carregar_estado(self):

        try:

            return json.loads(

                self.estado_path.read_text(

                    encoding="utf-8"

                )

            )

        except Exception:

            return {

                "humor":"neutro",

                "energia":5,

                "personalidade":"normal"

            }

    # -------------------------------------------------

    def salvar_estado(self,**kwargs):

        estado=self.carregar_estado()

        estado.update(kwargs)

        self.estado_path.write_text(

            json.dumps(

                estado,

                indent=4,

                ensure_ascii=False

            ),

            encoding="utf-8"

        )

    # -------------------------------------------------

    def ler_prompt(self,nome):

        arquivo=self.prompts/nome

        if not arquivo.exists():

            return ""

        return arquivo.read_text(

            encoding="utf-8"

        ).strip()

    # -------------------------------------------------

    def personalidade(self):

        nome=self.personalidade_path.read_text(

            encoding="utf-8"

        ).strip()

        arquivo=self.personalidades/f"{nome}.md"

        if not arquivo.exists():

            return ""

        return arquivo.read_text(

            encoding="utf-8"

        ).strip()

    # -------------------------------------------------

    def trocar_personalidade(self,nome):

        self.personalidade_path.write_text(

            nome,

            encoding="utf-8"

        )

        self.salvar_estado(

            personalidade=nome

        )

    # -------------------------------------------------

    def ler_memoria(self):

        return self.memoria_path.read_text(

            encoding="utf-8"

        ).strip()

    # -------------------------------------------------

    def lembrar_unico(self,texto):

        texto=texto.strip()

        if not texto:

            return

        atual=self.ler_memoria()

        linhas=[

            x.strip()

            for x in atual.splitlines()

            if x.strip()

        ]

        if texto not in linhas:

            linhas.append(texto)

            self.memoria_path.write_text(

                "\n".join(linhas),

                encoding="utf-8"

            )

    # -------------------------------------------------

    def remover_memoria(self,texto):

        linhas=[

            x

            for x in self.ler_memoria().splitlines()

            if x.strip()!=texto.strip()

        ]

        self.memoria_path.write_text(

            "\n".join(linhas),

            encoding="utf-8"

        )

    # -------------------------------------------------

    def procurar(self,texto):

        texto=texto.lower()

        return [

            linha

            for linha in self.ler_memoria().splitlines()

            if texto in linha.lower()

        ]

    # -------------------------------------------------

    def salvar_conversa(self,usuario,resposta):

        with open(

            self.conversas_path,

            "a",

            encoding="utf-8"

        ) as f:

            f.write(

                f"Usuário: {usuario}\n"

            )

            f.write(

                f"Aldo: {resposta.texto}\n\n"

            )