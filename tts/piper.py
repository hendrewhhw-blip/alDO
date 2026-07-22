from __future__ import annotations

import hashlib
import platform
import random
import re
import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal


class SimuladorSincroniaThread(QThread):
    volume_atualizado = Signal(float)

    def __init__(self, arquivo_wav: str | Path, delay_inicial: float = 0.05, parent=None):
        super().__init__(parent)
        self.arquivo_wav = Path(arquivo_wav)
        self.delay_inicial = delay_inicial
        self._parar = False

    def run(self):
        try:
            # Pequena pausa para compensar o tempo de inicialização do player de áudio (ffplay/aplay)
            if self.delay_inicial > 0:
                time.sleep(self.delay_inicial)

            wf = wave.open(str(self.arquivo_wav), 'rb')
            framerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            
            chunk_size = 1024
            tempo_chunk = chunk_size / framerate
            dados_audio = wf.readframes(chunk_size)
            
            volume_suavizado = 0.0
            sensibilidade = 5.0
            
            # Limites de passo por frame para animação suave
            passo_maximo_abrir = 0.50
            passo_maximo_fechar = 0.34
            
            # Determina o tipo de dado do NumPy com base na largura do sample
            dtype = np.int16 if sampwidth == 2 else np.int8

            while len(dados_audio) > 0 and not self._parar:
                inicio_loop = time.time()
                
                dados_np = np.frombuffer(dados_audio, dtype=dtype).astype(np.float32)
                
                if len(dados_np) > 0:
                    # Se for estéreo, ajusta para calcular RMS correto
                    if n_channels > 1:
                        dados_np = dados_np.reshape(-1, n_channels).mean(axis=1)

                    volume_real = np.sqrt(np.mean(dados_np**2))
                    max_valor = 32768.0 if sampwidth == 2 else 128.0
                    volume_normalizado = volume_real / max_valor
                    
                    abertura_alvo = volume_normalizado * sensibilidade
                    abertura_alvo = min(1.0, max(0.0, float(abertura_alvo)))
                    
                    # Suavização com rampas controladas
                    if abertura_alvo > volume_suavizado:
                        diferenca = abertura_alvo - volume_suavizado
                        volume_suavizado += min(diferenca, passo_maximo_abrir)
                    else:
                        diferenca = volume_suavizado - abertura_alvo
                        volume_suavizado -= min(diferenca, passo_maximo_fechar)
                    
                    # Corte de ruído residual
                    if volume_suavizado < 0.05:
                        volume_suavizado = 0.0
                        
                    estado_boca = round(volume_suavizado, 3)
                    self.volume_atualizado.emit(float(estado_boca))
                
                # Controle rigoroso de tempo do loop
                tempo_gasto = time.time() - inicio_loop
                sleep_necessario = max(0.0, tempo_chunk - tempo_gasto)
                time.sleep(sleep_necessario)
                
                dados_audio = wf.readframes(chunk_size)

            # Cauda do áudio: fecha a boca gradualmente ao finalizar o arquivo
            while volume_suavizado > 0.0 and not self._parar:
                volume_suavizado -= min(volume_suavizado, passo_maximo_fechar)
                if volume_suavizado < 0.05:
                    volume_suavizado = 0.0
                    
                estado_boca = round(volume_suavizado, 3)
                self.volume_atualizado.emit(float(estado_boca))
                time.sleep(tempo_chunk)

            self.volume_atualizado.emit(0.0)
            wf.close()
            
        except Exception as e:
            print(f"Erro ao ler WAV para sincronia: {e}")

    def parar(self):
        self._parar = True


class PiperTTS:

    def __init__(self, config: dict, eventos=None, logger=None):
        self.config = config
        self.eventos = eventos
        self.logger = logger

        self.processo = None
        self.falando = False
        self.sincronia_thread = None
        
        # --- SISTEMA DE FILA E VOZES ALEATÓRIAS ---
        self.fila_falas = []
        
        # Lê as chaves diretamente do dicionário plano (config.json)
        self.vozes_disponiveis = self.config.get("vozes_aleatorias", [])
        self.chance_troca = self.config.get("chance_troca", 0.3)
        self.speaker = self.config.get("speaker", 0)

        self.executavel = self._localizar_piper()
        
        # Define a raiz do projeto (assumindo que piper.py está em src/audio ou src/tts)
        self.raiz = Path(__file__).resolve().parents[1]
        
        # Pega o nome do arquivo principal e monta o caminho completo da pasta Voices
        nome_modelo = self.config.get("voz", "pt_BR-faber-medium.onnx")
        self.modelo = self.raiz / "Voices" / nome_modelo
        self.modelo_json = Path(str(self.modelo) + ".json")

        # Configurações adicionais
        self.player = self.config.get("player", "ffplay")
        self.velocidade = self.config.get("velocidade", 1.0)
        self.cache_ativo = self.config.get("cache_tts", True)

        self.tmp = Path(tempfile.gettempdir()) / "aldo_tts"
        self.tmp.mkdir(exist_ok=True)

        self._validar()

    def _localizar_piper(self) -> str:
        exe = shutil.which("piper")
        if exe:
            return exe

        raiz = Path(__file__).resolve().parents[1]
        if platform.system() == "Windows":
            exe = raiz / "bin" / "windows" / "piper.exe"
        else:
            exe = raiz / "bin" / "linux" / "piper"

        if exe.exists():
            return str(exe)

        raise FileNotFoundError("Executável do Piper não encontrado.")

    def _validar(self):
        if not Path(self.executavel).exists():
            raise FileNotFoundError(f"Piper não encontrado em: {self.executavel}")
        if not self.modelo.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {self.modelo}")
        if not self.modelo_json.exists():
            raise FileNotFoundError(f"JSON do modelo não encontrado: {self.modelo_json}")

    def _hash(self, texto: str) -> str:
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def _arquivo_cache(self, texto: str) -> Path:
        return self.tmp / f"{self._hash(texto)}.wav"

    def sintetizar(self, texto: str, usar_cache: bool = True) -> Path | None:
        texto = texto.strip()
        if not texto:
            return None

        wav = self._arquivo_cache(texto)
        if usar_cache and self.cache_ativo and wav.exists():
            return wav

        comando = [
            self.executavel,
            "--model", str(self.modelo),
            "--output_file", str(wav)
        ]

        if self.speaker is not None:
            comando.extend(["--speaker", str(self.speaker)])

        try:
            subprocess.run(
                comando,
                input=texto,
                text=True,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as erro:
            if self.logger:
                self.logger.error(erro.stderr)
            raise RuntimeError("Falha ao sintetizar voz com o Piper.") from erro

        return wav

    def limpar_texto(self, texto: str) -> str:
        texto = texto.replace("*", "")
        texto = re.sub(r'[^\w\s.,!?àáâãéêíóôõúüçÀÁÂÃÉÊÍÓÔÕÚÜÇ-]', '', texto)
        return texto.strip()

    def falar(self, texto: str):
        # Divide o texto em frases mantendo a pontuação final usando regex
        frases = [f.strip() for f in re.split(r'(?<=[.!?])\s+', texto) if f.strip()]
        
        if not frases:
            frases = [texto.strip()]

        # Adiciona as frases na fila de reprodução
        self.fila_falas.extend(frases)

        # Se não estiver falando no momento, inicia a fila
        if not self.falando:
            self._tocar_proxima()

    def _tocar_proxima(self):
        """Puxa a próxima frase da fila, sorteia a voz e reproduz."""
        if not self.fila_falas:
            self.falando = False
            if self.eventos:
                self.eventos.emit("fim_fala")
            return

        texto_original = self.fila_falas.pop(0)
        texto_limpo = self.limpar_texto(texto_original)

        if not texto_limpo:
            # Se a frase ficou vazia após a limpeza, tenta a próxima
            self._tocar_proxima()
            return

        # Sorteio para troca de voz
        if self.vozes_disponiveis and random.random() < self.chance_troca:
            voz_sorteada = random.choice(self.vozes_disponiveis)
            
            # Pega apenas o nome do arquivo do sorteio e junta com a pasta Voices
            nome_sorteado = voz_sorteada.get("modelo", self.modelo.name)
            self.modelo = self.raiz / "Voices" / nome_sorteado
            self.modelo_json = Path(str(self.modelo) + ".json")
            
            self.speaker = voz_sorteada.get("speaker", self.speaker)
            
            try:
                self._validar()
                if self.logger:
                    self.logger.info(f"Voz alterada aleatoriamente para: {self.modelo.name} (Speaker: {self.speaker})")
            except FileNotFoundError as e:
                if self.logger:
                    self.logger.error(f"Erro ao trocar voz, ignorando: {e}")

        wav = self.sintetizar(texto_limpo)

        if wav is None:
            self._tocar_proxima()
            return
        
        self.reproduzir(wav)
        if self.eventos:
            self.eventos.emit("inicio_fala", texto=texto_limpo)

    def atualizar(self):
        """Deve ser chamado periodicamente no loop principal para detectar fim de áudio."""
        if self.processo is None:
            return

        if self.processo.poll() is None:
            return

        self.processo = None
        self.falando = False

        # O áudio acabou, toca a próxima frase da fila em vez de terminar
        self._tocar_proxima()

    def reproduzir(self, wav: Path):
        # Garante interrupção limpa de qualquer áudio/sincronia em andamento
        if self.falando or (self.sincronia_thread and self.sincronia_thread.isRunning()):
            self.parar()

        if self.player == "ffplay":
            comando = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(wav)]
        elif self.player == "aplay":
            comando = ["aplay", str(wav)]
        elif self.player == "paplay":
            comando = ["paplay", str(wav)]
        else:
            raise RuntimeError(f"Player '{self.player}' inválido.")

        self.processo = subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.falando = True

        # Inicia a thread de lip-sync
        self.sincronia_thread = SimuladorSincroniaThread(wav)
        if self.eventos:
            self.sincronia_thread.volume_atualizado.connect(
                lambda vol: self.eventos.emit("movimento_boca", volume=vol)
            )
        self.sincronia_thread.start()

    def parar(self):
        # Limpa a fila para não continuar falando caso seja interrompido
        self.fila_falas.clear()
        
        # Para a thread de sincronia
        if self.sincronia_thread and self.sincronia_thread.isRunning():
            self.sincronia_thread.parar()
            self.sincronia_thread.wait()

        # Mata o processo do player de áudio
        if self.processo is not None:
            try:
                self.processo.terminate()
                self.processo.wait(timeout=1)
            except Exception:
                try:
                    self.processo.kill()
                except Exception:
                    pass

        self.processo = None
        self.falando = False

        if self.eventos:
            self.eventos.emit("fala_interrompida")

    def limpar_cache(self):
        if not self.tmp.exists():
            return
        for arquivo in self.tmp.glob("*.wav"):
            try:
                arquivo.unlink()
            except Exception:
                pass

    @property
    def ocupado(self) -> bool:
        return self.falando or len(self.fila_falas) > 0

    def fechar(self):
        self.parar()

    def __repr__(self) -> str:
        return f"<PiperTTS modelo={self.modelo.name} fila={len(self.fila_falas)} falando={self.falando}>"