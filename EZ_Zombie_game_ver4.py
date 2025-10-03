import pygame
import random
import os
import time
import math
import threading
from pylsl import StreamInlet, resolve_stream

# ----------------------
# 初期設定
# ----------------------
pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
WIDTH, HEIGHT = screen.get_size() 
pygame.display.set_caption("視線注視でゾンビ退治ゲーム（画像版）")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 128)  # WARNING用

BASE_DIR = r"C:\Users\eeg\Desktop\game_picture"

background_img = pygame.image.load(os.path.join(BASE_DIR, "battlefieled.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

zombie_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
zombie_img = pygame.transform.scale(zombie_img, (160, 160))

boss_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
boss_img = pygame.transform.scale(boss_img, (480, 480))

treasure_img = pygame.image.load(os.path.join(BASE_DIR, "treasure.png"))

# ----------------------
# 入力選択（コンソール）
# ----------------------
input_mode = 0
while input_mode not in [1, 2]:
    input_mode = int(input("入力モードを選択してください（1:キーボード 2:視線）: "))

# ----------------------
# LSL視線入力用
# ----------------------
latest_gaze = [WIDTH//2, HEIGHT//2]
def lsl_receive():
    global latest_gaze
    print("LSLストリームを検索中...")
    streams = resolve_stream('type', 'gaze')
    if not streams:
        print("⚠️ LSLストリームが見つかりません")
        return
    inlet = StreamInlet(streams[0])
    print("ストリーム接続完了")
    while True:
        sample, timestamp = inlet.pull_sample()
        try:
            x = (sample[0] + sample[6])/2
            y = (sample[1] + sample[7])/2
            latest_gaze = [int(x*WIDTH), int(y*HEIGHT)]
        except:
            pass

if input_mode == 2:
    lsl_thread = threading.Thread(target=lsl_receive, daemon=True)
    lsl_thread.start()

# ----------------------
# ゾンビクラス
# ----------------------
class Zombie:
    def __init__(self, x=None, y=None, is_boss=False):
        self.x = x if x else random.randint(100, WIDTH-100)
        self.y = y if y else random.randint(100, HEIGHT-100)
        self.is_boss = is_boss
        self.size = 80 if is_boss else 40
        self.max_hp = 500 if is_boss else 100
        self.hp = self.max_hp
        self.speed = 80 if is_boss else 100
        self.vx = random.choice([-1,1])*random.uniform(0.5,1)*self.speed
        self.vy = random.choice([-1,1])*random.uniform(0.5,1)*self.speed

    def update(self, dt, gx, gy, powerup=False):
        self.x += self.vx*dt
        self.y += self.vy*dt
        if self.x<50 or self.x>WIDTH-50: self.vx*=-1
        if self.y<50 or self.y>HEIGHT-50: self.vy*=-1
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x,self.y))
        if rect.collidepoint(gx,gy):
            dx = abs(gx - rect.centerx)
            dy = abs(gy - rect.centery)
            max_dist = max(rect.width, rect.height)/2
            accuracy = 1 - math.hypot(dx,dy)/max_dist
            accuracy = max(0.2, accuracy)
            base_damage = 40 if not self.is_boss else 20
            if powerup: base_damage *=5
            self.hp -= base_damage*(accuracy**2)*4*dt

    def is_dead(self):
        return self.hp <= 0

    def draw(self, surf):
        img = boss_img if self.is_boss else zombie_img
        rect = img.get_rect(center=(self.x,self.y))
        surf.blit(img, rect)
        bar_w = 100 if self.is_boss else 80
        bar_h = 10
        bar_x = self.x - bar_w//2
        bar_y = self.y - self.size -20
        pygame.draw.rect(surf,(200,0,0),(bar_x,bar_y,bar_w,bar_h))
        hp_ratio = max(0,self.hp/self.max_hp)
        pygame.draw.rect(surf,(0,200,0),(bar_x,bar_y,int(bar_w*hp_ratio),bar_h))

# ----------------------
# 宝箱クラス（自然消滅）
# ----------------------
class Treasure:
    def __init__(self):
        self.x,self.y = WIDTH//2, HEIGHT//2
        self.hp = 200
        self.active = False
        self.start_time = None
        self.duration = 15

    def spawn(self):
        self.active=True
        self.start_time=time.time()
        self.hp=200

    def update(self, dt, gx, gy):
        if not self.active: return False
        rect = treasure_img.get_rect(center=(self.x,self.y))
        if rect.collidepoint(gx,gy):
            self.hp -= 40*dt
        elapsed = time.time() - self.start_time
        if elapsed>self.duration or self.hp<=0:
            self.active=False
            return True
        return False

    def draw(self,surf):
        if not self.active: return
        rect = treasure_img.get_rect(center=(self.x,self.y))
        surf.blit(treasure_img,rect)
        elapsed=int(time.time()-self.start_time)
        count=max(0,self.duration - elapsed)
        count_text = big_font.render(str(count),True,(255,255,0))
        surf.blit(count_text,(WIDTH//2-40,50))

# ----------------------
# ステージ管理
# ----------------------
def spawn_zombies(stage):
    if stage==1: return [Zombie() for _ in range(5)]
    elif stage==2: return [Zombie() for _ in range(7)]
    elif stage==3: return [Zombie() for _ in range(5)] + [Zombie(is_boss=True)]
    return []

stage=1
stage_state="playing"
zombies=spawn_zombies(stage)
score=0
running=True
warning_start=None
treasure=Treasure()
powerup=False
boss_start_time=None

# ----------------------
# メインループ
# ----------------------
while running:
    dt=clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            running=False

    screen.blit(background_img,(0,0))
    gx,gy = pygame.mouse.get_pos() if input_mode==1 else latest_gaze
    pygame.draw.circle(screen,(255,0,0),(gx,gy),8,2)

    # ゾンビ更新
    if stage_state in ["playing","boss"]:
        for z in zombies[:]:
            z.update(dt,gx,gy,powerup)
            z.draw(screen)
            if z.is_dead():
                zombies.remove(z)
                score += 50 if z.is_boss else 10

        score_text=font.render(f"Score: {score}",True,(255,255,255))
        screen.blit(score_text,(10,10))

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
            warning_text=big_font.render("WARNING!!",True,(255,0,0))
            screen.blit(warning_text,(WIDTH//2-250,HEIGHT//2-64))
        else:
            stage_state="boss"
            zombies=spawn_zombies(stage)
            boss_start_time=time.time()

    elif stage_state=="boss":
        if boss_start_time and not treasure.active:
            if time.time()-boss_start_time>5:
                treasure.spawn()
        if treasure.update(dt,gx,gy):
            powerup=True
        treasure.draw(screen)

    elif stage_state=="clear":
        end_text=big_font.render("GAME CLEAR!",True,(255,255,0))
        screen.blit(end_text,(WIDTH//2-150,HEIGHT//2))

    pygame.display.flip()

pygame.quit()