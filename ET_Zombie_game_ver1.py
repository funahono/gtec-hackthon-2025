import pygame
import random
import os
import threading
from pylsl import StreamInlet, resolve_stream
import time

pygame.init()
# WIDTH, HEIGHT = 3840, 2160
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
WIDTH, HEIGHT = screen.get_size() 
pygame.display.set_caption("視線注視でゾンビ退治ゲーム（画像版）")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)

# ----------------------
# ディレクトリ設定
# ----------------------
BASE_DIR = r"C:\Users\eeg\Desktop\game_picture"

# 画像読み込み
background_img = pygame.image.load(os.path.join(BASE_DIR, "battlefieled.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

zombie_img = pygame.image.load(os.path.join(BASE_DIR, "zombi.png"))
zombie_img = pygame.transform.scale(zombie_img, (80, 80))

# ----------------------
# ゾンビクラス
# ----------------------
class Zombie:
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.size = 40
        self.max_hp = 100
        self.hp = self.max_hp
    
    def update(self, dt, gx, gy):
        dist = ((gx - self.x)**2 + (gy - self.y)**2)**0.5
        if dist <= self.size:
            self.hp -= 40 * dt  # 注視でHP減少

    def is_dead(self):
        return self.hp <= 0

    def draw(self, surf):
        # ゾンビ画像描画（中心に配置）
        rect = zombie_img.get_rect(center=(self.x, self.y))
        surf.blit(zombie_img, rect)

        # HPゲージ
        bar_w = 80
        bar_h = 8
        bar_x = self.x - bar_w//2
        bar_y = self.y - self.size - 20
        pygame.draw.rect(surf, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))  # 赤背景
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surf, (0, 200, 0), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))  # 緑HP

# ----------------------
# LSLデータ受信スレッド用関数
# ----------------------
latest_gaze = [WIDTH // 2, HEIGHT // 2]  # 初期値は画面中央

def lsl_receive():
    global latest_gaze
    print("LSLストリームを検索中...")
    streams = resolve_stream('type', 'gaze')
    if not streams:
        print("⚠️ LSLストリームが見つかりませんでした。プログラムを終了します。")
        return
    inlet = StreamInlet(streams[0])
    print("ストリームに接続しました！")

    while True:
        sample, timestamp = inlet.pull_sample()
        # sampleのインデックスは環境によるので適宜調整してください
        # ここでは両目のX,Y座標の平均を使う例です
        try:
            x = (sample[0] + sample[6]) / 2
            y = (sample[1] + sample[7]) / 2
            print(f"receive {x}, {y}")

            # LSL座標系→画面座標系変換が必要ならここで処理
            # 例えば視線が正規化座標(0～1)なら以下のように画面サイズに合わせる
            x_screen = int(x * WIDTH)
            y_screen = int(y * HEIGHT)

            # 最新座標を更新
            latest_gaze = [x_screen, y_screen]
        except Exception as e:
            print("LSLデータ処理エラー:", e)

# ----------------------
# メイン処理
# ----------------------
def main():
    global latest_gaze
    zombies = [Zombie() for _ in range(5)]
    score = 0
    running = True

    # LSL受信スレッド開始
    lsl_thread = threading.Thread(target=lsl_receive, daemon=True)
    lsl_thread.start()

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 背景を描画
        screen.blit(background_img, (0, 0))

        # 視線座標を使う
        gx, gy = latest_gaze

        # 注視点を赤い丸で表示
        pygame.draw.circle(screen, (255, 0, 0), (gx, gy), 8, 2)

        # ゾンビ処理
        for z in zombies[:]:
            z.update(dt, gx, gy)
            z.draw(screen)
            if z.is_dead():
                zombies.remove(z)
                score += 10

        # スコア表示
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        if not zombies:
            end_text = font.render("All zombies defeated!", True, (255, 255, 0))
            screen.blit(end_text, (WIDTH//2 - 120, HEIGHT//2))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
