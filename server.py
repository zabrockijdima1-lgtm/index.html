import asyncio, json, math, os, random, time, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ════════════════════════════════════════════════════════
# НАЛАШТУВАННЯ — вставити свої дані
# ════════════════════════════════════════════════════════
TON_WALLET    = "UQAfazCyjGjugOf73_LrxUuLvxSmExM_8loArhgATwKXU6yA"
TONCENTER_KEY = "062f53efeb759f033896aab86a1f423f4102443694799e2dd34e8c14e7f4e9f0"

# ── NFT Каталог — реальні Telegram Gifts з Fragment ──────────────────────────
NFT_CATALOG = [
    {"id":"lollipop",  "name":"Lollipop",       "img":"https://nft.fragment.com/gift/lollipop-1.webp",       "floor":3.0,  "rarity":"Common",    "emoji":"🍭", "stars":"300+"},
    {"id":"icecream",  "name":"Ice Cream",       "img":"https://nft.fragment.com/gift/icecream-1.webp",       "floor":2.8,  "rarity":"Common",    "emoji":"🍦", "stars":"340+"},
    {"id":"cupcake",   "name":"Cupcake",         "img":"https://nft.fragment.com/gift/cupcake-1.webp",        "floor":2.9,  "rarity":"Common",    "emoji":"🧁", "stars":"340+"},
    {"id":"torch",     "name":"Torch",           "img":"https://nft.fragment.com/gift/torch-1.webp",          "floor":2.9,  "rarity":"Common",    "emoji":"🔦", "stars":"344+"},
    {"id":"popsicle",  "name":"Popsicle",        "img":"https://nft.fragment.com/gift/popsicle-1.webp",       "floor":2.8,  "rarity":"Common",    "emoji":"🍫", "stars":"350+"},
    {"id":"flamingo",  "name":"Flamingo Ring",   "img":"https://nft.fragment.com/gift/flamingo-1.webp",       "floor":3.0,  "rarity":"Common",    "emoji":"🦩", "stars":"370+"},
    {"id":"noodles",   "name":"Spicy Noodles",   "img":"https://nft.fragment.com/gift/spicynoodles-1.webp",   "floor":3.05, "rarity":"Common",    "emoji":"🍜", "stars":"377+"},
    {"id":"poop",      "name":"Poop",            "img":"https://nft.fragment.com/gift/poop-1.webp",           "floor":3.33, "rarity":"Rare",      "emoji":"💩", "stars":"479+"},
    {"id":"tgbag",     "name":"Telegram Bag",    "img":"https://nft.fragment.com/gift/telegrambag-1.webp",    "floor":3.5,  "rarity":"Rare",      "emoji":"👜", "stars":"500+"},
    {"id":"clover",    "name":"Lucky Clover",    "img":"https://nft.fragment.com/gift/luckyclover-1.webp",    "floor":4.7,  "rarity":"Rare",      "emoji":"🍀", "stars":"554+"},
    {"id":"seeds",     "name":"Pumpkin Seeds",   "img":"https://nft.fragment.com/gift/pumpkinseeds-1.webp",   "floor":4.8,  "rarity":"Rare",      "emoji":"🌰", "stars":"560+"},
    {"id":"cooldog",   "name":"Cool Dog",        "img":"https://nft.fragment.com/gift/cooldog-1.webp",        "floor":3.8,  "rarity":"Rare",      "emoji":"🐶", "stars":"600+"},
    {"id":"diamond",   "name":"Diamond Ring",    "img":"https://nft.fragment.com/gift/diamondring-1.webp",    "floor":15.0, "rarity":"Epic",      "emoji":"💍", "stars":"1800+"},
    {"id":"trophy",    "name":"Trophy",          "img":"https://nft.fragment.com/gift/trophy-1.webp",         "floor":25.0, "rarity":"Epic",      "emoji":"🏆", "stars":"3000+"},
    {"id":"rocket",    "name":"Rocket",          "img":"https://nft.fragment.com/gift/rocket-1.webp",         "floor":50.0, "rarity":"Legendary", "emoji":"🚀", "stars":"6000+"},
    {"id":"crown",     "name":"Golden Crown",    "img":"https://nft.fragment.com/gift/goldencrown-1.webp",    "floor":100.0,"rarity":"Legendary", "emoji":"👑", "stars":"12000+"},
]

def get_nft_for_win(win_ton: float):
    if win_ton < 2.5:
        return None
    candidates = [n for n in NFT_CATALOG if n["floor"] <= win_ton]
    if not candidates:
        return NFT_CATALOG[0]
    return max(candidates, key=lambda n: n["floor"])

def get_nft_preview(bet_ton: float, mult: float):
    return get_nft_for_win(bet_ton * mult)

# ── Перевірка TON транзакцій ──────────────────────────────────────────────────
pending_topups: dict = {}  # uid -> {amount, ts, done}

async def check_ton_tx(uid: int, amount: float, since_ts: float) -> bool:
    try:
        params = {"address": TON_WALLET, "limit": 20}
        if TONCENTER_KEY:
            params["api_key"] = TONCENTER_KEY

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://toncenter.com/api/v2/getTransactions",
                params=params
            )
            data = r.json()
            print(f"TonCenter response: ok={data.get('ok')}, txs={len(data.get('result',[]))}")

            if not data.get("ok"):
                print(f"TonCenter error: {data}")
                return False

            nanos = int(amount * 1e9)
            for tx in data.get("result", []):
                tx_time = tx.get("utime", 0)
                if tx_time < since_ts - 180:
                    break
                val = int(tx.get("in_msg", {}).get("value", 0))
                print(f"TX: {val} nanos at {tx_time}, need {nanos} since {since_ts}")
                if abs(val - nanos) < 50_000_000:
                    print(f"✅ Match found for uid {uid}!")
                    return True
    except Exception as e:
        print(f"check_ton_tx error: {e}")
    return False

async def auto_check_topups():
    while True:
        await asyncio.sleep(10)
        for uid, info in list(pending_topups.items()):
            if info.get("done"):
                pending_topups.pop(uid, None)
                continue
            if time.time() - info["ts"] > 900:
                pending_topups.pop(uid, None)
                continue
            print(f"🔍 Checking {info['amount']} TON for uid {uid}")
            found = await check_ton_tx(uid, info["amount"], info["ts"])
            if found:
                info["done"] = True
                amt = info["amount"]
                if uid not in players:
                    players[uid] = {"name":"?","nick":"","photo":"","balance":0,"nfts":[]}
                players[uid]["balance"] = round(players[uid]["balance"] + amt, 4)
                if uid in clients:
                    try:
                        await clients[uid].send_text(json.dumps({
                            "t":"topup","credited":amt,"bal":players[uid]["balance"]
                        }))
                    except: pass
                print(f"✅ Credited {amt} TON to {uid}, balance={players[uid]['balance']}")

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
    def calc_mult(self, t):
        # Та сама формула що і на клієнті
        return round(math.exp(t * 0.07), 2)

g = G()

def gen_crash():
    r = random.random()
    if r < 0.05: return 1.00
    return round(min(0.95/(1-r), 500), 2)

async def broadcast(msg):
    data = json.dumps(msg)
    dead = []
    for uid, ws in list(clients.items()):
        try: await ws.send_text(data)
        except: dead.append(uid)
    for uid in dead: clients.pop(uid, None)

def players_list():
    return [{
        "uid": uid,
        "name": players.get(uid,{}).get("name","?"),
        "nick": players.get(uid,{}).get("nick",""),
        "photo": players.get(uid,{}).get("photo",""),
        "bet": b["amount"],
        "cashed": b.get("cashed",False),
        "win": b.get("win"),
        "mult": b.get("mult"),
        "lost": b.get("lost",False),
        "nft": b.get("nft"),
    } for uid, b in bets.items()]

# ── Game loop ─────────────────────────────────────────────────────────────────
async def game_loop():
    while True:
        g.phase = "waiting"; g.mult = 1.0
        g.crash_at = gen_crash(); g.round_id += 1
        bets.clear()

        for cd in range(5, 0, -1):
            await broadcast({"t":"cd","sec":cd,"rid":g.round_id,"ca":g.crash_at,"now":time.time()})
            await asyncio.sleep(1)

        g.phase = "flying"; g.start_ts = time.time()
        await broadcast({"t":"st","ts":g.start_ts,"ca":g.crash_at,"rid":g.round_id,"now":time.time()})

        while True:
            el = time.time() - g.start_ts
            g.mult = g.calc_mult(el)
            if g.mult >= g.crash_at:
                g.mult = g.crash_at
                break
            for uid, bet in list(bets.items()):
                if bet.get("cashed") or bet.get("lost"): continue
                ac = bet.get("auto_cashout")
                if ac and g.mult >= ac:
                    await do_cashout(uid, g.mult)
            await broadcast({"t":"tick","m":g.mult,"pl":players_list(),"now":time.time()})
            # NFT прев'ю
            for uid, bet in list(bets.items()):
                if not bet.get("cashed") and not bet.get("lost") and uid in clients:
                    nft = get_nft_preview(bet["amount"], g.mult)
                    if nft:
                        try:
                            await clients[uid].send_text(json.dumps({
                                "t":"nft_preview","nft":nft,
                                "potential_win":round(bet["amount"]*g.mult,3)
                            }))
                        except: pass
            await asyncio.sleep(0.15)

        g.phase = "crashed"
        g.history.insert(0, g.crash_at); g.history = g.history[:20]
        for uid, bet in bets.items():
            if not bet.get("cashed"): bet["lost"] = True
        await broadcast({"t":"cr","ca":g.crash_at,"rid":g.round_id,"h":g.history,"pl":players_list(),"now":time.time()})
        await asyncio.sleep(3)

async def do_cashout(uid, mult):
    bet = bets.get(uid)
    if not bet or bet.get("cashed"): return
    win = round(bet["amount"] * mult, 4)
    bet["cashed"] = True; bet["win"] = win; bet["mult"] = mult
    nft = get_nft_for_win(win); bet["nft"] = nft
    if uid in players:
        if nft:
            players[uid].setdefault("nfts",[]).append({**nft,"won_at":mult,"win_ton":win})
        else:
            players[uid]["balance"] = round(players[uid]["balance"]+win, 4)
    await broadcast({"t":"co","uid":uid,"win":win,"mx":mult,"pl":players_list(),"now":time.time()})
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":"your_co","win":win,"mx":mult,
                "bal":players.get(uid,{}).get("balance",0),"nft":nft
            }))
        except: pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(game_loop())
    asyncio.create_task(auto_check_topups())

# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/{uid}")
async def ws_ep(ws: WebSocket, uid: int):
    await ws.accept(); clients[uid] = ws
    await ws.send_text(json.dumps({
        "t":"init","phase":g.phase,"mult":g.mult,"ts":g.start_ts,
        "ca":g.crash_at,"rid":g.round_id,"h":g.history,
        "pl":players_list(),"bal":players.get(uid,{}).get("balance",1.0),
        "nfts":players.get(uid,{}).get("nfts",[]),"now":time.time()
    }))
    try:
        while True:
            d = json.loads(await ws.receive_text())
            a = d.get("a")
            if a == "auth":
                if uid not in players:
                    players[uid] = {"name":d.get("name","Player"),"nick":d.get("nick",""),"photo":d.get("photo",""),"balance":1.0,"nfts":[]}
                else:
                    players[uid]["name"]  = d.get("name", players[uid]["name"])
                    players[uid]["nick"]  = d.get("nick", players[uid]["nick"])
                    players[uid]["photo"] = d.get("photo", players[uid]["photo"])
            elif a == "bet":
                if g.phase != "waiting": continue
                amt = float(d.get("amt", 0))
                bal = players.get(uid, {}).get("balance", 0)
                if amt < 0.1 or amt > bal:
                    await ws.send_text(json.dumps({"t":"err","msg":"Недостатньо TON"}))
                    continue
                players[uid]["balance"] = round(bal - amt, 4)
                bets[uid] = {"amount":amt,"auto_cashout":d.get("ac"),"cashed":False,"lost":False}
                await ws.send_text(json.dumps({"t":"bet_ok","amt":amt,"bal":players[uid]["balance"]}))
                await broadcast({"t":"newbet","pl":players_list(),"now":time.time()})
            elif a == "cashout":
                if g.phase == "flying" and uid in bets:
                    await do_cashout(uid, g.mult)
            elif a == "topup_start":
                # Фіксуємо початок оплати для автоперевірки
                amt = float(d.get("amount", 0))
                if amt >= 0.1:
                    pending_topups[uid] = {"amount":amt,"ts":time.time(),"done":False}
                    await ws.send_text(json.dumps({"t":"topup_pending","amount":amt}))
                    print(f"📝 Topup started: uid={uid}, amount={amt}")
    except WebSocketDisconnect:
        clients.pop(uid, None)

# ── REST ──────────────────────────────────────────────────────────────────────
@app.get("/topup/{uid}/{amount}")
async def get_topup(uid: int, amount: float):
    """Ручне зарахування (для адміна)"""
    if uid not in players:
        players[uid] = {"name":"Player","nick":"","photo":"","balance":0,"nfts":[]}
    players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":"topup","credited":amount,"bal":players[uid]["balance"]
            }))
        except: pass
    return {"ok":True,"balance":players[uid]["balance"]}

@app.post("/topup/{uid}/{amount}")
async def post_topup(uid: int, amount: float):
    return await get_topup(uid, amount)

@app.get("/")
async def root():
    return {"status":"ok","round":g.round_id,"phase":g.phase,"players":len(clients),"pending_topups":len(pending_topups)}
