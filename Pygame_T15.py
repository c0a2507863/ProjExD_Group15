import os
import random#ランダムのimport
import math
import sys
import pygame as pg
import random


# ==============================================================================
# 1. グローバル定数・初期設定
# ==============================================================================

# 画面サイズ・フレームレート
WIDTH = 1000
HEIGHT = 600
FPS = 60

# スクリプトの絶対パスを基準にカレントディレクトリを変更（資産読み込みエラー防止）
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Pygameの初期化
pg.init()
#ひだ
try:
    pg.mixer.init()
except Exception:
    pass

screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

#ひだ ジャンプ音
jump_sound = None
try:
    jump_sound = pg.mixer.Sound(os.path.join('fig', 'jump1.wav'))
except Exception:
    jump_sound = None

# BGM
try:
    pg.mixer.music.load(os.path.join('fig', '追跡者.mp3'))
    pg.mixer.music.set_volume(0.4)
    pg.mixer.music.play(-1)
except Exception:
    pass

# ==============================================================================
# 2. カラー定義 (RGB値)
# ==============================================================================

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
    プレイヤーの座標、物理挙動（ジャンプ・重力）、描画を管理するクラス。
    【拡張性のヒント】
    - アニメーション：self.image_list を作り、update内でフレームごとに画像を切り替える。
    - しゃがみアクション：self.h を半分にし、y座標を調整する処理をupdateに挟む。
    """

    def __init__(self):
        # 座標とサイズ
        self.x = 200
        self.y = 400
        self.w = 50
        self.h = 50

        # 物理パラメータ
        self.vy = 0             # Y軸方向の移動速度（正：落下、負：上昇）
        self.gravity = 0.8      # 毎フレーム加算される重力加速度
        self.jump_power = -15   # ジャンプ時に与えられる初速（負の値で上方向）

        self.gravity = 0.8
        self.jump_power = -15

        # 状態フラグ
        self.on_ground = True   # 接地しているかどうか（空中ジャンプ防止用）
        self.nidanjump = False
        #ひだ
        self.image = None
        try:
            self.image = pg.image.load(os.path.join('fig', 'player1.png')).convert_alpha()
        except Exception:
            self.image = None

    def jump(self):
        """
        接地している場合のみ、上方向の初速を与えてジャンプを開始する。
        """
        checkonground = False
        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            #ひだ ジャンプ音
            if jump_sound:
                jump_sound.play()

        elif not self.on_ground and not self.nidanjump:
            self.vy = self.jump_power     # 再び上方向の初速を与える
            self.nidanjump = True

    def turbo(self):
        """
        地面に足がついている、または一段ジャンプをしている最中にシフトキーを押すと、ロケットのように上方向の速度を与える。
        ただし、二段ジャンプ中には使用できないようにする。
        """
        # 現在のすべてのキーの入力状態を取得
        keys = pg.key.get_pressed()

        # 左シフトまたは右シフトが押されているか判定
        if keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]:
            # 地面にいるまたは二段ジャンプ中ではない
            if self.on_ground or (not self.on_ground and not self.nidanjump):
                
                # 上方向への推進力
                self.vy = -8

    def update(self, ground_y: int):
        """
        重力の適用、座標の更新、および地面との衝突判定を行う。
        """

        # 重力による加速と座標更新
        self.vy += self.gravity
        self.y += self.vy

        # 地面衝突判定（プレイヤーの足元が地面を超えたら位置を補正）
        if self.y + self.h >= ground_y:
            self.y = ground_y - self.h
            self.vy = 0
            self.on_ground = True
            self.nidanjump = False

    def draw(self, screen: pg.Surface):
        """
        プレイヤーを画面に描画する（将来的に画像描画 `blit` へ差し替え可能）。
        """
    #ひだ
        if self.image:
            img = pg.transform.smoothscale(self.image, (self.w, self.h))
            screen.blit(img, (self.x, self.y))
        else:
            pg.draw.rect(
                screen,
                BLUE,
                (self.x, self.y, self.w, self.h)
            )


# ==============================================================================
# 4. Obstacleクラス
# ==============================================================================


class Obstacle:
    """
    画面右から左へ移動する障害物を管理するクラス。
    【拡張性のヒント】
    - 複数種類の障害物：__init__にタイプ引数（空飛ぶ敵など）を持たせ、y座標やサイズを分岐させる。
    - 画像化：pg.image.loadで画像を読み込み、rectのサイズに合わせて描画する。
    """

    def __init__(self):
        # 初期出現位置（画面の右端外側）とサイズ
        self.x = WIDTH
        self.y = 450
        self.w = 50
        self.h = 50

        # 移動速度
        self.speed = 10
        #ひだ
        self.image = None
        try:
            self.image = pg.image.load(os.path.join('fig', 'shougaibutsu1.png')).convert_alpha()
        except Exception:
            self.image = None

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
        """
        障害物を画面に描画する。
        """
    #ひだ
        if self.image:
            img = pg.transform.smoothscale(self.image, (self.w, self.h))
            screen.blit(img, (self.x, self.y))
        else:
            pg.draw.rect(
                screen,
                RED,
                (self.x, self.y, self.w, self.h)
            )
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
    スクロールする背景（空、縦線、地面、地面のライン）を描画・管理するクラス。
    【拡張性のヒント】
    - 多重スクロール（遠景・近景）：速度の異なる複数のscroll_xを用意することで、奥行きを表現できる。
    """

    def __init__(self):
        self.scroll_x = 0
        self.scroll_speed = 10
        #ひだ
        self.image = None
        try:
            self.image = pg.image.load(os.path.join('fig', 'background1.png')).convert()
        except Exception:
            self.image = None

    def update(self):
        """
        スクロール位置を更新。一定量流れたらループさせる。
        """
        self.scroll_x -= self.scroll_speed
        #ひだ
        if self.image:
            img_w = self.image.get_width()
            if self.scroll_x <= -img_w:
                self.scroll_x += img_w
        elif self.scroll_x <= -100:
            self.scroll_x = 0

    def draw(self, screen: pg.Surface, ground_y: int):
        """
        背景の各レイヤーを奥から順に描画する。
        """

        #ひだ
        if self.image:
            img_w = self.image.get_width()
            bx = int(self.scroll_x % img_w) - img_w
            while bx < WIDTH:
                screen.blit(self.image, (bx, 0))
                bx += img_w
        else:
            screen.fill(SKY)

        # レイヤー3: 地面（固定の黒い矩形）
        pg.draw.rect(
            screen,
            BLACK,
            (0, ground_y, WIDTH, HEIGHT-ground_y)
        )

        # レイヤー4: 地面の模様（スクロール付きの黄色いライン）
        for x in range(0, WIDTH + 100, 100):
            pg.draw.rect(
                screen,
                YELLOW,
                (x + self.scroll_x, ground_y + 40, 50, 10)
            )

# =========================================
# Pauseクラス
# =========================================
class Pause:
    def __init__(self, font, big_font):
        self.font = font
        self.big_font = big_font
        self.active = False  # ポーズ中かどうか

    def toggle(self):
        self.active = not self.active

    def draw(self, screen):
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.big_font.render("PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 60)))

        msg1 = self.font.render("R : Restart", True, WHITE)
        msg2 = self.font.render("T : Reset", True, WHITE)

        screen.blit(msg1, (WIDTH//2 - 100, HEIGHT//2 + 10))
        screen.blit(msg2, (WIDTH//2 - 100, HEIGHT//2 + 60))


# ==============================================================================
# 6. Gameクラス 
# ==============================================================================

class Game:
    """
    ゲームの状態（進行中、ゲームオーバー）、各オブジェクトの統括、スコア、衝突判定を管理。
    【拡張性のヒント】
    - リスタート機能：self.game_over時に特定キーでインスタンス変数を初期化する reset() メソッドを作る。
    - 難易度上昇：update内で self.score に応じて obstacle.speed と background.scroll_speed を増加させる。
    - アイテム追加：self.items などのリストを用意し、衝突時にスコア加算する処理をここに行う。
    """

    def __init__(self):
        # 地面の基準Y座標
        self.ground_y = 500

        # 各種ゲームオブジェクトの生成
        self.player = Player()
        self.obstacle = Obstacle()
        self.background = Background()
        self.item = Item() #アイテム用

        # フォント設定 (デフォルトフォント)
        self.font = pg.font.Font(None, 50)
        self.big_font = pg.font.Font(None, 80)

        self.pause = Pause(self.font, self.big_font)

        self.game_over = False

        # カウンタ変数
        self.score = 0
        self.distance = 0

    def check_collision(self):
        """
        プレイヤーと障害物の矩形（Rect）が重なっているかを判定する。
        """
        # プレイヤーの現在位置からRectを生成
        player_rect = pg.Rect(
            self.player.x,
            self.player.y,
            self.player.w,
            self.player.h
        )

        # 障害物のRectを取得
        obstacle_rect = self.obstacle.get_rect()

        # 衝突していたらゲームオーバーフラグを立てる
        if player_rect.colliderect(obstacle_rect):
            self.game_over = True

        item_rect = self.item.get_rect() #アイテム当たり判定
        if player_rect.colliderect(item_rect):
            self.score += 100
            self.item.x = WIDTH + random.randint(300, 800)
            self.item.y = random.randint(200, 500)

    def update(self):
        """
        ゲームが進行中の場合のみ、各オブジェクトの更新、衝突判定、スコア計算を行う。
        """

        if self.pause.active or self.game_over:
                return
        
        self.player.update(self.ground_y)
        self.obstacle.update()
        self.background.update()

        current_ground_y = self.obstacle.get_ground_y(
            self.player.x, self.player.w, self.ground_y
        )
        self.player.update(current_ground_y)
        self.obstacle.update()
        self.background.update()
        self.item.update() # アイテム更新

        self.check_collision()

        # スコア加算
        self.score += 0.1

        if self.player.y > HEIGHT:
            self.game_over = True


        # 距離加算
        self.distance += self.obstacle.speed

    def draw(self, screen: pg.Surface):
        """
        背景、オブジェクト、UI、ゲームオーバー画面を順に描画する。
        """
        # 1. 背景とキャラクターの描画
        self.background.draw(screen, self.ground_y)
        self.player.draw(screen)
        self.obstacle.draw(screen)
        self.item.draw(screen) # アイテム描画

        # 2. プレイ中UI (SCORE) の描画
        score_text = self.font.render(
            f"SCORE : {int(self.score)}",
            True,
            BLACK
        )
        screen.blit(score_text, (20, 20))

        # 3. ゲームオーバーUI（フラグが立っている場合のみオーバーレイ表示）
        if self.game_over:
            # 画面全体を覆う半透明の黒シートを作成
            overlay = pg.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            # 「GAME OVER」テキストの配置（画面中央）
            gameover_text = self.big_font.render(
                "GAME OVER",
                True,
                WHITE
            )
            gameover_rect = gameover_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 80)
            )
            screen.blit(gameover_text, gameover_rect)

            # 「DISTANCE」テキストの配置
            result_distance = self.font.render(
                f"DISTANCE : {int(self.distance)} m",
                True,
                WHITE
            )
            distance_rect = result_distance.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 20)
            )
            screen.blit(result_distance, distance_rect)

            retry_text = self.font.render("Press R to Restart", True, WHITE)
            retry_rect = retry_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
            screen.blit(retry_text, retry_rect)

            return
        
        # Pause画面
        if self.pause.active:
            self.pause.draw(screen)
            return


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


# ==============================================================================
# 7. メイン
# ==============================================================================


def main():
    """
    メインループ。イベントの監視、フレームレートの制御、Gameクラスの呼び出しを担当。
    """
    game = Game()
    running = True

    # メインゲームループ
    while running:

        # FPSを60に固定（1フレームあたりの時間を制御）
        clock.tick(FPS)

        # --- イベント処理部 ---
        for event in pg.event.get():
            # ×ボタンが押されたらループを抜ける
            if event.type == pg.QUIT:
                running = False

            # キーボードが押された瞬間の判定
            if event.type == pg.KEYDOWN:
                #gameover中の操作
                if game.game_over:
                    if event.key == pg.K_r:
                        game = Game()
                    continue

                # Pキーでポーズ切り替え
                if event.key == pg.K_p:
                    game.pause.toggle()

                # ポーズ中の操作
                if game.pause.active:
                    if event.key == pg.K_r:  # 再開
                        game.pause.active = False

                    if event.key == pg.K_t:  # リセット
                        game = Game()

                    continue

                if event.key == pg.K_SPACE:
                    game.player.jump()
                
                # TODO: ここに「ゲームオーバー時にRキーでリスタート」などの判定を追加しやすい

        # --- 更新・計算部 ---
        game.player.turbo()  # ターボはキーの押下状態で常に判定する
        game.update()

        # --- 描画部 ---
        game.draw(screen)

        # 画面バッファを更新してディスプレイに反映
        pg.display.update()

    # ループを抜けたら安全にPygameとシステムを終了
    pg.quit()
    sys.exit()


# スクリプトが直接実行された場合のみmainを実行
if __name__ == "__main__":
    main()