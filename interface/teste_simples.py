from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from pathlib import Path
import sys

base = ShowBase()

script_path = Path(__file__).resolve().parent
modelo_path = script_path.parent / "avatar" / "aldoo"/"Aldo_model.glb"

print("\n\n=== INICIANDO TESTE DE SHAPE KEYS ===")
if not modelo_path.exists():
    print(f"ERRO: Arquivo não encontrado em {modelo_path}")
    sys.exit()

try:
    # Actor é a classe que lê Shape Keys (Morphs) no Panda3D
    avatar = Actor(str(modelo_path))
    
    print("\n=== ESTRUTURA INTERNA DO ARQUIVO ===")
    avatar.ls()
    print("======================================\n")
    
    # Se carregou como Character, as Shape Keys viraram Sliders!
    sliders = avatar.getJoints(jointName="*", partName="modelRoot")
    print(f"Foram encontrados {len(sliders)} juntas/sliders de controle.")
    
    for slider in sliders:
        # Imprime o nome de tudo o que pode ser animado (Bones e Shape Keys)
        print(f" -> Controle disponível: {slider.getName()}")
        
except Exception as e:
    print(f"Erro ao carregar o modelo: {e}")

sys.exit()