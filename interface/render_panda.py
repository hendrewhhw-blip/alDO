import sys
import threading
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor  # Importante: usar Actor para Shape Keys
from panda3d.core import WindowProperties, DirectionalLight, AmbientLight

class PandaApp:
    def __init__(self):
        self.base = ShowBase()
        self.base.setBackgroundColor(0.2, 0.4, 0.8, 1.0)
        
        props = WindowProperties()
        props.setUndecorated(True)
        self.base.win.requestProperties(props)
        
        self.avatar = None
        
        self._inicializar_cena()
        
        self.comando_pendente = None
        self.lock = threading.Lock()
        
        thread_leitura = threading.Thread(target=self._escutar_stdin, daemon=True)
        thread_leitura.start()
        
        self.base.taskMgr.add(self._processar_comandos, "processar_comandos")

    def _inicializar_cena(self):
        script_path = Path(__file__).resolve().parent
        modelo_path = script_path.parent / "avatar" / "aldoo"/ "Aldo_model.glb"
        
        if modelo_path.exists():
            self.avatar = Actor(str(modelo_path))
            self.avatar.reparentTo(self.base.render)
            
            # 1. Forçamos o render para calcular o tamanho real do modelo
            self.base.graphicsEngine.renderFrame()
            
            # 2. Mapeia onde o Aldo está (Bounding Box)
            bMin, bMax = self.avatar.getTightBounds()
            center = (bMin + bMax) / 2
            
            # 3. Centraliza o Aldo no mundo (0,0,0) corrigindo qualquer offset do Blender
            self.avatar.setPos(-center.getX(), -center.getY(), -center.getZ())
            
            # 4. Calcula uma distância segura para a câmera baseada no tamanho do modelo
            size = (bMax - bMin).length()
            distancia = size * 1.5 if size > 0 else 5
            
            # 5. Centraliza a câmera no Aldo
            self.base.cam.setPos(0, -distancia, 0)
            self.base.cam.lookAt(0, 0, 0)
            
            self.avatar.setShaderAuto()
            print(f"[Panda3D] Modelo carregado. Centro: {center}, Distância da câmera: {distancia:.2f}")
            
            self._mapear_morphs()
        else:
            print(f"[Panda3D] ERRO: O arquivo '{modelo_path}' não foi encontrado.")
        
        # Iluminação mantida como estava
        alight = AmbientLight('alight')
        alight.setColor((0.6, 0.6, 0.6, 1))
        self.base.render.setLight(self.base.render.attachNewNode(alight))
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.8, 1))
        dlnp = self.base.render.attachNewNode(dlight)
        dlnp.setHpr(0, -45, 0)
        self.base.render.setLight(dlnp)

    def _mapear_morphs(self):
        print("\n--- [Panda3D] Mapeando Controles Faciais ---")
        joints = self.avatar.getJoints(jointName="*", partName="modelRoot")
        for joint in joints:
            print(f" -> Slider detectado: '{joint.getName()}'")
        print("----------------------------------------------\n")

    def _escutar_stdin(self):
        while True:
            linha = sys.stdin.readline()
            if not linha: break
            with self.lock: 
                self.comando_pendente = linha.strip()

    def _processar_comandos(self, task):
        comando = None
        with self.lock:
            if self.comando_pendente:
                comando = self.comando_pendente
                self.comando_pendente = None          
        
        if comando:
            partes = comando.split()
            if not partes: return task.cont

            if partes[0] == "POS" and len(partes) >= 5:
                x, y, w, h = map(int, partes[1:5])
                props = WindowProperties()
                props.setOrigin(x, y)
                props.setSize(w, h)
                self.base.win.requestProperties(props)
                
            elif partes[0] == "SHAPE" and self.avatar and len(partes) >= 3:
                nome_key = partes[1]
                try:
                    valor = float(partes[2])
                except ValueError: return task.cont
                
                # A mágica do controle:
                slider = self.avatar.controlJoint(None, 'modelRoot', nome_key)
                if slider:
                    slider.setX(valor)
                    # Força a atualização do esqueleto após mover o slider
                    self.avatar.update() 
                    print(f"[Panda3D] Aplicado {nome_key} = {valor}")
                else:
                    print(f"[Panda3D] Morph '{nome_key}' não encontrado.")
                    
        return task.cont

if __name__ == "__main__":
    app = PandaApp()
    app.base.run()