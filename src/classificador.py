"""
classificador.py
================
Inferência do Gemma 1 2b treinado em modo de função.
Recebe uma fala e retorna True/False chamando a função classificar_fala.
"""

import json
import re
import torch
import random
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ADAPTER_DIR = "./modelo_classificador"
MODEL_BASE  = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Template idêntico ao do treino — modelo espera exatamente esse formato
PROMPT_TEMPLATE = """\
<|system|>
Você é um classificador de falas. Chame a função abaixo com o resultado correto.

Função disponível:
{schema}</s>
<|user|>
Fala capturada: "{input}"</s>
<|assistant|>
"""

# ──────────────────────────────────────────────
# Fallback heurístico
# ──────────────────────────────────────────────

_DIRECIONADAS = [
    "você", "voce", "seu", "sua", "ei", "oi", "olá", "ola",
    "assistente", "robô", "robo", "sabe", "consegue", "pode",
    "poderia", "fale", "explica", "me diz", "me conta"
]
_IGNORAR = {
    "hm", "hmm", "ah", "ahn", "é", "tá", "ok", "sim",
    "não", "nao", "uhm", "uh", "eh", "né", "ne"
}

def _heuristica(texto: str) -> bool:
    t = texto.lower().strip()
    if len(t) < random.randint(1,4) or t in _IGNORAR:
        return False
    if any(p in t for p in _DIRECIONADAS):
        return True
    if t.endswith("?") or t.startswith(("o que","como","quando","onde","por que","qual","quem")):
        return True
    if len(t.split()) >= 5:
        return True
    return False


# ──────────────────────────────────────────────
# Parser da saída JSON
# ──────────────────────────────────────────────

_JSON_RE = re.compile(r'\{[^}]+\}')

def _parse_result(texto: str) -> str | None:
    """Extrai o valor de 'result' do PRIMEIRO JSON gerado pelo modelo."""
    match = _JSON_RE.search(texto)   # pega só o primeiro match
    if not match:
        return None
    try:
        data = json.loads(match.group())
        return data.get("result", "").upper().strip()
    except json.JSONDecodeError:
        return None


# ──────────────────────────────────────────────
# Classificador
# ──────────────────────────────────────────────

class Classificador:
    def __init__(self, usar_modelo: bool = True):
        self.modelo_ok = False
        self.schema    = None

        if not usar_modelo:
            print("[Classificador] Modo heurístico.")
            return

        adapter_path = Path(ADAPTER_DIR)
        if not adapter_path.exists():
            print("[Classificador] Adaptador não encontrado — rode treinar.py primeiro.")
            print("[Classificador] Usando heurísticas como fallback.")
            return

        try:
            # Carrega o schema salvo pelo treino
            schema_path = adapter_path / "function_schema.json"
            if schema_path.exists():
                with open(schema_path, encoding="utf-8") as f:
                    self.schema = json.dumps(json.load(f), ensure_ascii=False, indent=2)
            else:
                # Schema inline de emergência
                self.schema = json.dumps({
                    "name": "classificar_fala",
                    "parameters": {
                        "properties": {
                            "result": {"type": "string", "enum": ["SIM", "NAO"]}
                        },
                        "required": ["result"]
                    }
                }, ensure_ascii=False)

            print("[Classificador] Carregando modelo...")
            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)
            base = AutoModelForCausalLM.from_pretrained(
                MODEL_BASE,
                quantization_config=bnb,
                device_map="auto",
            )
            self.model = PeftModel.from_pretrained(base, ADAPTER_DIR)
            self.model.eval()
            self.modelo_ok = True
            print("[Classificador] Pronto!")

        except Exception as e:
            print(f"[Classificador] Falha: {e}")
            print("[Classificador] Usando heurísticas como fallback.")

    def deve_responder(self, texto: str) -> bool:
        if not self.modelo_ok:
            return _heuristica(texto)

        prompt = PROMPT_TEMPLATE.format(schema=self.schema, input=texto)
        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(self.model.device)

            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=20,       # {"result": "SIM"} tem ~10 tokens
                    do_sample=False,         # greedy — determinístico
                    temperature=1.0,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            novos   = output[0][inputs["input_ids"].shape[1]:]
            gerado  = self.tokenizer.decode(novos, skip_special_tokens=True).strip()
            result  = _parse_result(gerado)

            print(f"[Classificador] '{texto[:40]}' → {gerado!r} → {result}")

            if result == "SIM":
                return True
            if result == "NAO":
                return False

            # JSON malformado ou valor inesperado — fallback
            print("[Classificador] JSON inválido, usando heurística.")
            return _heuristica(texto)

        except Exception as e:
            print(f"[Classificador] Erro: {e}")
            return _heuristica(texto)
