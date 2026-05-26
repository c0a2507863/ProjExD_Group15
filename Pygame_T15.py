import os
import random#ランダムのimport
import math
import sys
import pygame as pg
import random


# =========================================
# 初期設定
# =========================================

WIDTH = 1000
HEIGHT = 600
FPS = 60

os.chdir(os.path.dirname(os.path.abspath(__file__)))

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()


# =========================================
# 色
# =========================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
SKY = (135, 206, 235)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)


# =========================================
# Playerクラス
# =========================================

class Player:
    """
    プレイヤーを管理するクラス
    """

    def __init__(self):
        self.x = 200
        self.y = 400

        self.w = 50
        self.h = 50

        self.vy = 0

        self.gravity = 0.8
        self.jump_power = -15

        self.on_ground = True

    def jump(self):
        """
        ジャンプする
        """

        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False

    def update(self, ground_y: int):
        """
        プレイヤー更新
        """

        self.vy += self.gravity
        self.y += self.vy

        # 地面判定
        if self.y + self.h >= ground_y:
            self.y = ground_y - self.h
            self.vy = 0
            self.on_ground = True

    def draw(self, screen: pg.Surface):
        """
        プレイヤー描画
        """

        pg.draw.rect(
            screen,
            BLUE,
            (self.x, self.y, self.w, self.h)
        )


# =========================================
# Obstacleクラス
# =========================================

class Obstacle:
    """
    障害物クラス
    """

    def __init__(self):
        self.w = 50
        self.h = 50
        self.speed = 10

        # 最初の障害物を生成
        self.reset(is_first=True)
#障害物をランダムに出るようにするためのメゾット
    def reset(self, is_first=False):
        """障害物の状態をランダムにリセットする"""
        if is_first:
            self.x = WIDTH
        else:
            self.x = WIDTH + random.randint(0, 150)
        #障害物ののタイプをランダムに決める
        if is_first:
            self.move_type = random.choice(["normal", "wavy"])
        else:
            self.move_type = random.choices(
                ["normal", "wavy", "pit"], weights=[5, 3, 2], k=1
            )[0]
        self.angle = 0
        #それぞれのタイプの設定
        if self.move_type == "wavy":
            self.base_y = 350  # 上下に動くタイプは少し空中からスタート
            self.w = 50
        elif self.move_type == "pit":
            self.base_y = 500  # 落とし穴は地面の高さからスタート
            self.w = 150  # 3マス分の幅にする
        else:
            self.base_y = 450  # 通常タイプは地面の上
            self.w = 50

        self.y = self.base_y
    #落とし穴に関するメゾット
    def get_ground_y(
        self, player_x: int, player_w: int, default_ground_y: int
    ) -> int:
        """★プレイヤーの位置に応じた『地面の高さ』を計算して返すメソッド"""
        if self.move_type == "pit":
            # プレイヤーが落とし穴の上にいるか判定
            if player_x + player_w > self.x and player_x < self.x + self.w:
                # 穴の上なら、地面を画面の下（落ちる判定）にする
                return HEIGHT + 200

        # は穴の上にいないなら通常の地面の高さを返す
        return default_ground_y

    def update(self):
        """障害物更新"""

        # 左へ進む
        self.x -= self.speed

        ##動く障害物のみMATH.SINを使って上下に揺らす
        if self.move_type == "wavy":
            self.angle += 0.08  # 数値を大きくすると上下の揺れが速くなります
            # math.sinを使って基準の高さから上下に最大70ピクセル揺らす
            self.y = self.base_y + math.sin(self.angle) * 70
        else:
            self.y = self.base_y

        # 画面外へ行ったらリセットして再抽選
        if self.x + self.w < 0:
            self.reset()

    def draw(self, screen: pg.Surface):
        """障害物描画"""
        #pit(落とし穴)の場合は、空の色で穴を描き、枠線を黄色にする。それ以外は赤い四角で描く
        if self.move_type == "pit":
            hole_rect = pg.Rect(self.x, self.y, self.w, self.h)
            pg.draw.rect(screen, SKY, hole_rect)
            pg.draw.rect(screen, YELLOW, hole_rect, 4)
        else:
            pg.draw.rect(screen, RED, (self.x, self.y, self.w, self.h))

    def get_rect(self) -> pg.Rect:
        """Rect取得"""
        #落とし穴自体は「ぶつかってゲームオーバーになる障害物」ではないため、衝突判定をサイズ0にして無効化する
        if self.move_type == "pit":
            return pg.Rect(0, 0, 0, 0)

        return pg.Rect(self.x, self.y, self.w, self.h)
# =========================================
# Backgroundクラス
# =========================================

class Background:
    """
    背景クラス
    """

    def __init__(self):
        self.scroll_x = 0
        self.scroll_speed = 10

    def update(self):
        """
        背景更新
        """

        self.scroll_x -= self.scroll_speed

        if self.scroll_x <= -100:
            self.scroll_x = 0

    def draw(self, screen: pg.Surface, ground_y: int):
        """
        背景描画
        """

        # 空
        screen.fill(SKY)

        # 背景の縦線
        for x in range(0, WIDTH + 100, 100):
            pg.draw.rect(
                screen,
                GRAY,
                (x + self.scroll_x, 0, 5, HEIGHT)
            )

        # 地面
        pg.draw.rect(
            screen,
            BLACK,
            (0, ground_y, WIDTH, HEIGHT-ground_y)
        )

        # 地面ライン
        for x in range(0, WIDTH + 100, 100):
            pg.draw.rect(
                screen,
                YELLOW,
                (x + self.scroll_x, ground_y + 40, 50, 10)
            )


# =========================================
# Gameクラス
# =========================================

class Game:
    """
    ゲーム全体クラス
    """

    def __init__(self):

        self.ground_y = 500

        self.player = Player()
        self.obstacle = Obstacle()
        self.background = Background()
        self.item = Item() #アイテム用

        self.font = pg.font.Font(None, 50)
        self.big_font = pg.font.Font(None, 80)

        self.game_over = False

        # スコア
        self.score = 0

        # 距離
        self.distance = 0

    def check_collision(self):
        """
        当たり判定
        """

        player_rect = pg.Rect(
            self.player.x,
            self.player.y,
            self.player.w,
            self.player.h
        )

        obstacle_rect = self.obstacle.get_rect()

        if player_rect.colliderect(obstacle_rect):
            self.game_over = True

        item_rect = self.item.get_rect() #アイテム当たり判定
        if player_rect.colliderect(item_rect):
            self.score += 100
            self.item.x = WIDTH + random.randint(300, 800)
            self.item.y = random.randint(200, 500)

    def update(self):
        """
        更新処理
        """

        if not self.game_over:

            current_ground_y = self.obstacle.get_ground_y(
                self.player.x, self.player.w, self.ground_y
            )
            self.player.update(current_ground_y)
            self.obstacle.update()
            self.background.update()
            self.item.update() # アイテム更新

            self.check_collision()

            if self.player.y > HEIGHT:
                self.game_over = True

            # スコア加算
            self.score += 0.1

            # 距離加算
            self.distance += self.obstacle.speed

    def draw(self, screen: pg.Surface):
        """
        描画処理
        """

        self.background.draw(screen, self.ground_y)

        self.player.draw(screen)
        self.obstacle.draw(screen)
        self.item.draw(screen) # アイテム描画

        # SCORE表示
        score_text = self.font.render(
            f"SCORE : {int(self.score)}",
            True,
            BLACK
        )

        screen.blit(score_text, (20, 20))

        # GAME OVER画面
        if self.game_over:

            # 半透明背景
            overlay = pg.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)

            screen.blit(overlay, (0, 0))

            # GAME OVER
            gameover_text = self.big_font.render(
                "GAME OVER",
                True,
                WHITE
            )

            gameover_rect = gameover_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 80)
            )

            screen.blit(gameover_text, gameover_rect)

            # DISTANCE表示
            result_distance = self.font.render(
                f"DISTANCE : {int(self.distance)} m",
                True,
                WHITE
            )

            distance_rect = result_distance.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 20)
            )

            screen.blit(result_distance, distance_rect)


# =========================================
# Itemクラス
# =========================================
class Item:
    """
    アイテムクラス
    """
    def __init__(self):
        self.x = WIDTH
        self.y = random.randint(200,500)

        self.w = 50
        self.h = 50

        self.speed = 15
    
    def update(self):
        """
        アイテム更新
        """

        self.x -= self.speed

        # 画面外へ行ったら戻す ランダムに
        if self.x + self.w < 0:
            self.x = WIDTH + random.randint(300, 800)
    
    def draw(self, screen: pg.Surface):
        """
        アイテム描画
        """

        pg.draw.rect(
            screen,
            YELLOW,
            (self.x, self.y, self.w, self.h)
        )

    def get_rect(self) -> pg.Rect:
        return pg.Rect(
            self.x,
            self.y,
            self.w,
            self.h
        )


# =========================================
# メイン関数
# =========================================

def main():
    """
    メイン関数
    """

    game = Game()

    running = True

    while running:

        clock.tick(FPS)

        # イベント処理
        for event in pg.event.get():

            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:

                if event.key == pg.K_SPACE:
                    game.player.jump()

        # 更新
        game.update()

        # 描画
        game.draw(screen)

        pg.display.update()

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()