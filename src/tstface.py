import pygame
import threading
import os
import numpy as np
import time
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH = 500
HEIGHT = 500
boca = 10
boca_suave = 10
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()
rosto = pygame.image.load(os.path.join(BASE_DIR,"rosto.png"))
rosto = pygame.transform.scale(rosto, (WIDTH, HEIGHT))
screen.fill((0, 0, 0))
screen.blit(rosto, (0, 0))
pygame.draw.ellipse(
    screen,
    (20, 20, 20),
    (190, 330 - int(boca_suave * 0.45) //2 , 120, int(boca_suave * 0.45))
    )
pygame.display.flip()
clock.tick(60)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            break

