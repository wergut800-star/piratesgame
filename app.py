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
        SELECT nickname, hp, xp, gold, piastres, pearls, level, gender
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
    # ---------- Море ----------

@app.route("/sea")
def sea():

    player = get_player()

    if player is None:
        return redirect("/")

    events = [
        "🌊 Море спокойно. Путешествие продолжается.",
        "💰 Вы нашли сундук с золотом!",
        "🦜 На горизонте замечен пиратский корабль.",
        "🐬 Стая дельфинов сопровождает ваш корабль.",
        "🌪 Начался сильный шторм!",
        "🏝 Вы обнаружили неизвестный остров.",
        "🦈 Вокруг корабля кружат акулы.",
        "☠️ Морской разбойник требует выкуп."
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

    return render_template(
        "sea.html",
        player=player,
        event=event,
        players_count=players_count
    )


# ---------- Карта ----------

@app.route("/map")
def game_map():

    player = get_player()

    if player is None:
        return redirect("/")

    locations = [
        {"name": "Порт Роял", "level": 1},
        {"name": "Остров Черепа", "level": 10},
        {"name": "Пенная бухта", "level": 20},
        {"name": "Логово пиратов", "level": 20},
        {"name": "Сантьяга", "level": 35},
        {"name": "Грамвуса", "level": 35},
        {"name": "Вирджиния", "level": 45},
        {"name": "Тортуга", "level": 48}
    ]

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

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )