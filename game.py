import sys, random, time, json
from collections import Counter

# ---------------- 설정/가격/이름 ----------------
ITEM_PRICES = {
    "포션": {"buy": 20, "sell": 10},
    "최고급 포션": {"buy": 100, "sell": 50},
    "강화석": {"buy": 200, "sell": 100},
    "낡은검": {"buy": 30, "sell": 15},
    "강화검": {"buy": 80, "sell": 40},
    "전설의 검": {"buy": 300, "sell": 150},
    "가죽방패": {"buy": 40, "sell": 20},
    "방패": {"buy": 60, "sell": 30},
    "전설의 방패": {"buy": 250, "sell": 125},
}

MONSTER_NAMES = {1:"슬라임",2:"고블린",3:"늑대",4:"오크",5:"트롤",6:"리치",7:"드래곤"}
BOSS_NAMES = {5:"트롤킹",10:"리치로드",15:"드래곤로드"}  # 메뉴에서 직접 수정 가능

# ---------------- 유틸 ----------------
def required_exp(level): return 30 + (level - 1) * 20

def parseItemName(item):
    if "+" in item:
        base, plus = item.split("+", 1)
        try:
            return base, int(plus)
        except ValueError:
            return base, 0
    return item, 0

def weapon_bonus(name): return {"낡은검":2, "강화검":3, "전설의 검":6}.get(name, 0)
def shield_bonus(name): return {"가죽방패":1, "방패":2, "전설의 방패":4}.get(name, 0)

# ---------------- 데이터 저장 ----------------
def saveCharacters(characters):
    with open("character.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(characters, ensure_ascii=False))

def loadCharacters():
    try:
        with open("character.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def persistPlayerUpdate(player):
    records = loadCharacters()
    for r in records:
        if r["name"] == player.name:
            r.update({
                "hp": player.hp, "max_hp": player.max_hp,
                "attack": player.attack, "defense": player.defense,
                "level": player.level, "exp": player.exp,
                "gold": player.gold, "rebirth": player.rebirth,
                "current_floor": player.current_floor,
                "base_max_hp": player.base_max_hp,
                "base_attack": player.base_attack,
                "base_defense": player.base_defense,
                "inventory": player.inventory[:],
                "equip_slots": player.equip_slots
            })
            saveCharacters(records)
            return
    # 없으면 새로 추가
    records.append({
        "name": player.name,
        "hp": player.hp, "max_hp": player.max_hp,
        "attack": player.attack, "defense": player.defense,
        "level": player.level, "exp": player.exp,
        "gold": player.gold, "rebirth": player.rebirth,
        "current_floor": player.current_floor,
        "base_max_hp": player.base_max_hp,
        "base_attack": player.base_attack,
        "base_defense": player.base_defense,
        "inventory": player.inventory[:],
        "equip_slots": player.equip_slots
    })
    saveCharacters(records)

def toPlayer(rec):
    return Player(
        name=rec["name"], hp=rec["hp"], max_hp=rec["max_hp"],
        attack=rec["attack"], defense=rec["defense"],
        level=rec["level"], exp=rec["exp"], inventory=rec.get("inventory", []),
        gold=rec["gold"], rebirth=rec["rebirth"], current_floor=rec["current_floor"],
        base_max_hp=rec.get("base_max_hp", 30), base_attack=rec.get("base_attack", 10),
        base_defense=rec.get("base_defense", 5), equip_slots=rec.get("equip_slots", {"weapon":None,"shield":None})
    )

# ---------------- 클래스 ----------------
class Player:
    def __init__(self, name, hp=30, max_hp=30, attack=10, defense=5,
                 level=1, exp=0, inventory=None, gold=50, rebirth=0, current_floor=1,
                 base_max_hp=30, base_attack=10, base_defense=5, equip_slots=None):
        self.name = name
        self.hp = hp; self.max_hp = max_hp
        self.attack = attack; self.defense = defense
        self.level = level; self.exp = exp
        self.inventory = inventory if inventory else []
        self.gold = gold; self.rebirth = rebirth; self.current_floor = current_floor
        self.base_max_hp = base_max_hp; self.base_attack = base_attack; self.base_defense = base_defense
        self.equip_slots = equip_slots if equip_slots else {"weapon": None, "shield": None}

class Monster:
    def __init__(self, name, hp, attack, defense, exp_reward, gold_reward=0, is_boss=False):
        self.name = name; self.hp = hp; self.max_hp = hp
        self.attack = attack; self.defense = defense
        self.exp_reward = exp_reward; self.gold_reward = gold_reward
        self.is_boss = is_boss

# ---------------- 레벨업/환생 ----------------
def checkLevelUp(player):
    while player.exp >= required_exp(player.level):
        player.exp -= required_exp(player.level)
        player.level += 1
        player.max_hp += 10           # 최대체력만 증가
        player.attack += 2
        player.defense += 1
        print(f"🎉 레벨업! LV:{player.level} HP:{player.hp}/{player.max_hp} ATK:{player.attack} DEF:{player.defense}")

def resetCharacterProgress(player):
    player.level = 1; player.exp = 0
    player.gold = 0; player.current_floor = 1
    player.rebirth += 1
    # 인벤토리 초기화
    player.inventory = []
    # 장비 해제 (강화 수치 무시하고 모두 제거)
    for slot in ["weapon","shield"]:
        cur = player.equip_slots[slot]
        if cur:
            name = cur["name"]; plus = cur["plus"]
            if slot == "weapon": player.attack -= weapon_bonus(name) * plus
            else: player.defense -= shield_bonus(name) * plus
            player.equip_slots[slot] = None
    # 기본치로 복구 (base_*는 강화석 반영 수치라 유지)
    player.max_hp = player.base_max_hp
    player.attack = player.base_attack
    player.defense = player.base_defense
    player.hp = player.max_hp
    print(f"{player.name}가 쓰러졌습니다... {player.rebirth}회차 환생! 인벤토리/장비가 초기화됩니다.")
    persistPlayerUpdate(player)

# ---------------- 장비 ----------------
def equipItem(player, item):
    if item not in player.inventory:
        print("인벤토리에 없습니다.")
        return
    base, plus = parseItemName(item)
    # 무기
    if "검" in base:
        cur = player.equip_slots["weapon"]
        if cur is None:
            player.inventory.remove(item)
            player.equip_slots["weapon"] = {"name": base, "plus": max(1, plus)}
            player.attack += weapon_bonus(base) * max(1, plus)
            print(f"{base}+{max(1,plus)} 장착! ATK:{player.attack}")
        elif cur["name"] == base:
            player.inventory.remove(item)
            cur["plus"] += max(1, plus)
            player.attack += weapon_bonus(base) * max(1, plus)
            print(f"{base} 강화! 현재 +{cur['plus']} ATK:{player.attack}")
        else:
            print("무기 슬롯은 하나만 착용 가능합니다. 먼저 해제하세요.")
            return
    # 방패
    elif "방패" in base:
        cur = player.equip_slots["shield"]
        if cur is None:
            player.inventory.remove(item)
            player.equip_slots["shield"] = {"name": base, "plus": max(1, plus)}
            player.defense += shield_bonus(base) * max(1, plus)
            print(f"{base}+{max(1,plus)} 장착! DEF:{player.defense}")
        elif cur["name"] == base:
            player.inventory.remove(item)
            cur["plus"] += max(1, plus)
            player.defense += shield_bonus(base) * max(1, plus)
            print(f"{base} 강화! 현재 +{cur['plus']} DEF:{player.defense}")
        else:
            print("방패 슬롯은 하나만 착용 가능합니다. 먼저 해제하세요.")
            return
    else:
        print("장착할 수 없는 아이템입니다.")
        return
    persistPlayerUpdate(player)

def unequip(player, slot):
    if slot not in player.equip_slots: print("잘못된 슬롯"); return
    cur = player.equip_slots[slot]
    if not cur: print("해제할 장비가 없습니다."); return
    name = cur["name"]; plus = cur["plus"]
    if slot == "weapon": player.attack -= weapon_bonus(name) * plus
    else: player.defense -= shield_bonus(name) * plus
    player.equip_slots[slot] = None
    # 강화 수치 유지해서 인벤토리로 반환
    player.inventory.append(f"{name}+{plus}")
    print(f"{name}+{plus} 해제 완료 → 인벤토리로 반환")
    persistPlayerUpdate(player)

def unequipAll(player):
    changed = False
    for slot in ["weapon","shield"]:
        cur = player.equip_slots[slot]
        if cur:
            changed = True
            name = cur["name"]; plus = cur["plus"]
            if slot == "weapon": player.attack -= weapon_bonus(name) * plus
            else: player.defense -= shield_bonus(name) * plus
            player.equip_slots[slot] = None
            player.inventory.append(f"{name}+{plus}")
            print(f"{name}+{plus} 해제 → 인벤토리 반환")
    if changed: persistPlayerUpdate(player)
    else: print("해제할 장비가 없습니다.")

def showEquipment(player):
    w = player.equip_slots["weapon"]; s = player.equip_slots["shield"]
    print("\n🛡️ 장비창")
    print("무기:", "-" if not w else f"{w['name']}+{w['plus']}")
    print("방패:", "-" if not s else f"{s['name']}+{s['plus']}")
    print("[1] 무기 해제  [2] 방패 해제  [3] 둘 다 해제  [0] 뒤로")
    choice = input("선택: ").strip()
    if choice == "1": unequip(player, "weapon")
    elif choice == "2": unequip(player, "shield")
    elif choice == "3": unequipAll(player)

# ---------------- 아이템/인벤토리 ----------------
def applyItemEffect(player, item):
    base, plus = parseItemName(item)
    if base == "포션":
        heal = 15
        player.hp = min(player.max_hp, player.hp + heal)
        print(f"포션 사용! HP +{heal} ▶ {player.hp}/{player.max_hp}")
    elif base == "최고급 포션":
        heal = 40
        player.hp = min(player.max_hp, player.hp + heal)
        print(f"최고급 포션 사용! HP +{heal} ▶ {player.hp}/{player.max_hp}")
    elif base == "강화석":
        player.max_hp += 10
        player.base_max_hp += 10
        player.attack += 2
        player.base_attack += 2
        print(f"강화석 사용! HP Max +10, ATK +2 ▶ HP:{player.hp}/{player.max_hp}, ATK:{player.attack}")
    else:
        equipItem(player, item)

def showInventory(player):
    print("\n🎒 인벤토리")
    if not player.inventory:
        print("- 비어있습니다.")
        return
    counts = Counter(player.inventory)
    for idx, (item, cnt) in enumerate(counts.items(), 1):
        print(f"[{idx}] {item} x{cnt}")
    use = input("사용/장착할 아이템 이름 입력 (취소는 엔터): ").strip()
    if not use or use not in counts: return
    # 여러 개 한 번에 사용
    try:
        num = int(input(f"{use} 몇 개 사용하시겠습니까? (최대 {counts[use]}): ").strip())
    except ValueError:
        print("잘못된 입력입니다.")
        return
    num = max(1, min(num, counts[use]))
    for _ in range(num):
        applyItemEffect(player, use)
        # 장비 장착이면 applyItemEffect가 equipItem 호출 → 인벤토리 제거는 equipItem이 처리
        # 소비아이템이면 여기서 제거
        base, _ = parseItemName(use)
        if base in ["포션", "최고급 포션", "강화석"]:
            player.inventory.remove(use)
    persistPlayerUpdate(player)

# ---------------- 상점 ----------------
def shop_items_by_floor(player):
    items = {
        "포션": ITEM_PRICES["포션"]["buy"],
        "강화검": ITEM_PRICES["강화검"]["buy"],
        "방패": ITEM_PRICES["방패"]["buy"],
        "강화석": ITEM_PRICES["강화석"]["buy"]
    }
    if player.current_floor >= 5:
        items["최고급 포션"] = ITEM_PRICES["최고급 포션"]["buy"]
    if player.current_floor >= 10:
        items["전설의 검"] = ITEM_PRICES["전설의 검"]["buy"]
        items["전설의 방패"] = ITEM_PRICES["전설의 방패"]["buy"]
    return items

def shop(player):
    print("\n🏪 상점")
    print("[1] 구매  [2] 판매  [0] 뒤로")
    c = input("선택: ").strip()
    if c == "1": shopBuy(player)
    elif c == "2": shopSell(player)

def shopBuy(player):
    items = shop_items_by_floor(player)
    print("\n🛒 구매 가능 목록:")
    keys = list(items.keys())
    for i, k in enumerate(keys, 1):
        print(f"[{i}] {k} - {items[k]} GOLD")
    print("[0] 뒤로")
    try:
        ch = int(input("구매할 번호: ").strip())
    except ValueError:
        return
    if ch == 0: return
    if 1 <= ch <= len(keys):
        name = keys[ch - 1]; price = items[name]
        if player.gold < price:
            print("골드가 부족합니다.")
            return
        player.gold -= price
        # 자동 장착 시도 (슬롯 비었을 때만)
        if ("검" in name) or ("방패" in name):
            slot = "weapon" if "검" in name else "shield"
            if player.equip_slots[slot] is None:
                player.equip_slots[slot] = {"name": name, "plus": 1}
                if slot == "weapon":
                    player.attack += weapon_bonus(name)
                    print(f"{name} 구매 및 자동 장착! ATK:{player.attack}")
                else:
                    player.defense += shield_bonus(name)
                    print(f"{name} 구매 및 자동 장착! DEF:{player.defense}")
            else:
                player.inventory.append(name)
                print(f"{name} 구매 완료! (슬롯 사용중 → 인벤토리로)")
        else:
            player.inventory.append(name)
            print(f"{name} 구매 완료! 인벤토리에 추가")
        persistPlayerUpdate(player)

def sell_price_with_plus(base, plus):
    base_sell = ITEM_PRICES.get(base, {"sell": 0})["sell"]
    # 강화 수치당 50% 가중치 (원하는 비율로 조정 가능)
    return int(base_sell * (1 + 0.5 * plus))

def shopSell(player):
    if not player.inventory:
        print("판매할 아이템이 없습니다.")
        return
    print("\n💰 판매 가능 목록:")
    counts = Counter(player.inventory)
    items = list(counts.keys())
    for idx, itm in enumerate(items, 1):
        base, plus = parseItemName(itm)
        price = sell_price_with_plus(base, plus)
        print(f"[{idx}] {itm} x{counts[itm]} - {price} GOLD (개당)")
    print("[0] 뒤로")
    try:
        ch = int(input("판매할 번호: ").strip())
    except ValueError:
        return
    if ch == 0: return
    if 1 <= ch <= len(items):
        name = items[ch - 1]
        base, plus = parseItemName(name)
        price = sell_price_with_plus(base, plus)
        if price <= 0:
            print("이 아이템은 판매할 수 없습니다.")
            return
        player.inventory.remove(name)
        player.gold += price
        print(f"{name} 판매 완료! GOLD +{price} (현재 {player.gold})")
        persistPlayerUpdate(player)

# ---------------- 전투 ----------------
def battle(player, monster):
    print(f"\n⚔️ 전투 시작! {player.name} vs {monster.name}")
    while player.hp > 0 and monster.hp > 0:
        # 플레이어 공격
        dmg = max(1, player.attack - monster.defense)
        monster.hp -= dmg
        print(f"{player.name}의 공격! {monster.name}에게 {dmg} 피해 (HP {max(0, monster.hp)}/{monster.max_hp})")
        time.sleep(0.4)
        if monster.hp <= 0:
            print(f"{monster.name} 처치! EXP +{monster.exp_reward}")
            player.exp += monster.exp_reward
            if monster.gold_reward:
                player.gold += monster.gold_reward
                print(f"GOLD +{monster.gold_reward} (현재 {player.gold})")
            checkLevelUp(player)
            break
        # 몬스터 공격
        dmg = max(1, monster.attack - player.defense)
        player.hp -= dmg
        print(f"{monster.name}의 반격! {player.name} {dmg} 피해 (HP {max(0, player.hp)}/{player.max_hp})")
        time.sleep(0.4)
    if player.hp <= 0:
        print("쓰러졌습니다...")

# ---------------- 던전 ----------------
class Dungeon:
    def __init__(self, width, height, floor):
        self.width = width; self.height = height; self.floor = floor
        self.map = [["." for _ in range(width)] for _ in range(height)]
        self.player_pos = [width // 2, height // 2]
        self.boss_exists = (floor % 5 == 0)
        self.boss_defeated = False
        self.generate()

    def generate(self):
        m_count = min(2 + self.floor // 2, 6)
        i_count = min(1 + self.floor // 3, 4)
        # 몬스터
        for _ in range(random.randint(m_count, m_count + 1)):
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            if [x, y] != self.player_pos: self.map[y][x] = "M"
        # 아이템
        for _ in range(random.randint(i_count, i_count + 1)):
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            if [x, y] != self.player_pos: self.map[y][x] = "I"
        # 출구
        ex, ey = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
        self.map[ey][ex] = "E"
        # 보스 (5층마다)
        if self.boss_exists:
            bx, by = self.width // 2, 0
            self.map[by][bx] = "B"

    def draw(self, player):
        print(f"\n=== Floor {self.floor} ===")
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                row += "P" if [x, y] == self.player_pos else self.map[y][x]
            print(row)
        lock_text = "(보스 처치 필요)" if self.boss_exists and not self.boss_defeated else ""
        req = required_exp(player.level)
        print(f"HP:{player.hp}/{player.max_hp}  LV:{player.level}  EXP:{player.exp}/{req}  GOLD:{player.gold}  환생:{player.rebirth}  진행층:{player.current_floor}  출구:{lock_text}")

def roguelikeGame(player):
    floor = max(1, player.current_floor)
    while player.hp > 0:
        dungeon = Dungeon(6, 6, floor)
        while player.hp > 0:
            dungeon.draw(player)
            action = input("행동 (w/a/s/d 이동, i 인벤토리 사용, q 던전 나가기): ").strip().lower()
            if action == "q":
                print("던전 탐험을 종료합니다. (회복 없음)")
                player.current_floor = floor
                persistPlayerUpdate(player)
                return
            if action == "i":
                showInventory(player)
                continue
            dx, dy = 0, 0
            if action == "w": dy = -1
            elif action == "s": dy = 1
            elif action == "a": dx = -1
            elif action == "d": dx = 1
            else:
                print("잘못된 입력입니다."); continue

            new_x = dungeon.player_pos[0] + dx
            new_y = dungeon.player_pos[1] + dy
            if not (0 <= new_x < dungeon.width and 0 <= new_y < dungeon.height):
                print("벽입니다."); continue

            dungeon.player_pos = [new_x, new_y]
            tile = dungeon.map[new_y][new_x]

            if tile == "M":
                name = MONSTER_NAMES.get(floor, f"{floor}층 몬스터")
                gold_reward = random.randint(5, 15) + floor * 2
                monster = Monster(
                    name=name,
                    hp=20 + floor * 10,
                    attack=5 + floor * 3,
                    defense=2 + floor * 2,
                    exp_reward=15 + floor * 10,
                    gold_reward=gold_reward
                )
                battle(player, monster)
                dungeon.map[new_y][new_x] = "."
            elif tile == "B":
                print("보스 몬스터 등장!")
                boss_name = BOSS_NAMES.get(floor, f"{floor}층 보스")
                boss = Monster(
                    name=boss_name,
                    hp=120 + floor * 25,
                    attack=18 + floor * 6,
                    defense=10 + floor * 3,
                    exp_reward=150 + floor * 25,
                    gold_reward=80 + floor * 12,
                    is_boss=True
                )
                battle(player, boss)
                if boss.hp <= 0:
                    dungeon.boss_defeated = True
                    print(f"{boss_name} 처치! 출구가 활성화되었습니다.")
                dungeon.map[new_y][new_x] = "."
            elif tile == "I":
                # 2%로 희귀 장비
                if random.random() < 0.02:
                    found = random.choice(["전설의 검", "전설의 방패"])
                    print(f"✨ 희귀 아이템 발견! {found} 획득")
                    player.inventory.append(found)
                else:
                    found = random.choice(["포션","작은금화","강화석","낡은검","가죽방패","강화검","방패"])
                    print(f"아이템 발견! {found} 획득")
                    if found in ["낡은검","강화검","전설의 검","가죽방패","방패","전설의 방패"]:
                        player.inventory.append(found)
                    elif found == "포션":
                        player.inventory.append("포션")
                    elif found == "작은금화":
                        gained = random.randint(10, 25) + floor * 2
                        player.gold += gained
                        print(f"GOLD +{gained} (현재 {player.gold})")
                    elif found == "강화석":
                        player.inventory.append("강화석")
                dungeon.map[new_y][new_x] = "."
            elif tile == "E":
                if dungeon.boss_exists and not dungeon.boss_defeated:
                    print("출구가 잠겨 있습니다. 보스를 처치하세요!")
                else:
                    print("출구 도달! 다음 층으로 이동합니다.")
                    floor += 1
                    player.current_floor = floor
                    persistPlayerUpdate(player)
                    break

        if player.hp <= 0:
            resetCharacterProgress(player)
            return

# ---------------- 캐릭터/메뉴 ----------------
def showCharacter(player):
    print("\n📜 내 캐릭터")
    print(f"이름: {player.name}")
    print(f"HP: {player.hp}/{player.max_hp}")
    print(f"ATK: {player.attack}  DEF: {player.defense}")
    req = required_exp(player.level)
    print(f"LV: {player.level}  EXP: {player.exp}/{req}")
    print(f"GOLD: {player.gold}  환생: {player.rebirth}  진행층: {player.current_floor}")
    # 인벤토리 표시는 제거, 장비창만
    showEquipment(player)

def setBossName():
    try:
        fl = int(input("보스 이름을 지정할 층 입력 (예: 5): ").strip())
    except ValueError:
        print("층 입력이 올바르지 않습니다."); return
    name = input(f"{fl}층 보스 이름 입력: ").strip()
    if not name:
        print("이름이 비어있습니다."); return
    BOSS_NAMES[fl] = name
    print(f"{fl}층 보스 이름이 '{name}'로 설정되었습니다.")

def characterMake():
    name = input("캐릭터 이름: ").strip()
    if not name:
        print("이름은 비어있을 수 없습니다."); return
    existing = {c["name"] for c in loadCharacters()}
    if name in existing:
        print("이미 존재하는 이름입니다."); return
    p = Player(name)
    records = loadCharacters()
    records.append({
        "name": p.name, "hp": p.hp, "max_hp": p.max_hp,
        "attack": p.attack, "defense": p.defense,
        "level": p.level, "exp": p.exp, "gold": p.gold,
        "rebirth": p.rebirth, "current_floor": p.current_floor,
        "base_max_hp": p.base_max_hp, "base_attack": p.base_attack, "base_defense": p.base_defense,
        "inventory": p.inventory[:], "equip_slots": p.equip_slots
    })
    saveCharacters(records)
    print(f"{p.name} 캐릭터 생성 완료!")

def characterSelect():
    recs = loadCharacters()
    if not recs:
        print("저장된 캐릭터가 없습니다.")
        return None
    print("\n저장된 캐릭터 목록:")
    for i, c in enumerate(recs, 1):
        print(f"[{i}] {c['name']} (LV:{c['level']} HP:{c['hp']}/{c['max_hp']} EXP:{c['exp']} GOLD:{c['gold']} 환생:{c['rebirth']} 층:{c['current_floor']})")
    try:
        ch = int(input("선택 번호: ").strip())
    except ValueError:
        print("잘못된 입력입니다."); return None
    if 1 <= ch <= len(recs):
        p = toPlayer(recs[ch - 1])
        print(f"{p.name} 선택!")
        return p
    print("잘못된 선택입니다."); return None

def deleteCharacter():
    recs = loadCharacters()
    if not recs:
        print("삭제할 캐릭터가 없습니다."); return
    print("\n삭제 목록:")
    for i, c in enumerate(recs, 1):
        print(f"[{i}] {c['name']}")
    try:
        ch = int(input("삭제 번호: ").strip())
    except ValueError:
        print("잘못된 입력입니다."); return
    if 1 <= ch <= len(recs):
        name = recs[ch - 1]["name"]
        recs = [r for r in recs if r["name"] != name]
        saveCharacters(recs)
        print(f"{name} 삭제 완료.")
    else:
        print("잘못된 선택입니다.")

def systemMenu():
    print("\n[1] 던전 입장")
    print("[2] 인벤토리")
    print("[3] 내 캐릭터")
    print("[4] 상점")
    print("[5] 장비창 (해제/전체해제)")
    print("[6] 보스 이름 설정")
    print("[7] 종료")
    try:
        return int(input("선택: ").strip())
    except ValueError:
        return 7

def gameSystem(player):
    while True:
        c = systemMenu()
        if c == 1: roguelikeGame(player)
        elif c == 2: showInventory(player)
        elif c == 3: showCharacter(player)
        elif c == 4: shop(player)
        elif c == 5: showEquipment(player)
        elif c == 6: setBossName()
        elif c == 7:
            print("메인 메뉴로 돌아갑니다."); break
        else:
            print("잘못된 입력입니다.")

def title():
    print("\n[1] 게임 시작  [2] 종료")
    try:
        return int(input("입력: ").strip())
    except ValueError:
        return 2

# ---------------- 메인 ----------------
if title() == 1:
    while True:
        print("\n[1] 캐릭터 생성  [2] 캐릭터 불러오기  [3] 캐릭터 삭제  [4] 종료")
        try:
            m = int(input("선택: ").strip())
        except ValueError:
            m = 4
        if m == 1:
            characterMake()
        elif m == 2:
            hero = characterSelect()
            if hero:
                gameSystem(hero)
        elif m == 3:
            deleteCharacter()
        elif m == 4:
            sys.exit()
        else:
            print("잘못된 입력입니다.")
else:
    sys.exit()
