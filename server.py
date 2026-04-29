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
BOT_TOKEN     = os.getenv("BOT_TOKEN", "7509877748:AAHkFoiLYbCZ0LQxHHlsFVS0KMUQR2d0OoA")

# Кеш фото подарунків
gift_photo_cache: dict = {}

async def load_gift_photos():
    global gift_photo_cache
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getAvailableGifts")
            data = r.json()
            if not data.get("ok"):
                print(f"Gifts API error: {data}")
                return
            for gift in data["result"]["gifts"]:
                star_count = gift.get("star_count", 0)
                sticker    = gift.get("sticker", {})
                thumb      = sticker.get("thumbnail") or {}
                file_id    = thumb.get("file_id") or sticker.get("file_id","")
                if not file_id: continue
                r2 = await client.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                    params={"file_id": file_id}
                )
                d2 = r2.json()
                if d2.get("ok"):
                    path = d2["result"]["file_path"]
                    url  = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{path}"
                    gift_photo_cache[star_count] = url
            print(f"✅ Loaded {len(gift_photo_cache)} gift photos")
    except Exception as e:
        print(f"load_gift_photos error: {e}")

def get_gift_photo(floor_ton: float) -> str:
    if not gift_photo_cache: return ""
    target = int(floor_ton * 50)  # 1 TON ≈ 50 stars
    closest = min(gift_photo_cache.keys(), key=lambda s: abs(s-target))
    return gift_photo_cache.get(closest, "")

# ── NFT Каталог — реальні Telegram Gifts з Fragment ──────────────────────────
NFT_CATALOG = [
    {"id":"chillflame","name":"Chill Flame","floor":2.59,"price":2.72,"rarity":"Common","color":"#0d2e1a"},
    {"id":"xmasstocking","name":"Xmas Stocking","floor":2.6,"price":2.73,"rarity":"Common","color":"#0d2e1a"},
    {"id":"vicecream","name":"Vice Cream","floor":2.6,"price":2.73,"rarity":"Common","color":"#0d2e1a"},
    {"id":"snakebox","name":"Snake Box","floor":2.64,"price":2.77,"rarity":"Common","color":"#0d2e1a"},
    {"id":"candycane","name":"Candy Cane","floor":2.65,"price":2.78,"rarity":"Common","color":"#0d2e1a"},
    {"id":"lunarsnake","name":"Lunar Snake","floor":2.74,"price":2.88,"rarity":"Common","color":"#0d2e1a"},
    {"id":"holidaydrink","name":"Holiday Drink","floor":2.82,"price":2.96,"rarity":"Common","color":"#0d2e1a"},
    {"id":"whipcupcake","name":"Whip Cupcake","floor":2.85,"price":2.99,"rarity":"Common","color":"#0d2e1a"},
    {"id":"winterwreath","name":"Winter Wreath","floor":2.85,"price":2.99,"rarity":"Common","color":"#0d2e1a"},
    {"id":"bigyear","name":"Big Year","floor":2.87,"price":3.01,"rarity":"Common","color":"#0d2e1a"},
    {"id":"poolfloat","name":"Pool Float","floor":2.96,"price":3.11,"rarity":"Common","color":"#0d2e1a"},
    {"id":"jesterhat","name":"Jester Hat","floor":3.09,"price":3.24,"rarity":"Common","color":"#0d2e1a"},
    {"id":"petsnake","name":"Pet Snake","floor":3.11,"price":3.27,"rarity":"Common","color":"#0d2e1a"},
    {"id":"partysparkler","name":"Party Sparkler","floor":3.16,"price":3.32,"rarity":"Common","color":"#0d2e1a"},
    {"id":"hypnolollipop","name":"Hypno Lollipop","floor":3.18,"price":3.34,"rarity":"Common","color":"#0d2e1a"},
    {"id":"tamagadget","name":"Tama Gadget","floor":3.23,"price":3.39,"rarity":"Common","color":"#0d2e1a"},
    {"id":"freshsocks","name":"Fresh Socks","floor":3.26,"price":3.42,"rarity":"Common","color":"#0d2e1a"},
    {"id":"jackinthebox","name":"Jack-in-the-Box","floor":3.36,"price":3.53,"rarity":"Common","color":"#0d2e1a"},
    {"id":"easteregg","name":"Easter Egg","floor":3.41,"price":3.58,"rarity":"Common","color":"#0d2e1a"},
    {"id":"spicedwine","name":"Spiced Wine","floor":3.47,"price":3.64,"rarity":"Common","color":"#0d2e1a"},
    {"id":"happybrownie","name":"Happy Brownie","floor":3.49,"price":3.66,"rarity":"Common","color":"#0d2e1a"},
    {"id":"lolpop","name":"Lol Pop","floor":3.61,"price":3.79,"rarity":"Common","color":"#0d2e1a"},
    {"id":"stellarrocket","name":"Stellar Rocket","floor":3.63,"price":3.81,"rarity":"Common","color":"#0d2e1a"},
    {"id":"moodpack","name":"Mood Pack","floor":3.67,"price":3.85,"rarity":"Common","color":"#0d2e1a"},
    {"id":"starnotepad","name":"Star Notepad","floor":3.71,"price":3.9,"rarity":"Common","color":"#0d2e1a"},
    {"id":"gingercookie","name":"Ginger Cookie","floor":3.73,"price":3.92,"rarity":"Common","color":"#0d2e1a"},
    {"id":"cookieheart","name":"Cookie Heart","floor":3.84,"price":4.03,"rarity":"Common","color":"#0d2e1a"},
    {"id":"snowglobe","name":"Snow Globe","floor":3.83,"price":4.02,"rarity":"Common","color":"#0d2e1a"},
    {"id":"hexhot","name":"Hex Pot","floor":3.87,"price":4.06,"rarity":"Common","color":"#0d2e1a"},
    {"id":"bdaycandle","name":"B-Day Candle","floor":4.08,"price":4.28,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"bowtie","name":"Bow Tie","floor":4.27,"price":4.48,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"clovelpin","name":"Clover Pin","floor":4.07,"price":4.27,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"faithamulet","name":"Faith Amulet","floor":4.23,"price":4.44,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"snowmittens","name":"Snow Mittens","floor":4.29,"price":4.5,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"moonpendant","name":"Moon Pendant","floor":4.36,"price":4.58,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"lushbouquet","name":"Lush Bouquet","floor":4.47,"price":4.69,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"inputkey","name":"Input Key","floor":4.75,"price":4.99,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"timelessbook","name":"Timeless Book","floor":4.03,"price":4.23,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"spyagaric","name":"Spy Agaric","floor":4.56,"price":4.79,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"snoopdog","name":"Snoop Dogg","floor":4.71,"price":4.95,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"joyfulbundle","name":"Joyful Bundle","floor":5.61,"price":5.89,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"lightsword","name":"Light Sword","floor":5.04,"price":5.29,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"eternalcandle","name":"Eternal Candle","floor":5.39,"price":5.66,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"deskcalendar","name":"Desk Calendar","floor":5.48,"price":5.75,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"jollychimp","name":"Jolly Chimp","floor":5.88,"price":6.17,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"swagbag","name":"Swag Bag","floor":5.86,"price":6.15,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"evileye","name":"Evil Eye","floor":5.97,"price":6.27,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"sleighbell","name":"Sleigh Bell","floor":6.7,"price":7.04,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"berrybox","name":"Berry Box","floor":6.8,"price":7.14,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"hangingstar","name":"Hanging Star","floor":7.14,"price":7.5,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"jinglebells","name":"Jingle Bells","floor":7.4,"price":7.77,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"valentinebox","name":"Valentine Box","floor":8.22,"price":8.63,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"lovecandle","name":"Love Candle","floor":8.42,"price":8.84,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"crystalball","name":"Crystal Ball","floor":9.74,"price":10.23,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"skullflower","name":"Skull Flower","floor":9.75,"price":10.24,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"flyingbroom","name":"Flying Broom","floor":10.16,"price":10.67,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"tophat","name":"Top Hat","floor":10.59,"price":11.12,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"sakuraflower","name":"Sakura Flower","floor":10.81,"price":11.35,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"madpumpkin","name":"Mad Pumpkin","floor":10.89,"price":11.43,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"lovepotion","name":"Love Potion","floor":11.85,"price":12.44,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"snoopcigar","name":"Snoop Cigar","floor":12.08,"price":12.68,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"trappedheart","name":"Trapped Heart","floor":12.91,"price":13.56,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"skystiletto","name":"Sky Stilettos","floor":13.28,"price":13.94,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"ionicdrier","name":"Ionic Dryer","floor":13.53,"price":14.21,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"recordplayer","name":"Record Player","floor":14.24,"price":14.95,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"cupidcharm","name":"Cupid Charm","floor":17.41,"price":18.28,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"eternalrose","name":"Eternal Rose","floor":21.86,"price":22.95,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"electricskull","name":"Electric Skull","floor":24.69,"price":25.92,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"diamondring","name":"Diamond Ring","floor":25.28,"price":26.54,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"voodoodoll","name":"Voodoo Doll","floor":29.27,"price":30.73,"rarity":"Epic","color":"#1e0d3a"},
    {"id":"toybear","name":"Toy Bear","floor":30.1,"price":31.61,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"nekohelmet","name":"Neko Helmet","floor":31.59,"price":33.17,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"lowrider","name":"Low Rider","floor":39.89,"price":41.88,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"genielamp","name":"Genie Lamp","floor":40.7,"price":42.74,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"swisswatch","name":"Swiss Watch","floor":43.13,"price":45.29,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"kissedfrong","name":"Kissed Frog","floor":48.89,"price":51.33,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"magicpotion","name":"Magic Potion","floor":61.44,"price":64.51,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"gemsignet","name":"Gem Signet","floor":55.87,"price":58.66,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"artisanbrick","name":"Artisan Brick","floor":68.34,"price":71.76,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"ionicgem","name":"Ion Gem","floor":69.82,"price":73.31,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"perfumebottle","name":"Perfume Bottle","floor":70.86,"price":74.4,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"westsideside","name":"Westside Sign","floor":70.94,"price":74.49,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"minioscars","name":"Mini Oscar","floor":72.22,"price":75.83,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"heroichelmet","name":"Heroic Helmet","floor":200.58,"price":210.61,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"astralshards","name":"Astral Shard","floor":151.69,"price":159.27,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"durovscap","name":"Durov's Cap","floor":576.88,"price":605.72,"rarity":"Legendary","color":"#2e1e00"},
]

def get_nft_for_win(win_ton: float):
    if win_ton < 2.72:
        return None
    candidates = [n for n in NFT_CATALOG if round(n["floor"]*1.05, 2) <= win_ton]
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
    nft = get_nft_for_win(win)
    if nft:
        # Додаємо реальне фото з Telegram API
        nft = {**nft, "photo": get_gift_photo(nft["floor"])}
    bet["nft"] = nft
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
    asyncio.create_task(load_gift_photos())

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
@app.get("/lottie/{gift_name}")
async def proxy_lottie(gift_name: str):
    """Проксуємо Lottie файли з nft.fragment.com щоб обійти CORS"""
    from fastapi.responses import Response
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://nft.fragment.com/gift/{gift_name}.lottie.json",
                headers={"Referer": "https://fragment.com/"}
            )
            if r.status_code == 200:
                return Response(
                    content=r.content,
                    media_type="application/json",
                    headers={"Access-Control-Allow-Origin": "*"}
                )
    except Exception as e:
        print(f"Lottie proxy error: {e}")
    return Response(content=b"{}", media_type="application/json")

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
