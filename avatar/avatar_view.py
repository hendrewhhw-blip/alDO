from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3
import math
from pathlib import Path



class AvatarView:

    def __init__(self, base: ShowBase, avatar_manager):
        self.base = base
        self.avatar = avatar_manager
        BASE_DIR = Path(__file__).resolve().parent
        modelo = BASE_DIR / "Aldo_model.obj"
        self.modelo = self.base.loader.loadModel(str(modelo))
        self.modelo.reparentTo(self.base.render)

        self.modelo.setPos(0,6,-1.4)
        self.modelo.setScale(1.2)

        self.face = self.modelo.find("**/Face")
        self.olho_esq = self.modelo.find("**/LEye")
        self.olho_dir = self.modelo.find("**/REye")

        self.tempo = 0

        base.taskMgr.add(self.update,"avatar_update")
        
    def set_shape(self,nome,valor):

        try:
            self.face.setMorphSlider(nome,float(valor))
        except Exception:
            pass
        
    def limpar_expressoes(self):

        self.set_shape("HappyExpression",0)
        self.set_shape("SadExpression",0)
        self.set_shape("AngryExpression",0)
        self.set_shape("SurpriseExpression",0)
        self.set_shape("EyebrownUp",0)
        self.set_shape("DeformFace",0)
    def aplicar_emocao(self):

        self.limpar_expressoes()

        emo = self.avatar.emocao.value

        if emo == "feliz":
            self.set_shape("HappyExpression",1.7)

        elif emo == "triste":
            self.set_shape("SadExpression",1.6)

        elif emo == "irritado":
            self.set_shape("AngryExpression",1)

        elif emo == "surpreso":
            self.set_shape("SurpriseExpression",1)
            self.set_shape("EyebrownUp",1)

        elif emo == "curioso":
            self.set_shape("EyebrownUp",0.7)
    def atualizar_boca(self):

        self.set_shape(
            "MouthOpen",
            self.avatar.boca
        )
    def atualizar_olhos(self):

        blink = 1-self.avatar.olhos

        self.set_shape("Blink",blink)
    def atualizar_olhar(self):

        x = 0
        z = 0

        d = self.avatar.olhar.value

        if d=="esquerda":
            x=-0.05

        elif d=="direita":
            x=0.05

        elif d=="cima":
            z=0.04

        elif d=="baixo":
            z=-0.04

        self.olho_esq.setPos(x,0,z)
        self.olho_dir.setPos(x,0,z)
    def atualizar_cabeca(self):

        ang = self.avatar.inclinacao*8

        self.modelo.setH(ang)
    def idle(self,dt):

        if self.avatar.esta_ocioso:

            self.tempo+=dt

            self.modelo.setP(
                math.sin(self.tempo)*1.5
            )
    def update(self,task):

        dt=globalClock.getDt()

        self.aplicar_emocao()

        self.atualizar_boca()

        self.atualizar_olhos()

        self.atualizar_olhar()

        self.atualizar_cabeca()

        self.idle(dt)

        return task.cont

    def set_estado(self, estado):

        try:
            self.avatar._trocar_estado(estado)
        except Exception:
            self.avatar.estado = estado


    def set_emocao(self, emocao):

        self.avatar.definir_emocao(emocao)


    def set_olhar(self, direcao):

        self.avatar.olhar_para(direcao)

        
    def falando(self, estado):

        self.avatar.falando = estado

        if estado:
            self.avatar.abrir_boca(1.0)
        else:
            self.avatar.fechar_boca()    