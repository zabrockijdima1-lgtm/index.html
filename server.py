import asyncio, json, math, os, random, time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Стан гри ─────────────────────────────────────────────────────────────────
clients: dict[int, WebSocket] = {}   # uid → ws
players: dict[int, dict] = {}        # uid → {name, nick, photo, balance}
bets:    dict[int, dict] = {}        # uid → {amount, auto_cashout, cashed}

class G:
    phase     = "waiting"
    mult      = 1.0
    crash_at  = 1.0
    start_ts  = 0.0
    round_id  = 0
    history:  list = []
    SPEED     = 0.18   # швидкість ракети

g = G()

# ── Crash generator ────────────────────────────────────────────────────────────
def gen_crash() -> float:
    r = random.random()
    if r < 0.05: return 1.00
    return round(min(0.95 / (1 - r), 500), 2)

# ── Broadcast ──────────────────────────────────────────────────────────────────
async def broadcast(msg: dict):
    data = json.dumps(msg)
    dead = []
    for uid, ws in list(clients.items()):
        try:
            await ws.send_text(data)
        except:
            dead.append(uid)
    for uid in dead:
        clients.pop(uid, None)

def players_list():
    rows = []
    for uid, bet in bets.items():
        p = players.get(uid, {})
        rows.append({
            "uid":    uid,
            "name":   p.get("name", "?"),
            "nick":   p.get("nick", ""),
            "photo":  p.get("photo", ""),
            "bet":    bet["amount"],
            "cashed": bet.get("cashed", False),
            "win":    bet.get("win"),
            "mult":   bet.get("mult"),
            "lost":   bet.get("lost", False),
        })
    return rows

# ── Game loop ──────────────────────────────────────────────────────────────────
async def game_loop():
    while True:
        # ── WAITING ──────────────────────────────────────────────────────────
        g.phase    = "waiting"
        g.mult     = 1.0
        g.crash_at = gen_crash()
        g.round_id += 1
        bets.clear()

        for cd in range(5, 0, -1):
            await broadcast({
                "t": "cd",
                "sec": cd,
                "rid": g.round_id,
                "ca":  g.crash_at,
                "now": time.time(),
            })
            await asyncio.sleep(1)

        # ── FLYING ───────────────────────────────────────────────────────────
        g.phase    = "flying"
        g.start_ts = time.time()

        await broadcast({
            "t":   "st",
            "ts":  g.start_ts,
            "ca":  g.crash_at,
            "rid": g.round_id,
            "now": time.time(),
        })

        while True:
            elapsed  = time.time() - g.start_ts
            g.mult   = round(math.exp(elapsed * g.SPEED), 2)

            if g.mult >= g.crash_at:
                g.mult = g.crash_at
                break

            # Авто-cashout
            for uid, bet in list(bets.items()):
                if bet.get("cashed") or bet.get("lost"):
                    continue
                ac = bet.get("auto_cashout")
                if ac and g.mult >= ac:
                    await do_cashout(uid, g.mult)

            await broadcast({"t": "tick", "m": g.mult, "now": time.time()})
            await asyncio.sleep(0.07)

        # ── CRASHED ──────────────────────────────────────────────────────────
        g.phase = "crashed"
        g.history.insert(0, g.crash_at)
        g.history = g.history[:20]

        for uid, bet in bets.items():
            if not bet.get("cashed"):
                bet["lost"] = True

        await broadcast({
            "t":   "cr",
            "ca":  g.crash_at,
            "rid": g.round_id,
            "h":   g.history,
            "pl":  players_list(),
            "now": time.time(),
        })

        await asyncio.sleep(3)

async def do_cashout(uid: int, mult: float):
    bet = bets.get(uid)
    if not bet or bet.get("cashed"):
        return
    win = round(bet["amount"] * mult, 4)
    bet["cashed"] = True
    bet["win"]    = win
    bet["mult"]   = mult
    if uid in players:
        players[uid]["balance"] = round(players[uid]["balance"] + win, 4)
    await broadcast({
        "t":   "co",
        "uid": uid,
        "win": win,
        "mx":  mult,
        "pl":  players_list(),
        "now": time.time(),
    })
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":  "your_co",
                "win": win,
                "mx":  mult,
                "bal": players[uid]["balance"],
            }))
        except:
            pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(game_loop())

# ── WebSocket ──────────────────────────────────────────────────────────────────
@app.websocket("/ws/{uid}")
async def ws(websocket: WebSocket, uid: int):
    await websocket.accept()
    clients[uid] = websocket

    # Надсилаємо поточний стан
    await websocket.send_text(json.dumps({
        "t":    "init",
        "phase": g.phase,
        "mult":  g.mult,
        "ts":    g.start_ts,
        "ca":    g.crash_at,
        "rid":   g.round_id,
        "h":     g.history,
        "pl":    players_list(),
        "bal":   players.get(uid, {}).get("balance", 1.0),
        "now":   time.time(),
    }))

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)
            action = data.get("a")

            if action == "auth":
                players[uid] = {
                    "name":    data.get("name", "Player"),
                    "nick":    data.get("nick", ""),
                    "photo":   data.get("photo", ""),
                    "balance": players.get(uid, {}).get("balance", 1.0),
                }

            elif action == "bet":
                if g.phase != "waiting":
                    continue
                amount = float(data.get("amt", 0))
                bal    = players.get(uid, {}).get("balance", 0)
                if amount < 0.1 or amount > bal:
                    await websocket.send_text(json.dumps({"t": "err", "msg": "Недостатньо TON"}))
                    continue
                players[uid]["balance"] = round(bal - amount, 4)
                bets[uid] = {
                    "amount":       amount,
                    "auto_cashout": data.get("ac"),
                    "cashed":       False,
                    "lost":         False,
                }
                await websocket.send_text(json.dumps({
                    "t":   "bet_ok",
                    "amt": amount,
                    "bal": players[uid]["balance"],
                }))
                await broadcast({"t": "newbet", "pl": players_list(), "now": time.time()})

            elif action == "cashout":
                if g.phase == "flying" and uid in bets:
                    await do_cashout(uid, g.mult)

    except WebSocketDisconnect:
        clients.pop(uid, None)

# ── Топ-ап (для боту) ──────────────────────────────────────────────────────────
@app.post("/topup/{uid}/{amount}")
async def topup(uid: int, amount: float):
    if uid not in players:
        players[uid] = {"name": "Player", "nick": "", "photo": "", "balance": 0}
    players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":       "topup",
                "credited": amount,
                "bal":      players[uid]["balance"],
            }))
        except:
            pass
    return {"ok": True, "balance": players[uid]["balance"]}

@app.get("/")
async def root():
    return {"status": "ok", "round": g.round_id, "phase": g.phase, "players": len(clients)}
