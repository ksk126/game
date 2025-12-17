import pygame
import random

# 기본 설정
WIDTH, HEIGHT = 6, 6
TILE_SIZE = 64
SCREEN_WIDTH, SCREEN_HEIGHT = WIDTH*TILE_SIZE, HEIGHT*TILE_SIZE

COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (0, 200, 0)
COLOR_MONSTER = (200, 0, 0)
COLOR_ITEM = (0, 0, 200)
COLOR_EXIT = (200, 200, 0)

# 플레이어/몬스터 클래스
class Player:
    def __init__(self):
        self.hp = 50
        self.max_hp = 50
        self.attack = 10
        self.defense = 3
        self.gold = 0
        self.exp = 0

class Monster:
    def __init__(self, floor=1):
        self.hp = 20 + floor*5
        self.max_hp = self.hp
        self.attack = 6 + floor*2
        self.defense = 2 + floor
        self.exp_reward = 10 + floor*5
        self.gold_reward = 5 + floor*3

class Dungeon:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map = [["." for _ in range(width)] for _ in range(height)]
        self.player_pos = [width // 2, height // 2]
        self.generate()

    def generate(self):
        for _ in range(4):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            if [x,y] != self.player_pos:
                self.map[y][x] = "M"
        for _ in range(3):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
            if [x,y] != self.player_pos:
                self.map[y][x] = "I"
        ex, ey = random.randint(0, self.width-1), random.randint(0, self.height-1)
        self.map[ey][ex] = "E"

    def move_player(self, dx, dy, player):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            self.player_pos = [new_x, new_y]
            tile = self.map[new_y][new_x]
            if tile == "M":
                monster = Monster()
                battle(player, monster)
                self.map[new_y][new_x] = "."
            elif tile == "I":
                print("🎒 아이템 발견! 포션 획득")
                player.hp = min(player.max_hp, player.hp+10)
                self.map[new_y][new_x] = "."
            elif tile == "E":
                print("🚪 출구 도달! 다음 층으로 이동!")
                self.generate()

def draw_dungeon(screen, dungeon):
    screen.fill(COLOR_BG)
    for y in range(dungeon.height):
        for x in range(dungeon.width):
            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            tile = dungeon.map[y][x]
            if [x,y] == dungeon.player_pos:
                pygame.draw.rect(screen, COLOR_PLAYER, rect)
            elif tile == "M":
                pygame.draw.rect(screen, COLOR_MONSTER, rect)
            elif tile == "I":
                pygame.draw.rect(screen, COLOR_ITEM, rect)
            elif tile == "E":
                pygame.draw.rect(screen, COLOR_EXIT, rect)
            else:
                pygame.draw.rect(screen, (60,60,60), rect, 1)

def battle(player, monster):
    print(f"⚔️ 전투 시작! Player vs Monster")
    while player.hp > 0 and monster.hp > 0:
        # 플레이어 공격
        dmg = max(1, player.attack - monster.defense)
        monster.hp -= dmg
        print(f"플레이어 공격! 몬스터 HP {monster.hp}/{monster.max_hp}")
        pygame.time.delay(500)
        if monster.hp <= 0:
            print("몬스터 처치!")
            player.exp += monster.exp_reward
            player.gold += monster.gold_reward
            print(f"EXP +{monster.exp_reward}, GOLD +{monster.gold_reward}")
            break
        # 몬스터 반격
        dmg = max(1, monster.attack - player.defense)
        player.hp -= dmg
        print(f"몬스터 반격! 플레이어 HP {player.hp}/{player.max_hp}")
        pygame.time.delay(500)
    if player.hp <= 0:
        print("💀 플레이어가 쓰러졌습니다... 게임 오버")

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("던전 + 전투 시스템 예제")
    clock = pygame.time.Clock()

    dungeon = Dungeon(WIDTH, HEIGHT)
    player = Player()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: dungeon.move_player(0,-1,player)
                elif event.key == pygame.K_s: dungeon.move_player(0,1,player)
                elif event.key == pygame.K_a: dungeon.move_player(-1,0,player)
                elif event.key == pygame.K_d: dungeon.move_player(1,0,player)

        draw_dungeon(screen, dungeon)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()