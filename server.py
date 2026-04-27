import asyncio, json, math, os, random, time, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Конфіг ────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
TON_WALLET  = os.getenv("UQAfazCyjGjugOf73_LrxUuLvxSmExM_8loArhgATwKXU6yA", "")   # твій гаманець куди приходять TON
TONCENTER   = "https://toncenter.com/api/v2"

# ── NFT Каталог — реальні Telegram Gifts ─────────────────────────────────────
NFT_CATALOG = [
    {"id":"icecream",  "name":"Ice Cream",      "img":"https://nft.fragment.com/gift/icecream-1.webp",       "floor":2.8,  "rarity":"Common",    "emoji":"🍦", "stars":"340+"},
    {"id":"torch",     "name":"Torch",           "img":"https://nft.fragment.com/gift/torch-1.webp",          "floor":2.9,  "rarity":"Common",    "emoji":"🔦", "stars":"344+"},
    {"id":"flamingo",  "name":"Flamingo Ring",   "img":"https://nft.fragment.com/gift/flamingo-1.webp",       "floor":3.1,  "rarity":"Common",    "emoji":"🦩", "stars":"370+"},
    {"id":"noodles",   "name":"Spicy Noodles",   "img":"https://nft.fragment.com/gift/spicynoodles-1.webp",   "floor":3.2,  "rarity":"Common",    "emoji":"🍜", "stars":"377+"},
    {"id":"popsicle",  "name":"Popsicle",        "img":"https://nft.fragment.com/gift/popsicle-1.webp",       "floor":3.0,  "rarity":"Common",    "emoji":"🍫", "stars":"350+"},
    {"id":"lollipop",  "name":"Lollipop",        "img":"https://nft.fragment.com/gift/lollipop-1.webp",       "floor":2.5,  "rarity":"Common",    "emoji":"🍭", "stars":"300+"},
    {"id":"poop",      "name":"Poop",            "img":"https://nft.fragment.com/gift/poop-1.webp",           "floor":4.1,  "rarity":"Rare",      "emoji":"💩", "stars":"479+"},
    {"id":"seeds",     "name":"Pumpkin Seeds",   "img":"https://nft.fragment.com/gift/pumpkinseeds-1.webp",   "floor":4.8,  "rarity":"Rare",      "emoji":"🌰", "stars":"560+"},
    {"id":"clover",    "name":"Lucky Clover",    "img":"https://nft.fragment.com/gift/luckyclover-1.webp",    "floor":4.7,  "rarity":"Rare",      "emoji":"🍀", "stars":"554+"},
    {"id":"cupcake",   "name":"Cupcake",         "img":"https://nft.fragment.com/gift/cupcake-1.webp",        "floor":2.9,  "rarity":"Common",    "emoji":"🧁", "stars":"340+"},
    {"id":"cooldog",   "name":"Cool Dog",        "img":"https://nft.fragment.com/gift/cooldog-1.webp",        "floor":5.1,  "rarity":"Rare",      "emoji":"🐶", "stars":"600+"},
    {"id":"tgbag",     "name":"Telegram Bag",    "img":"https://nft.fragment.com/gift/telegrambag-1.webp",    "floor":4.3,  "rarity":"Rare",      "emoji":"👜", "stars":"500+"},
    {"id":"diamond",   "name":"Diamond Ring",    "img":"https://nft.fragment.com/gift/diamondring-1.webp",    "floor":15.0, "rarity":"Epic",      "emoji":"💍", "stars":"1800+"},
    {"id":"trophy",    "name":"Trophy",          "img":"https://nft.fragment.com/gift/trophy-1.webp",         "floor":25.0, "rarity":"Epic",      "emoji":"🏆", "stars":"3000+"},
    {"id":"rocket",    "name":"Rocket",          "img":"https://nft.fragment.com/gift/rocket-1.webp",         "floor":50.0, "rarity":"Legendary", "emoji":"🚀", "stars":"6000+"},
    {"id":"crown",     "name":"Golden Crown",    "img":"https://nft.fragment.com/gift/goldencrown-1.webp",    "floor":100.0,"rarity":"Legendary", "emoji":"👑", "stars":"12000+"},
]

def get_nft_for_win(win_ton: float):
    if win_ton < 2.8:
        return None
    candidates = [n for n in NFT_CATALOG if n["floor"] <= win_ton]
    if not candidates:
        return NFT_CATALOG[0]
    return max(candidates, key=lambda n: n["floor"])

def get_nft_preview(bet_ton: float, mult: float):
    return get_nft_for_win(bet_ton * mult)

# ── Перевірка TON транзакції ──────────────────────────────────────────────────
pending_topups: dict = {}  # uid -> {amount, ts, checked}

async def check_ton_tx(uid: int, amount: float, since_ts: float) -> bool:
    """Перевіряємо чи прийшла транзакція на наш гаманець"""
    if not TON_WALLET:
        print(f"❌ TON_WALLET не вказано!")
        return False
    try:
        # Використовуємо tonapi.io — не потребує API ключа
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://tonapi.io/v2/accounts/{TON_WALLET}/events",
                params={"limit": 20, "subject_only": "true"},
                headers={"Accept": "application/json"}
            )
            print(f"TON API status: {r.status_code}")
            if r.status_code != 200:
                print(f"TON API error: {r.text[:200]}")
                return False

            data = r.json()
            events = data.get("events", [])
            print(f"Got {len(events)} events, looking for {amount} TON since {since_ts}")

            nanos = int(amount * 1e9)

            for event in events:
                event_ts = event.get("timestamp", 0)
                if event_ts < since_ts - 120:
                    print(f"Event too old: {event_ts} < {since_ts}")
                    break

                for action in event.get("actions", []):
                    if action.get("type") != "TonTransfer":
                        continue
                    details = action.get("TonTransfer", {})
                    recipient = details.get("recipient", {}).get("address", "")
                    tx_amount = details.get("amount", 0)
                    print(f"TX: {tx_amount} nanos to {recipient[:20]}, need {nanos}")

                    # Порівнюємо адресу і суму (±0.05 TON на комісію)
                    if abs(tx_amount - nanos) < 50_000_000:
                        print(f"✅ Found matching TX for uid {uid}!")
                        return True

    except Exception as e:
        print(f"TON check error: {e}")
    return False

async def auto_check_topups():
    """Фонова задача — перевіряємо транзакції кожні 10с"""
    while True:
        await asyncio.sleep(10)
        now = time.time()
        for uid, info in list(pending_topups.items()):
            if info.get("done"):
                pending_topups.pop(uid, None)
                continue
            if now - info["ts"] > 900:  # таймаут 15 хвилин
                pending_topups.pop(uid, None)
                print(f"⏱ Topup timeout for uid {uid}")
                continue
            print(f"🔍 Checking TON tx for uid {uid}, amount {info['amount']}")
            found = await check_ton_tx(uid, info["amount"], info["ts"])
            if found:
                info["done"] = True
                amount = info["amount"]
                if uid not in players:
                    players[uid] = {"name":"Player","nick":"","photo":"","balance":0,"nfts":[]}
                players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)
                if uid in clients:
                    try:
                        await clients[uid].send_text(json.dumps({
                            "t": "topup",
                            "credited": amount,
                            "bal": players[uid]["balance"],
                        }))
                    except:
                        pass
                print(f"✅ Credited {amount} TON to uid {uid}, balance: {players[uid]['balance']}")

# ── Стан гри ──────────────────────────────────────────────────────────────────
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
        return round(1.0 + t*0.06 + math.exp(t*0.10) - 1, 2)

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
        "uid": uid, "name": players.get(uid,{}).get("name","?"),
        "nick": players.get(uid,{}).get("nick",""),
        "photo": players.get(uid,{}).get("photo",""),
        "bet": b["amount"], "cashed": b.get("cashed",False),
        "win": b.get("win"), "mult": b.get("mult"),
        "lost": b.get("lost",False), "nft": b.get("nft"),
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
                g.mult = g.crash_at; break
            for uid, bet in list(bets.items()):
                if bet.get("cashed") or bet.get("lost"): continue
                ac = bet.get("auto_cashout")
                if ac and g.mult >= ac:
                    await do_cashout(uid, g.mult)
            # Tick з NFT прев'ю
            await broadcast({"t":"tick","m":g.mult,"pl":players_list(),"now":time.time()})
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
            if a=="auth":
                players[uid] = {
                    "name":d.get("name","Player"),"nick":d.get("nick",""),
                    "photo":d.get("photo",""),
                    "balance":players.get(uid,{}).get("balance",1.0),
                    "nfts":players.get(uid,{}).get("nfts",[])
                }
            elif a=="bet":
                if g.phase!="waiting": continue
                amt = float(d.get("amt",0))
                bal = players.get(uid,{}).get("balance",0)
                if amt<0.1 or amt>bal:
                    await ws.send_text(json.dumps({"t":"err","msg":"Недостатньо TON"})); continue
                players[uid]["balance"] = round(bal-amt,4)
                bets[uid] = {"amount":amt,"auto_cashout":d.get("ac"),"cashed":False,"lost":False}
                await ws.send_text(json.dumps({"t":"bet_ok","amt":amt,"bal":players[uid]["balance"]}))
                await broadcast({"t":"newbet","pl":players_list(),"now":time.time()})
            elif a=="cashout":
                if g.phase=="flying" and uid in bets:
                    await do_cashout(uid, g.mult)
            elif a=="topup_start":
                # Гравець починає оплату — фіксуємо час і суму для перевірки
                amt = float(d.get("amount",0))
                if amt >= 0.1:
                    pending_topups[uid] = {"amount":amt,"ts":time.time(),"done":False}
                    await ws.send_text(json.dumps({"t":"topup_pending","amount":amt}))
    except WebSocketDisconnect:
        clients.pop(uid, None)

# ── REST ендпоінти ────────────────────────────────────────────────────────────
@app.post("/topup/{uid}/{amount}")
async def manual_topup(uid: int, amount: float):
    if uid not in players:
        players[uid] = {"name":"Player","nick":"","photo":"","balance":0,"nfts":[]}
    players[uid]["balance"] = round(players[uid]["balance"]+amount, 4)
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t":"topup","credited":amount,"bal":players[uid]["balance"]
            }))
        except: pass
    return {"ok":True,"balance":players[uid]["balance"]}

@app.get("/")
async def root():
    return {"status":"ok","round":g.round_id,"phase":g.phase,"players":len(clients)}
