"""Min Yidri: synchronized Arabic team guessing rooms over WebSockets."""

from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response

from cards_v2 import CARDS as CURATED_CARDS
from mini_games import EMOJI_PUZZLES, IMPOSTER_WORDS


ROOT = Path(__file__).resolve().parent
ROOM_TTL_SECONDS = 2 * 60 * 60

CARDS = [
    {"type": "ممنوع تقولها", "icon": "🤐", "time": 40, "points": 2, "prompt": "اشرح لفريقك كلمة «كبسة»", "hint": "ممنوع تقول: رز، دجاج، أكل، قدر"},
    {"type": "مثّلها يا بطل", "icon": "🎭", "time": 35, "points": 2, "prompt": "واحد يحاول يفتح كيس شبس بهدوء والكل نايم", "hint": "تمثيل بدون كلام أو أصوات واضحة"},
    {"type": "سَلِّكها", "icon": "🎤", "time": 45, "points": 3, "prompt": "أنت مذيع أخبار وتوك اكتشفت إن الورق اللي بيدك قائمة مقاضي", "hint": "كمّل النشرة بثقة لمدة 20 ثانية"},
    {"type": "ثلاثة بس", "icon": "⚡", "time": 10, "points": 2, "prompt": "سمّوا 3 أشياء تلقاها في شنطة الأم", "hint": "قبل ما يخلص الوقت القصير"},
    {"type": "ممنوع تقولها", "icon": "🤐", "time": 40, "points": 2, "prompt": "اشرح لفريقك كلمة «زحمة»", "hint": "ممنوع تقول: سيارات، شارع، طريق، واقف"},
    {"type": "كَمّل السالفة", "icon": "🧠", "time": 45, "points": 3, "prompt": "بدأت السالفة بـ: «دخلت المطبخ الساعة ٣ الفجر وفجأة…»", "hint": "كل لاعب يضيف جملة، وممنوع التناقض أو التأخير"},
    {"type": "صوت بس", "icon": "📣", "time": 30, "points": 2, "prompt": "خلّي فريقك يعرف: ماكينة قهوة تعطّلت", "hint": "بالأصوات فقط، ممنوع الكلام أو التمثيل باليد"},
    {"type": "مين يعرفكم؟", "icon": "👀", "time": 25, "points": 2, "prompt": "اختاروا الشخص الأكثر احتمالًا ينسى جواله في الثلاجة", "hint": "النقاط إذا الأغلبية أشارت لنفس الشخص"},
    {"type": "تحدّي الذاكرة", "icon": "🧩", "time": 35, "points": 3, "prompt": "قولوا بالتتابع: «رحت البقالة وجبت…»", "hint": "كل واحد يكرر القائمة ويزيد غرضًا؛ انجحوا في 7 أغراض"},
    {"type": "مثّلها يا بطل", "icon": "🎭", "time": 35, "points": 2, "prompt": "مندوب توصيل ضايع ويشرح الموقع لصاحب البيت", "hint": "بدون كلام — البقية يخمّنوا المشهد"},
    {"type": "المحامي", "icon": "⚖️", "time": 40, "points": 3, "prompt": "دافع عن رأي: المنبّه أكثر اختراع ظالم في التاريخ", "hint": "خطاب مقنع لمدة 20 ثانية"},
    {"type": "ثلاثة بس", "icon": "⚡", "time": 10, "points": 2, "prompt": "سمّوا 3 أعذار للتأخير غير الزحمة", "hint": "بسرعة، وممنوع تكرار نفس الفكرة"},
    {"type": "الدبلجة", "icon": "🎬", "time": 35, "points": 3, "prompt": "لاعبان يمثلوا نقاشًا صامتًا بين قطوتين، وثالث يدبلج الاثنين", "hint": "لازم يكون للنقاش بداية ونهاية مفهومة"},
    {"type": "ممنوع تقولها", "icon": "🤐", "time": 40, "points": 2, "prompt": "اشرح لفريقك كلمة «واتساب»", "hint": "ممنوع تقول: رسالة، جوال، قروب، أخضر"},
    {"type": "خبير من كيسك", "icon": "🧪", "time": 45, "points": 3, "prompt": "اشرح علميًا: ليش الريموت يختفي دايمًا؟", "hint": "استخدم كلمتين على الأقل: جاذبية، موجات، نظرية"},
    {"type": "لقطة حجازية", "icon": "🪭", "time": 30, "points": 2, "prompt": "مثّل شخص يقول «دحين أجيك» وهو لسه ما قام", "hint": "ممنوع ذكر الجملة نفسها"},
    {"type": "تحدّي التزامن", "icon": "🤝", "time": 30, "points": 3, "prompt": "ثلاثة من الفريق يعدّوا من 1 إلى 10 بدون ترتيب مسبق", "hint": "إذا تكلم اثنان مع بعض ترجعوا من البداية"},
    {"type": "إعلان مضروب", "icon": "📺", "time": 45, "points": 3, "prompt": "سوّوا إعلانًا فاخرًا لشبشب ضايعة فردته الثانية", "hint": "لازم فيه اسم منتج وشعار وسبب للشراء"},
    {"type": "فكّ الشفرة", "icon": "🔐", "time": 35, "points": 3, "prompt": "وصلوا لفريقكم الجملة: «العشاء جاهز» بثلاث كلمات", "hint": "ممنوع استخدام: أكل، جوع، مطبخ"},
    {"type": "مين يعرفكم؟", "icon": "👀", "time": 25, "points": 2, "prompt": "مين لو صار مشهور أول شيء يسويه يغير رقمه؟", "hint": "النقاط إذا اختار الفريق نفس اختيار أغلبية الجلسة"},
    {"type": "سَلِّكها", "icon": "🎤", "time": 40, "points": 3, "prompt": "اعتذر رسميًا لنبتة لأنك نسيت تسقيها", "hint": "خلك جاد جدًا ولا تضحك لمدة 20 ثانية"},
    {"type": "قلب المعنى", "icon": "🔄", "time": 35, "points": 2, "prompt": "امدح الزحمة كأنها أفضل شيء حصل لك اليوم", "hint": "اذكر 3 فوائد مقنعة — أو شبه مقنعة"},
    {"type": "صوت بس", "icon": "📣", "time": 30, "points": 2, "prompt": "خلّي فريقك يعرف: واحد يمشي على أرض حارة", "hint": "بالصوت فقط، ولا تقول أي كلمة"},
    {"type": "تحدّي الصورة", "icon": "🗿", "time": 25, "points": 2, "prompt": "كوّنوا تمثالًا جماعيًا بعنوان «آخر حبة سمبوسة»", "hint": "عندكم 10 ثواني للتحضير ثم تجمّدوا"},
    {"type": "ممنوع تقولها", "icon": "🤐", "time": 40, "points": 2, "prompt": "اشرح لفريقك كلمة «استراحة»", "hint": "ممنوع تقول: شباب، كورة، شاليه، ويكند"},
    {"type": "المخرج", "icon": "🎬", "time": 45, "points": 3, "prompt": "مثّلوا طلب شاورما كأنه مشهد أكشن", "hint": "شخصان على الأقل، ومع مؤثرات صوتية"},
    {"type": "الجواب الغلط", "icon": "🙃", "time": 30, "points": 3, "prompt": "جاوبوا بإجابات غلط فقط: فين ننام؟ إيش نشرب؟ إيش نلبس؟", "hint": "الحَكَم يسأل 8 أسئلة؛ أي جواب منطقي يخسّركم"},
    {"type": "تحدّي الحروف", "icon": "🔤", "time": 35, "points": 3, "prompt": "قولوا 6 أشياء في البيت تبدأ بحرف «م»", "hint": "بدون أسماء أشخاص أو تكرار"},
    {"type": "خبير من كيسك", "icon": "🧪", "time": 45, "points": 3, "prompt": "قدّم محاضرة عن فن اختيار مكان الجلسة في المجلس", "hint": "استخدم: استراتيجية، زاوية، شاحن"},
    {"type": "التوأم", "icon": "👯", "time": 30, "points": 3, "prompt": "لاعبان يقولان معًا: شيء نطلبه آخر الليل", "hint": "ثلاث محاولات فقط، وممنوع الاتفاق قبلها"},
    {"type": "لقطة حجازية", "icon": "🪭", "time": 35, "points": 2, "prompt": "مثّلوا واحد ضيّع سيارته في مواقف المول ويحاول يكون هادي", "hint": "لاعب واحد والبقية تخمّن"},
    {"type": "إعلان مضروب", "icon": "📺", "time": 45, "points": 3, "prompt": "بيعوا اختراعًا: زر يسكّت إشعارات القروبات ساعة", "hint": "اسم وسعر وشعار إعلاني لا يُنسى"},
    {"type": "كَمّل السالفة", "icon": "🧠", "time": 45, "points": 3, "prompt": "دق الباب ولقينا كرتونًا مكتوبًا عليه: لا تفتحوه…", "hint": "كل شخص جملة؛ 6 جمل متماسكة على الأقل"},
    {"type": "تحدّي التزامن", "icon": "🤝", "time": 25, "points": 2, "prompt": "كل الفريق يصفّق في نفس اللحظة بدون قائد أو عدّ", "hint": "عندكم 3 محاولات فقط"},
    {"type": "المحامي", "icon": "⚖️", "time": 40, "points": 3, "prompt": "أقنعوا الجلسة أن النوم بعد العصر رياضة رسمية", "hint": "قدّموا سببين وشعارًا للرياضة"},
    {"type": "فكّ الشفرة", "icon": "🔐", "time": 35, "points": 3, "prompt": "وصلوا لفريقكم: «نسيت المفتاح داخل السيارة»", "hint": "4 كلمات فقط، وممنوع: مفتاح، سيارة، نسيت"},
]

# Version 2 uses only cards that fit the one-explainer/guessing mechanic.
CARDS = CURATED_CARDS


@dataclass
class Player:
    id: str
    name: str
    team: int
    socket: WebSocket | None = None


@dataclass
class Room:
    code: str
    host_id: str
    players: dict[str, Player] = field(default_factory=dict)
    phase: str = "lobby"
    mode: str = "team"
    team_names: list[str] = field(default_factory=lambda: ["الفريق الأصفر", "الفريق الأحمر"])
    scores: list[int] = field(default_factory=lambda: [0, 0])
    powers: list[dict[str, bool]] = field(default_factory=lambda: [
        {"double": True, "time": True}, {"double": True, "time": True}
    ])
    total_rounds: int = 12
    round_index: int = 0
    current_team: int = 0
    active_player_id: str | None = None
    turn_cursors: list[int] = field(default_factory=lambda: [0, 0])
    card_index: int | None = None
    used_cards: list[int] = field(default_factory=list)
    revealed: bool = False
    deadline: float | None = None
    paused_remaining: float | None = None
    multiplier: int = 1
    personal_scores: dict[str, int] = field(default_factory=dict)
    puzzle_index: int | None = None
    used_puzzles: list[int] = field(default_factory=list)
    guesses: dict[str, str] = field(default_factory=dict)
    emoji_answer_revealed: bool = False
    imposter_category: str = "عشوائي"
    imposter_count: int = 1
    secret_word: str | None = None
    imposter_ids: list[str] = field(default_factory=list)
    role_deadline: float | None = None
    imposter_options: list[str] = field(default_factory=list)
    imposter_guesses: dict[str, str] = field(default_factory=dict)
    imposters_revealed: bool = False
    imposter_answer_revealed: bool = False
    updated_at: float = field(default_factory=time.time)


app = FastAPI(title="مين يدري")
rooms: dict[str, Room] = {}


def room_code() -> str:
    for _ in range(100):
        code = str(random.randint(1000, 9999))
        if code not in rooms:
            return code
    raise RuntimeError("Could not allocate a room code")


def safe_name(value: Any, fallback: str = "لاعب") -> str:
    value = " ".join(str(value or "").strip().split())[:22]
    return value or fallback


def pick_card(room: Room) -> int:
    available = [i for i in range(len(CARDS)) if i not in room.used_cards]
    if not available:
        room.used_cards.clear()
        available = list(range(len(CARDS)))
    index = random.choice(available)
    room.used_cards.append(index)
    return index


def public_state(room: Room, viewer_id: str) -> dict[str, Any]:
    card = CARDS[room.card_index] if room.card_index is not None else None
    viewer = room.players.get(viewer_id)
    can_see_answer = bool(
        card
        and room.revealed
        and viewer
        and (viewer.id == room.active_player_id or viewer.team != room.current_team)
    )
    visible_card = None
    if card:
        visible_card = {
            "type": card["type"],
            "icon": card["icon"],
            "time": card["time"],
            "points": card["points"] * room.multiplier,
            "prompt": card["prompt"] if can_see_answer else None,
            "hint": card["hint"] if can_see_answer else None,
        }
    result = {
        "type": "state",
        "server_time": time.time(),
        "room": room.code,
        "you": viewer_id,
        "host_id": room.host_id,
        "phase": room.phase,
        "mode": room.mode,
        "players": [
            {"id": p.id, "name": p.name, "team": p.team, "connected": p.socket is not None}
            for p in room.players.values()
        ],
        "team_names": room.team_names,
        "scores": room.scores,
        "powers": room.powers,
        "total_rounds": room.total_rounds,
        "round_index": room.round_index,
        "current_team": room.current_team,
        "active_player_id": room.active_player_id,
        "card": visible_card,
        "revealed": room.revealed,
        "deadline": room.deadline,
        "paused_remaining": room.paused_remaining,
        "can_see_answer": can_see_answer,
        "personal_scores": room.personal_scores,
        "imposter_category": room.imposter_category,
        "imposter_count": room.imposter_count,
    }
    if room.mode == "emoji" and room.puzzle_index is not None:
        puzzle = EMOJI_PUZZLES[room.puzzle_index]
        show_all_guesses = viewer_id == room.host_id or room.emoji_answer_revealed
        result["emoji"] = {
            "category": puzzle["category"],
            "clue": puzzle["clue"],
            "answer": puzzle["answer"] if (viewer_id == room.host_id or room.emoji_answer_revealed) else None,
            "answer_revealed": room.emoji_answer_revealed,
            "guesses": room.guesses if show_all_guesses else {
                pid: (guess if pid == viewer_id else "تم إرسال التخمين")
                for pid, guess in room.guesses.items()
            },
        }
    if room.mode == "imposter" and room.secret_word:
        is_imposter = viewer_id in room.imposter_ids
        result["imposter"] = {
            "category": room.imposter_category,
            "your_role": "imposter" if is_imposter else "knows",
            "word": room.secret_word if (not is_imposter or room.imposter_answer_revealed) else None,
            "role_deadline": room.role_deadline,
            "imposters_revealed": room.imposters_revealed,
            "imposter_ids": room.imposter_ids if room.imposters_revealed else [],
            "options": room.imposter_options if (is_imposter and room.imposters_revealed) else [],
            "guesses": room.imposter_guesses if room.imposter_answer_revealed else {},
            "answer_revealed": room.imposter_answer_revealed,
        }
    return result


async def send_error(socket: WebSocket, message: str) -> None:
    await socket.send_json({"type": "error", "message": message})


async def broadcast(room: Room) -> None:
    room.updated_at = time.time()
    dead: list[str] = []
    for player in list(room.players.values()):
        if player.socket is None:
            continue
        try:
            await player.socket.send_json(public_state(room, player.id))
        except Exception:
            player.socket = None
            dead.append(player.id)
    if room.host_id in dead:
        choose_new_host(room)


def choose_new_host(room: Room) -> None:
    connected = [p for p in room.players.values() if p.socket is not None]
    if connected:
        room.host_id = connected[0].id


def require_host(room: Room, player_id: str) -> bool:
    return room.host_id == player_id


def choose_active_player(room: Room) -> None:
    eligible = [
        player for player in room.players.values()
        if player.team == room.current_team and player.socket is not None
    ]
    if not eligible:
        room.active_player_id = None
        return
    cursor = room.turn_cursors[room.current_team] % len(eligible)
    room.active_player_id = eligible[cursor].id
    room.turn_cursors[room.current_team] = (cursor + 1) % len(eligible)


def start_round(room: Room) -> None:
    room.card_index = pick_card(room)
    choose_active_player(room)
    room.revealed = False
    room.deadline = None
    room.paused_remaining = None
    room.multiplier = 1


def pick_puzzle(room: Room) -> int:
    available = [i for i in range(len(EMOJI_PUZZLES)) if i not in room.used_puzzles]
    if not available:
        room.used_puzzles.clear()
        available = list(range(len(EMOJI_PUZZLES)))
    index = random.choice(available)
    room.used_puzzles.append(index)
    return index


def start_emoji_round(room: Room) -> None:
    room.puzzle_index = pick_puzzle(room)
    room.guesses.clear()
    room.emoji_answer_revealed = False


def start_imposter_round(room: Room) -> None:
    connected = [p for p in room.players.values() if p.socket is not None]
    category = room.imposter_category
    if category == "عشوائي" or category not in IMPOSTER_WORDS:
        category = random.choice(list(IMPOSTER_WORDS))
    room.imposter_category = category
    room.secret_word = random.choice(IMPOSTER_WORDS[category])
    room.imposter_ids = [p.id for p in random.sample(connected, min(room.imposter_count, len(connected) - 1))]
    wrong = [w for w in IMPOSTER_WORDS[category] if w != room.secret_word]
    room.imposter_options = random.sample(wrong, 3) + [room.secret_word]
    random.shuffle(room.imposter_options)
    room.role_deadline = time.time() + 15
    room.imposter_guesses.clear()
    room.imposters_revealed = room.imposter_answer_revealed = False


def reset_to_lobby(room: Room) -> None:
    room.phase = "lobby"
    room.round_index = 0
    room.card_index = room.puzzle_index = None
    room.active_player_id = None
    room.revealed = room.emoji_answer_revealed = False
    room.deadline = room.paused_remaining = None
    room.secret_word = None
    room.imposter_ids.clear(); room.imposter_options.clear(); room.imposter_guesses.clear()
    room.imposters_revealed = room.imposter_answer_revealed = False


async def process_action(room: Room, player: Player, data: dict[str, Any]) -> None:
    action = data.get("action")
    if action == "ping":
        await player.socket.send_json({"type": "pong"})
        return

    if action == "set_team" and room.phase == "lobby":
        team = int(data.get("team", -1))
        if team in (0, 1):
            player.team = team
            await broadcast(room)
        return

    if action == "set_team_name" and room.phase == "lobby" and require_host(room, player.id):
        team = int(data.get("team", -1))
        if team in (0, 1):
            room.team_names[team] = safe_name(data.get("name"), room.team_names[team])
            await broadcast(room)
        return

    if action == "set_mode" and room.phase == "lobby" and require_host(room, player.id):
        mode = str(data.get("mode"))
        if mode in ("team", "emoji", "imposter"):
            room.mode = mode
            await broadcast(room)
        return

    if action == "set_imposter" and room.phase == "lobby" and require_host(room, player.id):
        category = str(data.get("category", "عشوائي"))
        room.imposter_category = category if category == "عشوائي" or category in IMPOSTER_WORDS else "عشوائي"
        room.imposter_count = 2 if int(data.get("count", 1)) == 2 else 1
        await broadcast(room)
        return

    if action == "submit_guess" and room.phase == "game" and room.mode == "emoji":
        guess = " ".join(str(data.get("guess", "")).strip().split())[:40]
        if guess:
            room.guesses[player.id] = guess
            await broadcast(room)
        return

    if action == "submit_imposter_choice" and room.phase == "game" and room.mode == "imposter":
        choice = str(data.get("choice", ""))
        if player.id in room.imposter_ids and choice in room.imposter_options:
            room.imposter_guesses[player.id] = choice
            await broadcast(room)
        return

    if not require_host(room, player.id):
        await send_error(player.socket, "هذا الزر عند المضيف فقط")
        return

    if action == "return_lobby":
        reset_to_lobby(room)
        await broadcast(room)
        return

    if action == "close_room":
        for p in list(room.players.values()):
            if p.socket:
                try:
                    await p.socket.send_json({"type": "room_closed", "message": "المضيف أنهى الغرفة"})
                    await p.socket.close()
                except Exception:
                    pass
                p.socket = None
        rooms.pop(room.code, None)
        return

    if action == "start" and room.phase == "lobby":
        connected = [p for p in room.players.values() if p.socket is not None]
        minimum = 3 if room.mode == "imposter" else 2
        if len(connected) < minimum:
            await send_error(player.socket, f"هذه اللعبة تحتاج {minimum} لاعبين متصلين على الأقل")
            return
        if room.mode == "team" and {p.team for p in connected} != {0, 1}:
            await send_error(player.socket, "لازم لاعب في كل فريق")
            return
        rounds = int(data.get("rounds", 12))
        room.total_rounds = rounds if rounds in (5, 8, 10, 12, 16) else 8
        room.phase = "game"
        room.personal_scores = {p.id: 0 for p in connected}
        room.scores = [0, 0]
        room.powers = [{"double": True, "time": True}, {"double": True, "time": True}]
        room.round_index = 0
        room.current_team = 0
        room.turn_cursors = [0, 0]
        if room.mode == "team":
            room.used_cards.clear(); start_round(room)
        elif room.mode == "emoji":
            room.used_puzzles.clear(); start_emoji_round(room)
        else:
            start_imposter_round(room)
        await broadcast(room)
        return

    if action == "reveal" and room.phase == "game" and room.mode == "team" and not room.revealed:
        if room.active_player_id is None:
            await send_error(player.socket, "لا يوجد لاعب متصل في الفريق الحالي")
            return
        room.revealed = True
        room.deadline = time.time() + CARDS[room.card_index]["time"]
        room.paused_remaining = None
        await broadcast(room)
        return

    if action == "power" and room.phase == "game" and room.mode == "team":
        power = data.get("power")
        team = room.current_team
        if power == "double" and room.powers[team]["double"]:
            room.powers[team]["double"] = False
            room.multiplier = 2
        elif power == "time" and room.powers[team]["time"] and room.revealed:
            room.powers[team]["time"] = False
            if room.deadline is not None:
                room.deadline += 15
            elif room.paused_remaining is not None:
                room.paused_remaining += 15
        await broadcast(room)
        return

    if action == "pause" and room.phase == "game" and room.mode == "team" and room.revealed and room.deadline is not None:
        room.paused_remaining = max(0.0, room.deadline - time.time())
        room.deadline = None
        await broadcast(room)
        return

    if action == "resume" and room.phase == "game" and room.mode == "team" and room.revealed and room.paused_remaining is not None:
        room.deadline = time.time() + room.paused_remaining
        room.paused_remaining = None
        await broadcast(room)
        return

    if action == "resolve" and room.phase == "game" and room.mode == "team":
        success = bool(data.get("success"))
        if success:
            scoring_team = room.current_team
            points = CARDS[room.card_index]["points"] * room.multiplier
            room.scores[scoring_team] += points
        room.round_index += 1
        if room.round_index >= room.total_rounds:
            room.phase = "end"
            room.deadline = None
        else:
            room.current_team = 1 - room.current_team
            start_round(room)
        await broadcast(room)
        return

    if action == "reveal_emoji" and room.phase == "game" and room.mode == "emoji":
        room.emoji_answer_revealed = True
        await broadcast(room); return

    if action == "award_guess" and room.phase == "game" and room.mode == "emoji":
        winner = str(data.get("player_id", ""))
        if winner in room.personal_scores: room.personal_scores[winner] += 1
        room.round_index += 1
        if room.round_index >= room.total_rounds: room.phase = "end"
        else: start_emoji_round(room)
        await broadcast(room); return

    if action == "reveal_imposters" and room.phase == "game" and room.mode == "imposter":
        room.imposters_revealed = True
        await broadcast(room); return

    if action == "reveal_imposter_answer" and room.phase == "game" and room.mode == "imposter":
        room.imposter_answer_revealed = True
        await broadcast(room); return

    if action == "award_person" and room.phase == "game" and room.mode == "imposter":
        winner = str(data.get("player_id", ""))
        if winner in room.personal_scores: room.personal_scores[winner] += 1
        await broadcast(room); return

    if action == "next_imposter" and room.phase == "game" and room.mode == "imposter":
        room.round_index += 1
        if room.round_index >= room.total_rounds: room.phase = "end"
        else: start_imposter_round(room)
        await broadcast(room); return

    if action == "restart" and room.phase == "end":
        reset_to_lobby(room)
        await broadcast(room)


@app.get("/")
async def home() -> HTMLResponse:
    return HTMLResponse((ROOT / "index.html").read_text(encoding="utf-8"))


@app.get("/game.js")
async def game_script() -> Response:
    return Response((ROOT / "game.js").read_text(encoding="utf-8"), media_type="application/javascript")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "rooms": len(rooms)})


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    room: Room | None = None
    player: Player | None = None
    try:
        hello = await asyncio.wait_for(socket.receive_json(), timeout=20)
        action = hello.get("action")
        requested_id = str(hello.get("player_id") or "")

        if action == "create":
            code = room_code()
            player = Player(uuid.uuid4().hex, safe_name(hello.get("name"), "المضيف"), 0, socket)
            room = Room(code=code, host_id=player.id)
            room.players[player.id] = player
            rooms[code] = room
        elif action == "join":
            code = str(hello.get("room") or "").strip()
            room = rooms.get(code)
            if room is None:
                await send_error(socket, "الغرفة غير موجودة أو انتهت")
                await socket.close()
                return
            if requested_id in room.players:
                player = room.players[requested_id]
                player.socket = socket
                player.name = safe_name(hello.get("name"), player.name)
            elif room.phase == "lobby":
                connected_counts = [
                    sum(1 for p in room.players.values() if p.team == team and p.socket is not None)
                    for team in (0, 1)
                ]
                team = 0 if connected_counts[0] <= connected_counts[1] else 1
                player = Player(uuid.uuid4().hex, safe_name(hello.get("name")), team, socket)
                room.players[player.id] = player
            else:
                await send_error(socket, "اللعبة بدأت؛ انتظروا الجولة القادمة")
                await socket.close()
                return
        else:
            await send_error(socket, "طلب دخول غير صحيح")
            await socket.close()
            return

        await socket.send_json({"type": "welcome", "player_id": player.id, "room": room.code})
        await broadcast(room)

        while True:
            data = await socket.receive_json()
            await process_action(room, player, data)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except (ValueError, TypeError, json.JSONDecodeError):
        if socket.client_state.name == "CONNECTED":
            await send_error(socket, "وصلت بيانات غير صحيحة")
    finally:
        if room and player and player.socket is socket:
            player.socket = None
            if room.host_id == player.id:
                choose_new_host(room)
            if room.phase == "game" and room.active_player_id == player.id:
                choose_active_player(room)
            if room.code in rooms:
                await broadcast(room)


async def cleanup_rooms() -> None:
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - ROOM_TTL_SECONDS
        for code, room in list(rooms.items()):
            if room.updated_at < cutoff and not any(p.socket for p in room.players.values()):
                rooms.pop(code, None)


@app.on_event("startup")
async def start_cleanup() -> None:
    asyncio.create_task(cleanup_rooms())
