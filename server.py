import asyncio, json, math, os, random, time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── NFT каталог (симульований) ────────────────────────────────────────────────
NFT_CATALOG = [
    {"id":"nft001","name":"Crystal Dragon","img":"https://i.imgur.com/8Rm6hGc.png","floor":2.8,"rarity":"Common"},
    {"id":"nft002","name":"Golden Phoenix","img":"https://i.imgur.com/9KpLmNs.png","floor":5.5,"rarity":"Rare"},
    {"id":"nft003","name":"Shadow Wolf","img":"https://i.imgur.com/3TqWxYv.png","floor":12.0,"rarity":"Epic"},
    {"id":"nft004","name":"Cosmic Bear","img":"https://i.imgur.com/7HnRtQp.png","floor":28.0,"rarity":"Legendary"},
    {"id":"nft005","name":"Neon Tiger","img":"https://i.imgur.com/2KmPsXw.png","floor":3.5,"rarity":"Common"},
    {"id":"nft006","name":"Rainbow Unicorn","img":"https://i.imgur.com/5LpQrNz.png","floor":8.0,"rarity":"Rare"},
    {"id":"nft007","name":"Dark Matter Fox","img":"https://i.imgur.com/4GhYuKm.png","floor":50.0,"rarity":"Legendary"},
    {"id":"nft008","name":"Pixel Panda","img":"https://i.imgur.com/6JkMvBn.png","floor":2.8,"rarity":"Common"},
]

def get_nft_for_win(win_ton: float) -> dict | None:
    """Підбираємо NFT за виграшем в TON"""
    if win_ton < 2.8:
        return None
    candidates = [n for n in NFT_CATALOG if n["floor"] <= win_ton * 1.2]
    if not candidates:
        return NFT_CATALOG[0]
    # Обираємо найдорожчий що вписується в бюджет
    best = max(candidates, key=lambda n: n["floor"])
    return best

def get_nft_preview(bet_ton: float, current_mult: float) -> dict | None:
    """NFT прев'ю під час польоту"""
    potential_win = bet_ton * current_mult
    return get_nft_for_win(potential_win)

# ── Стан гри ─────────────────────────────────────────────────────────────────
clients: dict = {}
players: dict = {}
bets:    dict = {}

class G:
    phase    = "waiting"
    mult     = 1.0
    crash_at = 1.0
    start_ts = 0.0
    round_id = 0
    history: list = []

    def calc_mult(self, elapsed: float) -> float:
        slow = elapsed * 0.06
        fast = math.exp(elapsed * 0.10) - 1
        return round(1.0 + slow + fast, 2)

g = G()

def gen_crash() -> float:
    r = random.random()
    if r < 0.05: return 1.00
    return round(min(0.95 / (1 - r), 500), 2)

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
            "name":   p.get("name","?"),
            "nick":   p.get("nick",""),
            "photo":  p.get("photo",""),
            "bet":    bet["amount"],
            "cashed": bet.get("cashed",False),
            "win":    bet.get("win"),
            "mult":   bet.get("mult"),
            "lost":   bet.get("lost",False),
            "nft":    bet.get("nft"),
        })
    return rows

# ── Game loop ─────────────────────────────────────────────────────────────────
async def game_loop():
    while True:
        g.phase    = "waiting"
        g.mult     = 1.0
        g.crash_at = gen_crash()
        g.round_id += 1
        bets.clear()

        for cd in range(5, 0, -1):
            await broadcast({"t":"cd","sec":cd,"rid":g.round_id,"ca":g.crash_at,"now":time.time()})
            await asyncio.sleep(1)

        g.phase    = "flying"
        g.start_ts = time.time()
        await broadcast({"t":"st","ts":g.start_ts,"ca":g.crash_at,"rid":g.round_id,"now":time.time()})

        while True:
            elapsed = time.time() - g.start_ts
            g.mult  = g.calc_mult(elapsed)

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

            # Надсилаємо tick з NFT прев'ю для кожного гравця
            tick_msg = {"t":"tick","m":g.mult,"pl":players_list(),"now":time.time()}
            await broadcast(tick_msg)

            # Персональний NFT прев'ю
            for uid, bet in list(bets.items()):
                if not bet.get("cashed") and not bet.get("lost") and uid in clients:
                    nft = get_nft_preview(bet["amount"], g.mult)
                    if nft:
                        try:
                            await clients[uid].send_text(json.dumps({
                                "t": "nft_preview",
                                "nft": nft,
                                "potential_win": round(bet["amount"] * g.mult, 3),
                            }))
                        except:
                            pass
            await asyncio.sleep(0.15)

        # CRASHED
        g.phase = "crashed"
        g.history.insert(0, g.crash_at)
        g.history = g.history[:20]
        for uid, bet in bets.items():
            if not bet.get("cashed"):
                bet["lost"] = True
        await broadcast({"t":"cr","ca":g.crash_at,"rid":g.round_id,"h":g.history,"pl":players_list(),"now":time.time()})
        await asyncio.sleep(3)

async def do_cashout(uid: int, mult: float):
    bet = bets.get(uid)
    if not bet or bet.get("cashed"):
        return
    win = round(bet["amount"] * mult, 4)
    bet["cashed"] = True
    bet["win"]    = win
    bet["mult"]   = mult

    # Підбираємо NFT за виграшем
    nft = get_nft_for_win(win)
    bet["nft"] = nft

    if uid in players:
        if nft:
            # Виграш йде на NFT — не грошима
            if "nfts" not in players[uid]:
                players[uid]["nfts"] = []
            players[uid]["nfts"].append({**nft, "won_at": mult, "win_ton": win})
        else:
            # Виграш < 2.8 TON — повертаємо TON
            players[uid]["balance"] = round(players[uid]["balance"] + win, 4)

    await broadcast({"t":"co","uid":uid,"win":win,"mx":mult,"pl":players_list(),"now":time.time()})

    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":   "your_co",
                "win":  win,
                "mx":   mult,
                "bal":  players.get(uid,{}).get("balance",0),
                "nft":  nft,
            }))
        except:
            pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(game_loop())

# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/{uid}")
async def ws_endpoint(websocket: WebSocket, uid: int):
    await websocket.accept()
    clients[uid] = websocket
    await websocket.send_text(json.dumps({
        "t":"init","phase":g.phase,"mult":g.mult,"ts":g.start_ts,
        "ca":g.crash_at,"rid":g.round_id,"h":g.history,
        "pl":players_list(),"bal":players.get(uid,{}).get("balance",1.0),
        "nfts":players.get(uid,{}).get("nfts",[]),
        "now":time.time(),
    }))
    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)
            a = data.get("a")
            if a == "auth":
                players[uid] = {
                    "name":    data.get("name","Player"),
                    "nick":    data.get("nick",""),
                    "photo":   data.get("photo",""),
                    "balance": players.get(uid,{}).get("balance",1.0),
                    "nfts":    players.get(uid,{}).get("nfts",[]),
                }
            elif a == "bet":
                if g.phase != "waiting": continue
                amount = float(data.get("amt",0))
                bal    = players.get(uid,{}).get("balance",0)
                if amount < 0.1 or amount > bal:
                    await websocket.send_text(json.dumps({"t":"err","msg":"Недостатньо TON"}))
                    continue
                players[uid]["balance"] = round(bal - amount, 4)
                bets[uid] = {"amount":amount,"auto_cashout":data.get("ac"),"cashed":False,"lost":False}
                await websocket.send_text(json.dumps({"t":"bet_ok","amt":amount,"bal":players[uid]["balance"]}))
                await broadcast({"t":"newbet","pl":players_list(),"now":time.time()})
            elif a == "cashout":
                if g.phase == "flying" and uid in bets:
                    await do_cashout(uid, g.mult)
    except WebSocketDisconnect:
        clients.pop(uid, None)

@app.post("/topup/{uid}/{amount}")
async def topup(uid: int, amount: float):
    if uid not in players:
        players[uid] = {"name":"Player","nick":"","photo":"","balance":0,"nfts":[]}
    players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({"t":"topup","credited":amount,"bal":players[uid]["balance"]}))
        except:
            pass
    return {"ok":True,"balance":players[uid]["balance"]}

@app.get("/")
async def root():
    return {"status":"ok","round":g.round_id,"phase":g.phase,"players":len(clients)}
