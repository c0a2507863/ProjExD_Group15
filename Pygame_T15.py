import os
import sys
import pygame as pg


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
screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()


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


# ==============================================================================
# 3. Playerクラス
# ==============================================================================

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

        # 状態フラグ
        self.on_ground = True   # 接地しているかどうか（空中ジャンプ防止用）
        self.nidanjump = False

    def jump(self):
        """
        接地している場合のみ、上方向の初速を与えてジャンプを開始する。
        """
        checkonground = False
        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False

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

    def update(self):
        """
        障害物を左へ移動させ、画面外に消えたら右端へ再配置する。
        """
        self.x -= self.speed

        # 画面左外（完全に隠れる位置）に到達したかの判定
        if self.x + self.w < 0:
            # TODO: ここでランダムな遅延（例：WIDTH + random.randint(0, 300)）を入れると難易度が上がる
            self.x = WIDTH + 300

    def draw(self, screen: pg.Surface):
        """
        障害物を画面に描画する。
        """
        pg.draw.rect(
            screen,
            RED,
            (self.x, self.y, self.w, self.h)
        )

    def get_rect(self) -> pg.Rect:
        """
        Gameクラスでの当たり判定（colliderect）に使用するpg.Rectオブジェクトを返す。
        """
        return pg.Rect(
            self.x,
            self.y,
            self.w,
            self.h
        )


# ==============================================================================
# 5. Backgroundクラス
# ==============================================================================

class Background:
    """
    スクロールする背景（空、縦線、地面、地面のライン）を描画・管理するクラス。
    【拡張性のヒント】
    - 多重スクロール（遠景・近景）：速度の異なる複数のscroll_xを用意することで、奥行きを表現できる。
    """

    def __init__(self):
        self.scroll_x = 0
        self.scroll_speed = 10  # 背景の流れる速度（障害物の速度と同期させると自然）

    def update(self):
        """
        スクロール位置を更新。一定量流れたらループさせる。
        """
        self.scroll_x -= self.scroll_speed

        # 流れるパターンの最小単位（100px）ごとに位置をリセットして無限ループを作る
        if self.scroll_x <= -100:
            self.scroll_x = 0

    def draw(self, screen: pg.Surface, ground_y: int):
        """
        背景の各レイヤーを奥から順に描画する。
        """
        # レイヤー1: 空（画面全体の塗りつぶし）
        screen.fill(SKY)

        # レイヤー2: 遠景の縦線（スクロール付き）
        for x in range(0, WIDTH + 100, 100):
            pg.draw.rect(
                screen,
                GRAY,
                (x + self.scroll_x, 0, 5, HEIGHT)
            )

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


# ==============================================================================
# 6. Gameクラス (シーンマネージャー)
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

        # フォント設定 (デフォルトフォント)
        self.font = pg.font.Font(None, 50)
        self.big_font = pg.font.Font(None, 80)

        # ゲーム状態フラグ
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

    def update(self):
        """
        ゲームが進行中の場合のみ、各オブジェクトの更新、衝突判定、スコア計算を行う。
        """
        if not self.game_over:
            # 各オブジェクトの内部状態更新
            self.player.update(self.ground_y)
            self.obstacle.update()
            self.background.update()

            # 衝突検知
            self.check_collision()

            # スコアと総移動距離の加算
            self.score += 0.1
            self.distance += self.obstacle.speed

    def draw(self, screen: pg.Surface):
        """
        背景、オブジェクト、UI、ゲームオーバー画面を順に描画する。
        """
        # 1. 背景とキャラクターの描画
        self.background.draw(screen, self.ground_y)
        self.player.draw(screen)
        self.obstacle.draw(screen)

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


# ==============================================================================
# 7. メインループ
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
                # スペースキーでジャンプ
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