import sys
import time

import pygame
from pyjoycon import JoyCon, get_R_id, get_L_id


# Récupération de l'ID du Joy-Con droit
joycon_id = get_R_id()
if joycon_id is None:
    raise RuntimeError("Aucun Joy-Con droit détecté !")

# Initialisation
joycon = JoyCon(*joycon_id)

# --- Configuration Pygame ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Contrôle de perso avec analogique droit")
clock = pygame.time.Clock()

# Autoriser uniquement la fermeture de fenêtre
pygame.event.set_allowed(None)
pygame.event.set_allowed([pygame.QUIT])

# --- Personnage ---
player_size = 50
half = player_size / 2
player_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
player_color = (0, 200, 0)
stick_speed = 300  # pixels par seconde

def handle_joycon_stick(dt_game, status):
    # Lecture de l'analogique droit
    stick = status['analog-sticks']['right']
    raw_x = stick['horizontal']
    raw_y = stick['vertical']
    # Centrage et normalisation (-1.0 à +1.0)
    # Valeurs brutes : ~0 à 4095, milieu ≈2048
    norm_x = (raw_x - 2048) / 2048.0
    norm_y = (raw_y - 2048) / 2048.0
    # Sens de y inversé (pousser vers le haut => y négatif)
    norm_y = -norm_y

    # Movement vectoriel
    dx = norm_x * stick_speed * dt_game
    dy = norm_y * stick_speed * dt_game
    return pygame.Vector2(dx, dy)

# --- Boucle principale ---
running = True
while running:
    dt = clock.tick(60) / 1000  # delta-time en secondes
    status = joycon.get_status()

    # Gestion des événements Pygame
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    # Déplacement via l'analogique droit
    move = handle_joycon_stick(dt, status)
    player_pos += move

    # Clamp pour rester à l’écran
    player_pos.x = max(half, min(WIDTH  - half, player_pos.x))
    player_pos.y = max(half, min(HEIGHT - half, player_pos.y))

    # Rendu
    screen.fill((30, 30, 30))
    pygame.draw.rect(
        screen, player_color,
        (player_pos.x - half,
         player_pos.y - half,
         player_size, player_size)
    )
    pygame.display.flip()

# Nettoyage
# joycon.disconnect()
pygame.quit()
sys.exit()
