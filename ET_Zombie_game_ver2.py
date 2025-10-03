import pygame
import random
import os
import time
import math
from pylsl import StreamInlet, resolve_stream

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size() 

pygame.display.set_caption("視線注視でゾンビ退治ゲーム（画像版）")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 64)

# ----------------------
# ディレクトリ設定
# ----------------------
BASE_DIR = r"C:\Users\eeg\Desktop\game_picture"

# 画像読み込み
background_img = pygame.image.load(os.path.join(BASE_DIR, "battlefieled.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

zombie_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
zombie_img = pygame.transform.scale(zombie_img, (80, 80))

boss_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
boss_img = pygame.transform.scale(boss_img, (160, 160))  # ボスは大きめ

# ----------------------
# ゾンビクラス
# ----------------------
class Zombie:
    def __init__(self, x=None, y=None, is_boss=False):
        self.x = x if x else random.randint(100, WIDTH - 100)
        self.y = y if y else random.randint(100, HEIGHT - 100)
        self.is_boss = is_boss
        if self.is_boss:
            self.size = 80
            self.max_hp = 500
            self.speed = 50
        else:
            self.size = 40
            self.max_hp = 100
            self.speed = 80
        self.hp = self.max_hp
        self.vx = random.choice([-1, 1]) * random.uniform(0.5, 1) * self.speed
        self.vy = random.choice([-1, 1]) * random.uniform(0.5, 1) * self.speed

    def update(self, dt, gx, gy):
        # 移動
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 50 or self.x > WIDTH - 50:
            self.vx *= -1
        if self.y < 50 or self.y > HEIGHT - 50:
            self.vy *= -1

        # 画像矩形取得
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x, self.y))

        # 視線が画像内にある場合ダメージ
        if rect.collidepoint(gx, gy):
            dx = abs(gx - rect.centerx)
            dy = abs(gy - rect.centery)
            max_dist = max(rect.width, rect.height) / 2
            accuracy = 1 - math.hypot(dx, dy) / max_dist
            accuracy = max(0.2, accuracy)  # 端でも最低20%ダメージ
            base_damage = 40 if not self.is_boss else 20
            self.hp -= base_damage * (accuracy ** 2) * 4 * dt

    def is_dead(self):
        return self.hp <= 0

    def draw(self, surf):
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x, self.y))
        surf.blit(img, rect)

        # HPゲージ
        bar_w = 100 if self.is_boss else 80
        bar_h = 10
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.size - 20
        pygame.draw.rect(surf, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surf, (0, 200, 0), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

# ----------------------
# ゲーム進行管理
# ----------------------
def spawn_zombies(stage):
    if stage == 1:
        return [Zombie() for _ in range(5)]
    elif stage == 2:
        return [Zombie() for _ in range(7)]
    elif stage == 3:
        return [Zombie() for _ in range(5)] + [Zombie(is_boss=True)]
    return []

stage = 1
stage_state = "playing"  # "playing", "warning", "boss", "clear"
zombies = spawn_zombies(stage)
score = 0
running = True
warning_start = None

# ----------------------
# LSL視線入力初期化
# ----------------------
streams = resolve_stream('type', 'Gaze')
inlet = StreamInlet(streams[0])

# ----------------------
# メインループ
# ----------------------
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    screen.blit(background_img, (0, 0))

    # --- 視線座標取得 ---
    sample, timestamp = inlet.pull_sample(timeout=0.0)
    if sample:
        gx, gy = int(sample[0]), int(sample[1])
    else:
        gx, gy = -100, -100  # 視線取得できなければ画面外

    # 視線表示
    pygame.draw.circle(screen, (255, 0, 0), (gx, gy), 8, 2)

    if stage_state in ["playing", "boss"]:
        # ゾンビ更新
        for z in zombies[:]:
            z.update(dt, gx, gy)
            z.draw(screen)
            if z.is_dead():
                zombies.remove(z)
                score += 50 if z.is_boss else 10

        # スコア表示
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        # ステージ進行
        if not zombies:
            if stage == 1:
                stage = 2
                zombies = spawn_zombies(stage)
            elif stage == 2:
                stage = 3
                stage_state = "warning"
                warning_start = time.time()
            elif stage == 3:
                stage_state = "clear"

    elif stage_state == "warning":
        # WARNING表示5秒
        if time.time() - warning_start < 5:
            warning_text = big_font.render("WARNING!!", True, (255, 0, 0))
            screen.blit(warning_text, (WIDTH // 2 - 120, HEIGHT // 2 - 50))
        else:
            # WARNING終了 → ボス＋5体出現
            zombies = spawn_zombies(stage)
            stage_state = "boss"

    elif stage_state == "clear":
        end_text = big_font.render("GAME CLEAR!", True, (255, 255, 0))
        screen.blit(end_text, (WIDTH // 2 - 150, HEIGHT // 2))

    pygame.display.flip()

pygame.quit()