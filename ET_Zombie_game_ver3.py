import pygame
import random
import os
import time
import math
import threading
from pylsl import StreamInlet, resolve_stream

# =======================
# 初期設定
# =======================
pygame.init()
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 64)

# -----------------------
# ディレクトリと画像
# -----------------------
BASE_DIR = r"C:\Users\eeg\Desktop\game_picture"

background_img = pygame.image.load(os.path.join(BASE_DIR, "battlefieled.png"))
zombie_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
zombie_img = pygame.transform.scale(zombie_img, (80, 80))
boss_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
boss_img = pygame.transform.scale(boss_img, (160, 160))

# =======================
# ゾンビクラス
# =======================
class Zombie:
    def __init__(self, x=None, y=None, is_boss=False):
        screen_info = pygame.display.Info()
        WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
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
        self.x += self.vx * dt
        self.y += self.vy * dt
        screen_info = pygame.display.Info()
        WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
        if self.x < 50 or self.x > WIDTH - 50:
            self.vx *= -1
        if self.y < 50 or self.y > HEIGHT - 50:
            self.vy *= -1
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x, self.y))
        if rect.collidepoint(gx, gy):
            dx = abs(gx - rect.centerx)
            dy = abs(gy - rect.centery)
            max_dist = max(rect.width, rect.height) / 2
            accuracy = 1 - math.hypot(dx, dy) / max_dist
            accuracy = max(0.2, accuracy)
            base_damage = 40 if not self.is_boss else 20
            self.hp -= base_damage * (accuracy ** 2) * 4 * dt

    def is_dead(self):
        return self.hp <= 0

    def draw(self, surf):
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x, self.y))
        surf.blit(img, rect)
        bar_w = 100 if self.is_boss else 80
        bar_h = 10
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.size - 20
        pygame.draw.rect(surf, (200,0,0), (bar_x,bar_y,bar_w,bar_h))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surf, (0,200,0), (bar_x,bar_y,int(bar_w*hp_ratio),bar_h))

# =======================
# ステージゾンビ生成
# =======================
def spawn_zombies(stage):
    if stage==1: return [Zombie() for _ in range(5)]
    if stage==2: return [Zombie() for _ in range(7)]
    if stage==3: return [Zombie() for _ in range(5)] + [Zombie(is_boss=True)]
    return []

# =======================
# LSL視線入力スレッド
# =======================
latest_gaze = [0,0]
def lsl_receive():
    global latest_gaze
    streams = resolve_stream('type', 'gaze')
    if not streams:
        print("⚠️ LSLストリームなし")
        return
    inlet = StreamInlet(streams[0])
    while True:
        sample, _ = inlet.pull_sample()
        try:
            x = (sample[0] + sample[6])/2
            y = (sample[1] + sample[7])/2
            screen_info = pygame.display.Info()
            latest_gaze = [int(x*screen_info.current_w), int(y*screen_info.current_h)]
        except: pass

# =======================
# メインゲーム
# =======================
def main():
    global latest_gaze

    # コンソールで選択
    input_mode = 0
    while input_mode not in [1,2]:
        input_mode = int(input("入力方式を選択してください (1: キーボード, 2: 視線入力): "))

    # フルスクリーン
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_size()

    if input_mode==2:
        t = threading.Thread(target=lsl_receive, daemon=True)
        t.start()

    stage=1
    stage_state="playing"
    zombies=spawn_zombies(stage)
    score=0
    warning_start=None
    running=True

    while running:
        dt = pygame.time.Clock().tick(60)/1000.0
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            elif event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                running=False

        screen.blit(pygame.transform.scale(background_img,(WIDTH,HEIGHT)), (0,0))

        if input_mode==1:
            gx,gy = pygame.mouse.get_pos()
        else:
            gx,gy = latest_gaze

        pygame.draw.circle(screen,(255,0,0),(gx,gy),8,2)

        if stage_state in ["playing","boss"]:
            for z in zombies[:]:
                z.update(dt,gx,gy)
                z.draw(screen)
                if z.is_dead():
                    zombies.remove(z)
                    score += 50 if z.is_boss else 10
            screen.blit(font.render(f"Score: {score}", True,(255,255,255)),(10,10))
            if not zombies:
                if stage==1:
                    stage=2
                    zombies=spawn_zombies(stage)
                elif stage==2:
                    stage=3
                    stage_state="warning"
                    warning_start=time.time()
                elif stage==3:
                    stage_state="clear"
        elif stage_state=="warning":
            if time.time()-warning_start<5:
                screen.blit(big_font.render("WARNING!!", True,(255,0,0)),(WIDTH//2-120,HEIGHT//2-50))
            else:
                zombies=spawn_zombies(stage)
                stage_state="boss"
        elif stage_state=="clear":
            screen.blit(big_font.render("GAME CLEAR!", True,(255,255,0)),(WIDTH//2-150,HEIGHT//2))

        pygame.display.flip()

    pygame.quit()

if __name__=="__main__":
    main()