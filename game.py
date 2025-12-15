import sys, random

# ---------------- 플레이어/몬스터 ----------------
class Player:
    def __init__(self, name, hp=30, max_hp=30, attack=10, defense=5, level=1, exp=0,
                 inventory=None, gold=50, rebirth=0, current_floor=1):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp   # 최대 HP
        self.attack = attack
        self.defense = defense
        self.level = level
        self.exp = exp
        self.inventory = inventory if inventory else []
        self.gold = gold
        self.rebirth = rebirth
        self.current_floor = current_floor

class Monster:
    def __init__(self, name, hp, attack, defense, exp_reward):
        self.name = name
        self.hp = hp
        self.max_hp = hp   # 몬스터 최대 HP 기록
        self.attack = attack
        self.defense = defense
        self.exp_reward = exp_reward

# ---------------- 레벨업 체크 ----------------
def checkLevelUp(player):
    required_exp = 30 + (player.level - 1) * 20
    if player.exp >= required_exp:
        player.level += 1
        player.exp = 0
        player.max_hp += 10
        player.hp = player.max_hp
        player.attack += 2
        player.defense += 1
        print(f"🎉 {player.name} 레벨업! LV:{player.level}, HP:{player.hp}/{player.max_hp}, ATK:{player.attack}, DEF:{player.defense}")

# ---------------- 전투 ----------------
def battle(player, monster):
    print(f"\n⚔️ 전투 시작! {player.name} vs {monster.name}")
    while player.hp > 0 and monster.hp > 0:
        dmg = max(1, player.attack - monster.defense)
        monster.hp -= dmg
        print(f"{player.name}가 {monster.name}에게 {dmg} 데미지! (몬스터 HP: {monster.hp}/{monster.max_hp})")

        if monster.hp <= 0:
            print(f"{monster.name} 처치! 경험치 {monster.exp_reward} 획득!")
            player.exp += monster.exp_reward
            checkLevelUp(player)
            break

        dmg = max(1, monster.attack - player.defense)
        player.hp -= dmg
        print(f"{monster.name}가 {player.name}에게 {dmg} 데미지! (플레이어 HP: {player.hp}/{player.max_hp})")

    if player.hp <= 0:
        print(f"{player.name}가 쓰러졌습니다...")

# ---------------- 로그라이크 던전 ----------------
class Dungeon:
    def __init__(self, width, height, floor=1):
        self.width = width
        self.height = height
        self.floor = floor
        self.map = [["." for _ in range(width)] for _ in range(height)]
        self.player_pos = [width // 2, height // 2]
        self.generate()

    def generate(self):
        m_count = min(2 + self.floor // 2, 6)
        i_count = min(1 + self.floor // 3, 4)
        for _ in range(random.randint(m_count, m_count + 1)):
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            self.map[y][x] = "M"
        for _ in range(random.randint(i_count, i_count + 1)):
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            self.map[y][x] = "I"
        x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
        self.map[y][x] = "E"

    def draw(self, player):
        print(f"\n=== Floor {self.floor} ===")
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                if [x, y] == self.player_pos:
                    row += "P"
                else:
                    row += self.map[y][x]
            print(row)
        print(f"HP:{player.hp}/{player.max_hp}  LV:{player.level}  EXP:{player.exp}  GOLD:{player.gold}  환생:{player.rebirth}  진행층:{player.current_floor}")

def roguelikeGame(player):
    floor = max(1, player.current_floor)
    while player.hp > 0:
        dungeon = Dungeon(6, 6, floor=floor)

        while player.hp > 0:
            dungeon.draw(player)
            action = input("행동 (w/a/s/d 이동, q 던전나가기): ").strip().lower()

            if action == "q":
                print("던전 탐험을 종료합니다.")
                player.current_floor = floor
                persistPlayerUpdate(player)
                return

            dx, dy = 0, 0
            if action == "w": dy = -1
            elif action == "s": dy = 1
            elif action == "a": dx = -1
            elif action == "d": dx = 1
            else:
                print("올바른 입력이 아닙니다.")
                continue

            new_x = dungeon.player_pos[0] + dx
            new_y = dungeon.player_pos[1] + dy

            if 0 <= new_x < dungeon.width and 0 <= new_y < dungeon.height:
                dungeon.player_pos = [new_x, new_y]
                tile = dungeon.map[new_y][new_x]

                if tile == "M":
                    print("몬스터와 조우!")
                    monster = Monster(
                        name=f"{floor}층 몬스터",
                        hp=20 + floor * 10,
                        attack=5 + floor * 3,
                        defense=2 + floor * 2,
                        exp_reward=15 + floor * 10
                    )
                    battle(player, monster)
                    dungeon.map[new_y][new_x] = "."
                elif tile == "I":
                    found = random.choice(["포션", "작은금화", "강화석"])
                    print(f"아이템 발견! {found} 획득")
                    if found == "포션":
                        player.inventory.append("포션")
                    elif found == "작은금화":
                        gained = random.randint(10, 25) + floor * 2
                        player.gold += gained
                        print(f"GOLD +{gained} (현재 GOLD:{player.gold})")
                    elif found == "강화석":
                        player.inventory.append("강화석")
                    dungeon.map[new_y][new_x] = "."
                elif tile == "E":
                    print("출구를 발견했습니다! 다음 층으로 이동합니다.")
                    floor += 1
                    player.current_floor = floor
                    persistPlayerUpdate(player)
                    break
            else:
                print("벽입니다. 이동할 수 없습니다.")

        if player.hp <= 0:
            resetCharacterProgress(player)
            return

# ---------------- 인벤토리 ----------------
def showInventory(player):
    print("\n🎒 인벤토리")
    if not player.inventory:
        print("- 비어있습니다.")
    else:
        for idx, item in enumerate(player.inventory, start=1):
            print(f"[{idx}] {item}")

    use = input("아이템 사용하려면 이름 입력 (예: 포션, 강화석, 취소는 엔터): ").strip()
    if use == "포션":
        if "포션" in player.inventory:
            player.inventory.remove("포션")
            player.hp = min(player.max_hp, player.hp + 15)
            print(f"포션 사용! HP +15 (현재 HP:{player.hp}/{player.max_hp})")
        else:
            print("포션이 없습니다.")
    elif use == "강화석":
        if "강화석" in player.inventory:
            player.inventory.remove("강화석")
            player.max_hp += 10
            player.hp = player.max_hp
            player.attack += 2
            print(f"강화석 사용! HP +10, ATK +2 (HP:{player.hp}/{player.max_hp}, ATK:{player.attack})")
            persistPlayerUpdate(player)
        else:
            print("강화석이 없습니다.")

# ---------------- 캐릭터 정보 확인 ----------------
def showCharacter(player):
    print("\n📜 내 캐릭터 정보")
    print(f"이름: {player.name}")
    print(f"HP: {player.hp}/{player.max_hp}")
    print(f"ATK: {player.attack}")
    print(f"DEF: {player.defense}")
    print(f"LV: {player.level}")
    print(f"EXP: {player.exp}")
    print(f"GOLD: {player.gold}")
    print(f"환생 횟수: {player.rebirth}")
    print(f"진행 층: {player.current_floor}")
    if player.inventory:
        print(f"인벤토리: {', '.join(player.inventory)}")
    else:
        print("인벤토리: 비어있음")

# ---------------- 진행 초기화 (환생) ----------------
def resetCharacterProgress(player):
    player.level = 1
    player.exp = 0
    player.gold = 0
    player.hp = player.max_hp        # 현재 HP만 회복
    player.current_floor = 1         # 진행층 초기화
    player.rebirth += 1
    print(f"{player.name} 캐릭터가 쓰러졌습니다... {player.rebirth}회차 환생!")
    persistPlayerUpdate(player)

# ---------------- 파일 저장/불러오기 ----------------
def persistPlayerUpdate(player):
    characters = loadCharacters()
    updated = False
    for c in characters:
        if c.name == player.name:
            c.hp = player.hp
            c.max_hp = player.max_hp
            c.attack = player.attack
            c.defense = player.defense
            c.level = player.level
            c.exp = player.exp
            c.gold = player.gold
            c.rebirth = player.rebirth
            c.current_floor = player.current_floor
            updated = True
            break
    if not updated:
        characters.append(player)
    saveCharacters(characters)

def saveCharacters(characters):
    with open("character.txt", "w", encoding="utf-8") as f:
        for c in characters:
            f.write(c.name + "\n")
            f.write(str(c.hp) + "\n")
            f.write(str(c.max_hp) + "\n")
            f.write(str(c.attack) + "\n")
            f.write(str(c.defense) + "\n")
            f.write(str(c.level) + "\n")
            f.write(str(c.exp) + "\n")
            f.write(str(c.gold) + "\n")
            f.write(str(c.rebirth) + "\n")
            f.write(str(c.current_floor) + "\n")

def loadCharacters():
    characters = []
    try:
        with open("character.txt", "r", encoding="utf-8") as f:
            data = f.readlines()
            for i in range(0, len(data), 10):
                if i + 9 < len(data):
                    name = data[i].strip()
                    hp = int(data[i+1].strip())
                    max_hp = int(data[i+2].strip())
                    attack = int(data[i+3].strip())
                    defense = int(data[i+4].strip())
                    level = int(data[i+5].strip())
                    exp = int(data[i+6].strip())
                    gold = int(data[i+7].strip())
                    rebirth = int(data[i+8].strip())
                    current_floor = int(data[i+9].strip())
                    characters.append(Player(name, hp, max_hp, attack, defense, level, exp, [], gold, rebirth, current_floor))
    except FileNotFoundError:
        pass
    return characters

# ---------------- 로그인/캐릭터 관리 ----------------
def title():
    print("\n[1] 게임 시작")
    print("[2] 종료")
    try:
        return int(input("입력: ").strip())
    except ValueError:
        return 2

def gameMenu():
    print("\n[1] 캐릭터 생성")
    print("[2] 캐릭터 불러오기")
    print("[3] 캐릭터 삭제")
    print("[4] 종료")
    try:
        return int(input("선택: ").strip())
    except ValueError:
        return 4

def systemMenu():
    print("\n[1] 던전 입장")
    print("[2] 인벤토리")
    print("[3] 내 캐릭터")
    print("[4] 상점")
    print("[5] 종료")
    try:
        return int(input("선택: ").strip())
    except ValueError:
        return 5

def characterMake():
    name = input("캐릭터 이름 입력: ").strip()
    if not name:
        print("이름은 비어있을 수 없습니다.")
        return
    existing = {c.name for c in loadCharacters()}
    if name in existing:
        print("이미 존재하는 이름입니다. 다른 이름을 입력하세요.")
        return
    character = Player(name)
    chars = loadCharacters()
    chars.append(character)
    saveCharacters(chars)
    print(f"{character.name} 캐릭터가 생성되었습니다.")

def characterSelect():
    characters = loadCharacters()
    if not characters:
        print("저장된 캐릭터가 없습니다.")
        return None
    print("\n저장된 캐릭터 목록:")
    for idx, c in enumerate(characters, start=1):
        print(f"[{idx}] {c.name} (HP:{c.hp}/{c.max_hp}, LV:{c.level}, EXP:{c.exp}, GOLD:{c.gold}, 환생:{c.rebirth}, 진행층:{c.current_floor})")
    try:
        choice = int(input("선택할 캐릭터 번호: ").strip())
    except ValueError:
        print("잘못된 입력입니다.")
        return None
    if 1 <= choice <= len(characters):
        selected = characters[choice - 1]
        print(f"{selected.name} 선택 완료!")
        return selected
    else:
        print("잘못된 선택입니다.")
        return None

def deleteCharacter():
    characters = loadCharacters()
    if not characters:
        print("삭제할 캐릭터가 없습니다.")
        return
    print("\n삭제할 캐릭터 목록:")
    for idx, c in enumerate(characters, start=1):
        print(f"[{idx}] {c.name}")
    try:
        choice = int(input("삭제할 캐릭터 번호: ").strip())
    except ValueError:
        print("잘못된 입력입니다.")
        return
    if 1 <= choice <= len(characters):
        del_name = characters[choice - 1].name
        filtered = [c for c in characters if c.name != del_name]
        saveCharacters(filtered)
        print(f"{del_name} 캐릭터가 삭제되었습니다.")
    else:
        print("잘못된 선택입니다.")

# ---------------- 게임 시스템 ----------------
def gameSystem(player):
    while True:
        choice = systemMenu()
        if choice == 1:
            roguelikeGame(player)
        elif choice == 2:
            showInventory(player)
        elif choice == 3:
            showCharacter(player)
        elif choice == 4:
            shop(player)
        elif choice == 5:
            print("메인 메뉴로 돌아갑니다.")
            break
        else:
            print("올바른 입력이 아닙니다.")

# ---------------- 메인 실행 ----------------
if title() == 1:
    while True:
        choice = gameMenu()
        if choice == 1:
            characterMake()
        elif choice == 2:
            hero = characterSelect()
            if hero:
                gameSystem(hero)
        elif choice == 3:
            deleteCharacter()
        elif choice == 4:
            sys.exit()
        else:
            print("올바른 입력이 아닙니다.")
else:
    sys.exit()