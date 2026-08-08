from flask import Flask, render_template, request, redirect, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "pirates_secret_key"

DB = "game.db"

online_locations = {}


# ---------- База данных ----------

DB = "pirates.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Создаём таблицу, если её ещё нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT UNIQUE,
            password TEXT,
            gender TEXT,
            hp INTEGER DEFAULT 1000,
            xp INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 100,
            piastres INTEGER DEFAULT 10,
            pearls INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
    )
""")
             
    cur.execute("""
CREATE TABLE IF NOT EXISTS online_players (
    nickname TEXT PRIMARY KEY,
    last_seen INTEGER
    )
""")


    # Проверяем существующие столбцы
    cur.execute("PRAGMA table_info(players)")
    columns = [row[1] for row in cur.fetchall()]

    # Добавляем недостающие столбцы в старую базу
    if "password" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN password TEXT")

    if "gender" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN gender TEXT")

    if "hp" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN hp INTEGER DEFAULT 1000")

    if "xp" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN xp INTEGER DEFAULT 0")

    if "gold" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN gold INTEGER DEFAULT 100")

    if "piastres" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN piastres INTEGER DEFAULT 10")

    if "pearls" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN pearls INTEGER DEFAULT 0")

    if "level" not in columns:
        cur.execute("ALTER TABLE players ADD COLUMN level INTEGER DEFAULT 1")

    if "attack" not in columns:
        cur.execute(
        "ALTER TABLE players ADD COLUMN attack INTEGER DEFAULT 10"
    )

    if "speed" not in columns:
        cur.execute(
        "ALTER TABLE players ADD COLUMN speed INTEGER DEFAULT 10"
    )

    conn.commit()
    conn.close()

init_db()


# ---------- Получение игрока ----------

def get_player():
    if "nickname" not in session:
        return None

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT nickname, hp, xp, gold, piastres,
pearls, level, gender, attack, speed
FROM players
        WHERE nickname=?
    """, (session["nickname"],))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "nickname": row[0],
        "hp": row[1],
        "max_hp": 1000,
        "exp": row[2],
        "next_exp": 1000,
        "gold": row[3],
        "piastres": row[4],
        "pearls": row[5],
        "level": row[6],
        "gender": row[7],
        "attack": row[8],
        "speed": row[9],
        "mail": 0
    }

@app.route("/")
def index():
    player = get_player()

    if player is not None:
        return redirect("/port")

    session.pop("nickname", None)
    return redirect("/register")


# ---------- Регистрация ----------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    nickname = request.form["nickname"]
    password = request.form["password"]
    gender = request.form["gender"]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Проверяем, существует ли капитан
    cur.execute(
        "SELECT id, password FROM players WHERE nickname=?",
        (nickname,)
    )

    player = cur.fetchone()

    # Капитан уже существует
    if player is not None:

        # Проверяем пароль
        if player[1] == password:
            session["nickname"] = nickname
            conn.close()
            return redirect("/port")

        # Пароль неправильный
        conn.close()
        return render_template(
            "register.html",
            error="Неверный пароль!"
        )

        # Создаём нового капитана
    cur.execute("""
        INSERT INTO players (
            nickname,
            password,
            gender,
            hp,
            xp,
            gold,
            piastres,
            pearls,
            level
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nickname,
        password,
        gender,
        1000,
        0,
        100,
        10,
        0,
        1
    ))

    conn.commit()
    conn.close()

    # Запоминаем капитана
    session["nickname"] = nickname

    return redirect("/port")

    return render_template("register.html")


# ---------- Порт ----------

@app.route("/port")
def port():

    player = get_player()

    if player is None:
       session.pop("nickname", None)
       return redirect("/register")

    return render_template(
        "port.html",
        player=player
    )

@app.route("/players")
def players():
    query = request.args.get("q", "").strip()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT nickname, level
            FROM players
            WHERE nickname LIKE ?
            ORDER BY nickname
            LIMIT 30
        """, (f"%{query}%",))
    else:
        cur.execute("""
            SELECT nickname, level
            FROM players
            ORDER BY nickname
            LIMIT 30
        """)

    players_list = cur.fetchall()
    conn.close()

    return render_template(
        "players.html",
        players=players_list,
        query=query
    )

# ---------- Боты локаций ----------

LOCATION_BOTS = {
    "Пенная бухта": [
        {
            "name": "Джон Сильвер",
            "level": 1,
            "health": 100,
            "damage": 10
        },
        {
            "name": "Эдди Крю",
            "level": 2,
            "health": 120,
            "damage": 12
        },
        {
            "name": "Головорез Джо",
            "level": 3,
            "health": 150,
            "damage": 15
        }
    ]
}

bot_turn = {}

# ---------- БОЙ С БОТАМИ ----------

BATTLE_BOTS = {
    "Джон Сильвер": {
        "level": 1,
        "hp": 5000,
        "max_hp": 5000,
        "damage": 1222,
        "reward_gold": 50,
        "reward_xp": 20
    },

    "Эдди Крю": {
        "level": 2,
        "hp": 6500,
        "max_hp": 6500,
        "damage": 1300,
        "reward_gold": 75,
        "reward_xp": 30
    },

    "Головорез Джо": {
        "level": 3,
        "hp": 8000,
        "max_hp": 8000,
        "damage": 1380,
        "reward_gold": 100,
        "reward_xp": 40
    }
}


# Кто сейчас должен нападать
bot_turn = {}


@app.route("/battle/<bot_name>")
def battle(bot_name):

    player = get_player()

    if player is None:
        return redirect("/")

    if bot_name not in BATTLE_BOTS:
        return redirect("/sea")

    # Создаём отдельное состояние боя
    battle = {
        "bot_name": bot_name,
        "bot_hp": BATTLE_BOTS[bot_name]["max_hp"],
        "player_hp": player.get("health", 100),
        "max_player_hp": player.get("max_health", 100)
    }

    session["battle"] = battle

    bot = BATTLE_BOTS[bot_name].copy()

    bot["hp"] = battle["bot_hp"]
    bot["image"] = "bot.png"

    return render_template(
        "battle.html",
        player=player,
        bot=bot
    )


@app.route("/battle/attack", methods=["POST"])
def battle_attack():

    player = get_player()

    if player is None:
        return jsonify({
            "error": "Игрок не найден"
        })

    battle = session.get("battle")

    if not battle:
        return jsonify({
            "error": "Бой не найден"
        })

    data = request.get_json() or {}

    weapon = data.get("weapon")

    # Урон оружия
    weapon_damage = {
        "cannon": 1344,
        "harpoon": 1100,
        "mortar": 1600
    }

    damage = weapon_damage.get(weapon, 0)

    if damage <= 0:
        return jsonify({
            "error": "Неизвестное оружие"
        })

    bot_name = battle["bot_name"]

    bot = BATTLE_BOTS[bot_name]

    # Удар игрока
    battle["bot_hp"] -= damage

    if battle["bot_hp"] < 0:
        battle["bot_hp"] = 0

    player_message = (
        f"⚔️ Вы ударили {bot_name} "
        f"на {damage} урона!"
    )

    # Бот погиб
    if battle["bot_hp"] <= 0:

        player["gold"] = player.get("gold", 0) + bot["reward_gold"]

        player["xp"] = player.get("xp", 0) + bot["reward_xp"]

        session["battle"] = None

        return jsonify({
            "message": player_message,
            "player_hp": battle["player_hp"],
            "enemy_hp": 0,
            "finished": True,
            "result": (
                f"🏆 {bot_name} побеждён! "
                f"+{bot['reward_gold']} золота "
                f"+{bot['reward_xp']} опыта."
            )
        })

    # Ответный удар бота
    bot_damage = bot["damage"]

    battle["player_hp"] -= bot_damage

    if battle["player_hp"] < 0:
        battle["player_hp"] = 0

    enemy_message = (
        f"☠️ {bot_name} ударил вас "
        f"на {bot_damage} урона."
    )

    # Игрок погиб
    if battle["player_hp"] <= 0:

        session["battle"] = None

        return jsonify({
            "message": player_message,
            "enemy_message": enemy_message,
            "player_hp": 0,
            "enemy_hp": battle["bot_hp"],
            "finished": True,
            "result": "☠️ Ваш корабль разбит!"
        })

    session["battle"] = battle

    return jsonify({
        "message": player_message,
        "enemy_message": enemy_message,
        "player_hp": battle["player_hp"],
        "enemy_hp": battle["bot_hp"],
        "finished": False
    })


@app.route("/battle/rum", methods=["POST"])
def battle_rum():

    player = get_player()

    if player is None:
        return jsonify({
            "error": "Игрок не найден"
        })

    battle = session.get("battle")

    if not battle:
        return jsonify({
            "error": "Бой не найден"
        })

    # Ром можно пить только при здоровье ниже 25%
    max_hp = battle["max_player_hp"]

    if battle["player_hp"] >= max_hp * 0.25:

        return jsonify({
            "error": "Сейчас ром пить нельзя"
        })

    # Восстанавливаем 50% здоровья
    heal = int(max_hp * 0.50)

    battle["player_hp"] += heal

    if battle["player_hp"] > max_hp:
        battle["player_hp"] = max_hp

    session["battle"] = battle

    return jsonify({
        "player_hp": battle["player_hp"]
    })


    # ---------- Море ----------

@app.route("/sea")
def sea():

    player = get_player()

    if player is None:
        return redirect("/")

    locations = [
        {"name": "Пенная бухта", "level": 1},
        {"name": "Остров Черепа", "level": 10},
        {"name": "Пропащие души", "level": 20},
        {"name": "Логово пиратов", "level": 20},
        {"name": "Сент-Китс", "level": 35},
        {"name": "Ледяные острова", "level": 35},
        {"name": "Сент Люсия", "level": 45},
        {"name": "Тайник Дейви Джонса", "level": 48}
    ]

    player_level = player.get("level", 1)

    for location in locations:
        location["available"] = player_level >= location["level"]

    events = [
        "🌊 Море спокойно. Путешествие продолжается.",
        "💰 Вы нашли сундук с золотом!",
        "🏴‍☠️ На горизонте замечен пиратский корабль.",
        "🐬 Стая дельфинов сопровождает ваш корабль.",
        "🌪️ Начался сильный шторм!",
        "🏝️ Вы обнаружили неизвестный остров.",
        "🦈 Вокруг корабля кружат акулы.",
        "💀 Морской разбойник требует выкуп."
    ]

    event = random.choice(events)

    location = "Порт-Роял"

    if location not in online_locations:
        online_locations[location] = set()

    online_locations[location].add(player["nickname"])

    players_count = max(
        0,
        len(online_locations[location]) - 1
    )

# Боты всегда находятся в локации
bots = LOCATION_BOTS.get(location, [])

# Определяем следующего бота
if location not in bot_turn:
    bot_turn[location] = 0

if bots:
    current_bot = bots[bot_turn[location] % len(bots)]
else:
    current_bot = None

    return render_template(
    "sea.html",
    player=player,
    event=event,
    players_count=players_count,
    locations=locations,
    current_bot=current_bot,
    bots=bots
)

# ---------- Боты Пенной бухты ----------

bots_pennaya_buhta = [
    {
        "name": "Джон Сильвер",
        "level": 1,
        "hp": 100,
        "attack": 10,
        "defense": 5,
        "reward_gold": 50,
        "reward_xp": 20
    },
    {
        "name": "Эдди Крю",
        "level": 2,
        "hp": 130,
        "attack": 13,
        "defense": 7,
        "reward_gold": 75,
        "reward_xp": 30
    },
    {
        "name": "Головорез Джо",
        "level": 3,
        "hp": 170,
        "attack": 17,
        "defense": 10,
        "reward_gold": 100,
        "reward_xp": 40
    }
]


# ---------- Карта ----------

@app.route("/map")
def game_map():

    player = get_player()

    if player is None:
        return redirect("/")

    locations = [
    {"name": "Пенная бухта", "level": 1},
    {"name": "Остров Черепа", "level": 10},
    {"name": "Пропащие души", "level": 20},
    {"name": "Логово пиратов", "level": 20},
    {"name": "Сент-Китс", "level": 35},
    {"name": "Ледяные острова", "level": 35},
    {"name": "Сент Люсия", "level": 45},
    {"name": "Тайник Дейви Джонса", "level": 48}
]

    player_level = player.get("level", 1)

    for location in locations:
        location["available"] = player_level >= location["level"]

    return render_template(
        "map.html",
        player=player,
        locations=locations
    )


# ---------- Путешествие ----------

@app.route("/travel/<int:place>")
def travel(place):

    if "nickname" not in session:
        return redirect("/")

    session["location"] = place

    return redirect("/sea")


# ---------- Капитан ----------

@app.route("/captain")
def captain():

    player = get_player()

    if player is None:
        return redirect("/")

    return render_template(
        "captain.html",
        player=player
    )
    # ---------- Монстры ----------

monsters = [
    {
        "id": "snake",
        "name": "🐍 Морской змей",
        "level": 1,
        "hp": 20000,
        "reward_gold": 0,
        "reward_pearl": 1000,
        "reward_item": "Змеиный глаз",
        "image": "images/monsters/sea_serpent.png"
    }
]


@app.route("/monsters")
def monsters_page():

    player = get_player()

    if player is None:
        return redirect("/")

    available = []

    for monster in monsters:
        if monster["level"] <= player["level"]:
            available.append(monster)

    return render_template(
        "monsters.html",
        player=player,
        monsters=available
    )


# ---------- Морской змей ----------

@app.route("/monster/snake")
def monster_snake():

    player = get_player()

    if player is None:
        return redirect("/")

    battle_log = [
        "🐍 Морской змей появился из глубины моря!",
        "⚔️ Бой начинается..."
    ]

    return render_template(
        "monster_snake.html",
        player=player,
        monster=monsters[0],
        monster_hp=20000,
        monster_max_hp=20000,
        battle_log=battle_log
    )


# ---------- Запуск ----------

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    nickname = session.get("nickname")

    if not nickname:
        return "", 401

    import time

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO online_players (nickname, last_seen)
        VALUES (?, ?)
    """, (nickname, int(time.time())))

    conn.commit()
    conn.close()

    return "", 204

@app.route("/online_count")
def online_count():
    import time

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Удаляем игроков, которые не выходили на связь больше 60 секунд
    limit = int(time.time()) - 60

    cur.execute(
        "DELETE FROM online_players WHERE last_seen < ?",
        (limit,)
    )

    conn.commit()

    # Считаем игроков онлайн
    cur.execute("SELECT COUNT(*) FROM online_players")
    count = cur.fetchone()[0]

    conn.close()

    return {"count": count}

@app.route("/players")
def players_search():
    if "nickname" not in session:
        return redirect("/")

    query = request.args.get("q", "").strip()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT nickname, level
            FROM players
            WHERE nickname LIKE ?
            ORDER BY level DESC, nickname
            LIMIT 30
        """, (f"%{query}%",))
        players = cur.fetchall()
    else:
        players = []

    conn.close()

    return render_template(
        "players.html",
        players=players,
        query=query
    )


@app.route("/player/<nickname>")
def player_profile(nickname):
    if "nickname" not in session:
        return redirect("/")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT nickname, gender, hp, xp, gold, piastres, pearls, level
        FROM players
        WHERE nickname = ?
    """, (nickname,))

    player = cur.fetchone()
    conn.close()

    if player is None:
        return "Игрок не найден", 404

    return render_template(
        "player_profile.html",
        player=player
    )

@app.route("/poseidon")
def poseidon():
    return "<h1>🔱 Трезубец Посейдона</h1><p>Битва с Посейдоном скоро будет доступна!</p>"

@app.route("/quests")
def quests():
    return "<h1>📜 Задания</h1><p>Задания скоро будут доступны!</p>"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )