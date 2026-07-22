# Aldo

Aldo é um assistente virtual offline desenvolvido em Python. Feito para hardwares fracos;

O projeto possui:

- Conversação por texto e voz
- Transcrição de voz
- Síntese de voz
- Avatar animado
- Memória permanente e local
- Personalidades dinâmicas
- Plugins
- Eventos
- Sistema modular

---

## Recursos

✔ Conversação natural

✔ Memória permanente

✔ Memória de longo prazo

✔ Busca semântica

✔ Voz offline

✔ Avatar animado

✔ Personalidades

✔ Plugins

✔ Sistema de comandos

✔ Eventos automáticos

✔ Funcionamento totalmente offline

---

## Estrutura

```
Aldo/
```

Consulte `docs/arquitetura.md`.

---

## Instalação

Clone o projeto;

Crie o ambiente virtual;
    ```
    python -m venv .venv
    ```
Ative:

    Para usuários de Windows
    ```
    .venv\Scripts\activate
    ```

    Para usuários de Linux

    ```
    source .venv/bin/activate
    ```
Instale:
    ```
    pip install -r requirements.txt
    ```
---
## Execução

    ```
    python main.py
    ```

---

## Personalidades

As personalidades ficam em

```
personalidades/
```

Cada arquivo `.md` representa uma personalidade.

Exemplo

```
normal.md

hal9000.md

glados.md

am.md
```

---

## Memória

A memória fica em

```
data/
```

Os arquivos são totalmente editáveis.

---

## Plugins

Para criar um plugin basta adicionar um arquivo Python em

```
plugins/
```

---

## Licença

MIT