
import pygame
import os
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH  = 500
HEIGHT = 500

boca       = 10
boca_suave = 10

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock  = pygame.time.Clock()

rosto = pygame.image.load(os.path.join(BASE_DIR, "rosto.png"))
rosto = pygame.transform.scale(rosto, (WIDTH, HEIGHT))

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

RX           = 38    # raio horizontal esclera
RY           = 44    # raio vertical esclera
PUPILA_R     = 14    # raio pupila
GRAVIDADE    = 0.35
ATRITO       = 0.985
ELASTICIDADE = 0.5

# ──────────────────────────────────────────────
# Olho
# ──────────────────────────────────────────────

class Olho:
    def __init__(self, cx, cy):
        # centro da esclera (arrastável)
        self.cx = float(cx)
        self.cy = float(cy)

        # pupila começa no fundo da esclera
        self.px = float(cx)
        self.py = float(cy) + RY - PUPILA_R - 2

        # velocidade da pupila
        self.vx = 0.0
        self.vy = 0.0

        # drag do olho inteiro
        self.arrastando = False
        self.drag_offset = (0.0, 0.0)

    # ── drag do olho inteiro ──

    def dentro_esclera(self, mx, my):
        dx = (mx - self.cx) / RX
        dy = (my - self.cy) / RY
        return dx*dx + dy*dy <= 1.0

    def iniciar_drag(self, mx, my):
        if self.dentro_esclera(mx, my):
            self.arrastando = True
            self.drag_offset = (self.cx - mx, self.cy - my)
            return True
        return False

    def mover_drag(self, mx, my):
        if not self.arrastando:
            return
        self.cx = mx + self.drag_offset[0]
        self.cy = my + self.drag_offset[1]
        # pupila acompanha o olho mantendo posição relativa
        # (já que px/py são absolutas, não fazemos nada —
        #  a física vai reconfinar no update)

    def soltar(self):
        self.arrastando = False

    # ── física da pupila ──

    def update(self):
        # aplica gravidade
        self.vy += GRAVIDADE

        # atrito
        self.vx *= ATRITO
        self.vy *= ATRITO

        # move
        self.px += self.vx
        self.py += self.vy

        # confinamento elíptico com colisão
        rx  = RX - PUPILA_R
        ry  = RY - PUPILA_R
        dx  = self.px - self.cx
        dy  = self.py - self.cy
        # distância normalizada na elipse
        norm = math.hypot(dx / rx, dy / ry)

        if norm > 1.0:
            # ângulo do ponto de contato
            ang = math.atan2(dy, dx)
            # reposiciona na borda
            self.px = self.cx + math.cos(ang) * rx
            self.py = self.cy + math.sin(ang) * ry

            # normal da elipse no ponto de contato
            nx = math.cos(ang) / rx
            ny = math.sin(ang) / ry
            n_len = math.hypot(nx, ny)
            nx /= n_len
            ny /= n_len

            # reflexão da velocidade
            dot = self.vx * nx + self.vy * ny
            self.vx = (self.vx - 2 * dot * nx) * ELASTICIDADE
            self.vy = (self.vy - 2 * dot * ny) * ELASTICIDADE

    # ── desenho ──

    def desenhar(self, surface):
        cx, cy = int(self.cx), int(self.cy)
        px, py = int(self.px), int(self.py)

        # esclera branca
        pygame.draw.ellipse(
            surface, (240, 240, 240),
            (cx - RX, cy - RY, RX * 2, RY * 2)
        )
        # borda
        pygame.draw.ellipse(
            surface, (180, 180, 180),
            (cx - RX, cy - RY, RX * 2, RY * 2), 2
        )
        # pupila
        pygame.draw.circle(surface, (20, 20, 20), (px, py), PUPILA_R)
        # brilho
        pygame.draw.circle(surface, (255, 255, 255), (px - 5, py - 5), 4)


olho_esq = Olho(170, 185)
olho_dir = Olho(330, 185)
olhos    = [olho_esq, olho_dir]

# ──────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────

def set_boca(valor):
    global boca
    boca = valor

def update():
        global boca_suave

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for o in olhos:
                    o.iniciar_drag(*event.pos)

            elif event.type == pygame.MOUSEMOTION:
                for o in olhos:
                    o.mover_drag(*event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for o in olhos:
                    o.soltar()

        # suavização da boca
        if boca > boca_suave:
            boca_suave += (boca - boca_suave) * 0.25
        else:
            boca_suave += (boca - boca_suave) * 0.80

        # física dos olhos
        for o in olhos:
            o.update()

        # desenho
        screen.fill((0, 0, 0))
        screen.blit(rosto, (0, 0))

        for o in olhos:
            o.desenhar(screen)

        pygame.draw.ellipse(
            screen,
            (20, 20, 20),
            (190, 330 - int(boca_suave * 0.45) // 2, 120, int(boca_suave * 0.45))
        )

        pygame.display.flip()
        clock.tick(60)
