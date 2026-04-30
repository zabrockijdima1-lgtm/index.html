import asyncio, json, math, os, random, time, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Конфіг ────────────────────────────────────────────────────────────────────
TON_WALLET    = "UQAfazCyjGjugOf73_LrxUuLvxSmExM_8loArhgATwKXU6yA"
TONCENTER_KEY = "062f53efeb759f033896aab86a1f423f4102443694799e2dd34e8c14e7f4e9f0"
BOT_TOKEN     = os.getenv("BOT_TOKEN", "8757352545:AAGlu9yQu97JHfGljZH4ocqOBU_-sJm1KR8")
ADMIN_IDS     = {1256452126, 6479535975}
ADMIN_ID      = 1256452126

# Курс: скільки TON дають за 1 Stars
# 100 Stars ≈ 0.84 TON → 1 Star = 0.0084 TON
STARS_TO_TON  = 0.0084

# ── NFT Каталог ───────────────────────────────────────────────────────────────
NFT_CATALOG = [
    {"id":"chillflame","name":"Chill Flame","floor":2.59,"price":2.72,"rarity":"Common","color":"#0d2e1a"},
    {"id":"xmasstocking","name":"Xmas Stocking","floor":2.60,"price":2.73,"rarity":"Common","color":"#0d2e1a"},
    {"id":"vicecream","name":"Vice Cream","floor":2.60,"price":2.73,"rarity":"Common","color":"#0d2e1a"},
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
    {"id":"starnotepad","name":"Star Notepad","floor":3.71,"price":3.90,"rarity":"Common","color":"#0d2e1a"},
    {"id":"gingercookie","name":"Ginger Cookie","floor":3.73,"price":3.92,"rarity":"Common","color":"#0d2e1a"},
    {"id":"cookieheart","name":"Cookie Heart","floor":3.84,"price":4.03,"rarity":"Common","color":"#0d2e1a"},
    {"id":"snowglobe","name":"Snow Globe","floor":3.83,"price":4.02,"rarity":"Common","color":"#0d2e1a"},
    {"id":"hexhot","name":"Hex Pot","floor":3.87,"price":4.06,"rarity":"Common","color":"#0d2e1a"},
    {"id":"bdaycandle","name":"B-Day Candle","floor":4.08,"price":4.28,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"bowtie","name":"Bow Tie","floor":4.27,"price":4.48,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"clovelpin","name":"Clover Pin","floor":4.07,"price":4.27,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"faithamulet","name":"Faith Amulet","floor":4.23,"price":4.44,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"snowmittens","name":"Snow Mittens","floor":4.29,"price":4.50,"rarity":"Rare","color":"#0d1e3a"},
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
    {"id":"sleighbell","name":"Sleigh Bell","floor":6.70,"price":7.04,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"berrybox","name":"Berry Box","floor":6.80,"price":7.14,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"hangingstar","name":"Hanging Star","floor":7.14,"price":7.50,"rarity":"Rare","color":"#0d1e3a"},
    {"id":"jinglebells","name":"Jingle Bells","floor":7.40,"price":7.77,"rarity":"Rare","color":"#0d1e3a"},
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
    {"id":"toybear","name":"Toy Bear","floor":30.10,"price":31.61,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"nekohelmet","name":"Neko Helmet","floor":31.59,"price":33.17,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"lowrider","name":"Low Rider","floor":39.89,"price":41.88,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"genielamp","name":"Genie Lamp","floor":40.70,"price":42.74,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"swisswatch","name":"Swiss Watch","floor":43.13,"price":45.29,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"kissedfrong","name":"Kissed Frog","floor":48.89,"price":51.33,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"magicpotion","name":"Magic Potion","floor":61.44,"price":64.51,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"gemsignet","name":"Gem Signet","floor":55.87,"price":58.66,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"artisanbrick","name":"Artisan Brick","floor":68.34,"price":71.76,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"ionicgem","name":"Ion Gem","floor":69.82,"price":73.31,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"perfumebottle","name":"Perfume Bottle","floor":70.86,"price":74.40,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"westsideside","name":"Westside Sign","floor":70.94,"price":74.49,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"minioscars","name":"Mini Oscar","floor":72.22,"price":75.83,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"heroichelmet","name":"Heroic Helmet","floor":200.58,"price":210.61,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"astralshards","name":"Astral Shard","floor":151.69,"price":159.27,"rarity":"Legendary","color":"#2e1e00"},
    {"id":"durovscap","name":"Durov Cap","floor":576.88,"price":605.72,"rarity":"Legendary","color":"#2e1e00"},
]

def get_nft_for_win(win: float):
    if win < 2.72: return None
    ok = [n for n in NFT_CATALOG if n["price"] <= win]
    return max(ok, key=lambda n: n["floor"]) if ok else None

# ── Стан ─────────────────────────────────────────────────────────────────────
clients: dict = {}
players: dict = {}
bets:    dict = {}
referrals: dict = {}
ref_earnings: dict = {}
pending_topups: dict = {}

# ── Логи ─────────────────────────────────────────────────────────────────────
logs = {
    "bets": [],
    "cashouts": [],
    "deposits": [],
    "withdrawals": [],
    "referrals": [],
    "stars": [],       # {uid, name, stars, ton, ts}
}
MAX_LOGS = 500

def add_log(category, entry):
    entry["ts"] = time.time()
    logs[category].insert(0, entry)
    if len(logs[category]) > MAX_LOGS:
        logs[category].pop()

# ── Telegram ──────────────────────────────────────────────────────────────────
async def send_tg(uid: int, text: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": uid, "text": text, "parse_mode": "HTML"}
            )
    except Exception as e:
        print(f"TG send error: {e}")

# ── Зарахування балансу (спільна функція) ─────────────────────────────────────
async def credit_balance(uid: int, amount: float, source: str = "deposit"):
    """Зараховує amount TON на баланс гравця і нараховує реферальний бонус."""
    if uid not in players:
        players[uid] = {"name": "Player", "nick": "", "photo": "", "balance": 0, "nfts": []}
    players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)

    # Реферальний бонус
    if uid in referrals:
        ref_uid = referrals[uid]
        bonus = round(amount * 0.05, 4)
        if ref_uid not in players:
            players[ref_uid] = {"name": "?", "nick": "", "photo": "", "balance": 0, "nfts": []}
        players[ref_uid]["balance"] = round(players[ref_uid]["balance"] + bonus, 4)
        ref_earnings[ref_uid] = round(ref_earnings.get(ref_uid, 0) + bonus, 4)
        add_log("deposits", {"uid": ref_uid, "name": players[ref_uid].get("name", "?"), "amount": bonus, "note": f"ref bonus від {uid}"})
        if ref_uid in clients:
            try:
                await clients[ref_uid].send_text(json.dumps({"t": "ref_bonus", "bonus": bonus, "bal": players[ref_uid]["balance"]}))
            except:
                pass
        await send_tg(ref_uid, f"👥 <b>Реферальний бонус!</b>\nВаш реферал поповнив баланс на {amount} TON\nВаш бонус: <b>+{bonus} TON</b>")

    # Повідомлення гравцю по WS
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({
                "t": "topup_ok",
                "credited": amount,
                "bal": players[uid]["balance"],
                "source": source
            }))
        except:
            pass

    return players[uid]["balance"]

# ── Перевірка TON транзакцій ──────────────────────────────────────────────────
async def check_ton_tx(uid: int, amount: float, since_ts: float) -> bool:
    if not TON_WALLET: return False
    try:
        params = {"address": TON_WALLET, "limit": 20}
        if TONCENTER_KEY: params["api_key"] = TONCENTER_KEY
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://toncenter.com/api/v2/getTransactions", params=params)
            data = r.json()
            if not data.get("ok"): return False
            nanos = int(amount * 1e9)
            for tx in data.get("result", []):
                if tx.get("utime", 0) < since_ts - 180: break
                val = int(tx.get("in_msg", {}).get("value", 0))
                if abs(val - nanos) < 50_000_000: return True
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
            found = await check_ton_tx(uid, info["amount"], info["ts"])
            if found:
                info["done"] = True
                amt = info["amount"]
                bal = await credit_balance(uid, amt, source="ton")
                add_log("deposits", {"uid": uid, "name": players[uid].get("name", "?"), "amount": amt})
                await send_tg(ADMIN_ID, f"💰 <b>Депозит TON</b>\nКористувач: {players[uid].get('name','?')} (uid: {uid})\nСума: {amt} TON\nБаланс: {bal} TON")

# ── Stars: інвойс за вивід NFT (25 Stars) ────────────────────────────────────
NFT_WITHDRAW_STARS = 25  # комісія за вивід NFT зірками

@app.get("/stars/withdraw-invoice/{uid}/{nft_id}/{nft_name}")
async def create_withdraw_invoice(uid: int, nft_id: str, nft_name: str):
    payload = json.dumps({"uid": uid, "nft_id": nft_id, "type": "nft_withdraw"})
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink",
                json={
                    "title": f"NFT Withdrawal: {nft_name}",
                    "description": f"Fee for withdrawing NFT «{nft_name}» to your Telegram wallet",
                    "payload": payload,
                    "currency": "XTR",
                    "prices": [{"label": "Withdrawal fee", "amount": NFT_WITHDRAW_STARS}]
                }
            )
            data = r.json()
        if not data.get("ok"):
            print(f"createInvoiceLink error: {data}")
            return JSONResponse({"ok": False, "error": data.get("description", "Telegram error")})
        return JSONResponse({"ok": True, "invoice_link": data["result"]})
    except Exception as e:
        print(f"Withdraw invoice error: {e}")
        return JSONResponse({"ok": False, "error": "Server error"})

# ── Stars: створення інвойсу ──────────────────────────────────────────────────
@app.get("/stars/invoice/{uid}/{stars}")
async def create_stars_invoice(uid: int, stars: int):
    if stars < 10 or stars > 10000:
        return JSONResponse({"ok": False, "error": "Stars від 10 до 10 000"})
    ton_amount = round(stars * STARS_TO_TON, 4)
    payload = json.dumps({"uid": uid, "stars": stars, "ton": ton_amount})
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/createInvoiceLink",
                json={
                    "title": "Поповнення балансу ⭐",
                    "description": f"{stars} Telegram Stars → {ton_amount} TON на ігровий баланс",
                    "payload": payload,
                    "currency": "XTR",
                    "prices": [{"label": f"{stars} Stars", "amount": stars}]
                }
            )
            data = r.json()
        if not data.get("ok"):
            print(f"createInvoiceLink error: {data}")
            return JSONResponse({"ok": False, "error": data.get("description", "Помилка Telegram")})
        return JSONResponse({"ok": True, "invoice_link": data["result"], "ton": ton_amount})
    except Exception as e:
        print(f"Stars invoice error: {e}")
        return JSONResponse({"ok": False, "error": "Помилка сервера"})

# ── Stars: webhook від Telegram (successful_payment) ─────────────────────────
@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    try:
        update = await request.json()
    except:
        return JSONResponse({"ok": True})

    # pre_checkout_query — обов'язково підтвердити
    if "pre_checkout_query" in update:
        pcq_id = update["pre_checkout_query"]["id"]
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery",
                    json={"pre_checkout_query_id": pcq_id, "ok": True}
                )
        except Exception as e:
            print(f"answerPreCheckoutQuery error: {e}")
        return JSONResponse({"ok": True})

    # successful_payment
    msg = update.get("message", {})
    payment = msg.get("successful_payment")
    if payment and payment.get("currency") == "XTR":
        try:
            payload = json.loads(payment["invoice_payload"])
        except Exception as e:
            print(f"Stars payload parse error: {e}")
            return JSONResponse({"ok": True})

        pay_type = payload.get("type", "deposit")

        # ── Вивід NFT за Stars ────────────────────────────────────────────
        if pay_type == "nft_withdraw":
            uid = int(payload["uid"])
            nft_id = payload["nft_id"]
            p = players.get(uid)
            if p:
                nfts = p.get("nfts", [])
                found_nft = None
                new_nfts = []
                removed = False
                for n in nfts:
                    if n.get("id") == nft_id and not removed:
                        found_nft = n; removed = True
                    else:
                        new_nfts.append(n)
                if found_nft:
                    p["nfts"] = new_nfts
                    name = p.get("name", "?")
                    nick = p.get("nick", "")
                    nick_str = f"@{nick}" if nick else f"uid:{uid}"
                    add_log("withdrawals", {
                        "uid": uid, "name": name,
                        "nft_name": found_nft.get("name"),
                        "nft_floor": found_nft.get("floor"),
                        "sell_price": 0, "type": "withdraw_stars"
                    })
                    if uid in clients:
                        try:
                            await clients[uid].send_text(json.dumps({
                                "t": "nft_withdrawn",
                                "nft_id": nft_id,
                                "msg": f"✅ {found_nft.get('name')} успішно виведено!"
                            }))
                        except: pass
                    await send_tg(uid, f"✅ <b>NFT виведено!</b>\n{found_nft.get('name')} відправлено у ваш гаманець\nКомісія: {NFT_WITHDRAW_STARS} ⭐")
                    await send_tg(ADMIN_ID, f"🎁 <b>Вивід NFT (Stars)</b>\nКористувач: {name} ({nick_str})\nNFT: {found_nft.get('name')} (floor {found_nft.get('floor')} TON)\nКомісія: {NFT_WITHDRAW_STARS} ⭐")

        # ── Поповнення балансу Stars ──────────────────────────────────────
        else:
            try:
                uid = int(payload["uid"])
                stars = int(payload["stars"])
                ton_amount = float(payload["ton"])
            except Exception as e:
                print(f"Stars deposit payload error: {e}")
                return JSONResponse({"ok": True})

            bal = await credit_balance(uid, ton_amount, source="stars")
            add_log("stars", {
                "uid": uid,
                "name": players.get(uid, {}).get("name", "?"),
                "stars": stars,
                "ton": ton_amount
            })
            add_log("deposits", {
                "uid": uid,
                "name": players.get(uid, {}).get("name", "?"),
                "amount": ton_amount,
                "note": f"Stars x{stars}"
            })
            await send_tg(uid, f"⭐ <b>Stars зараховано!</b>\n{stars} Stars → <b>{ton_amount} TON</b> на ігровий баланс\nПоточний баланс: {bal} TON")
            await send_tg(ADMIN_ID, f"⭐ <b>Stars депозит</b>\nКористувач: {players.get(uid,{}).get('name','?')} (uid: {uid})\nStars: {stars} → {ton_amount} TON\nБаланс: {bal} TON")

    return JSONResponse({"ok": True})

# ── Встановити webhook ────────────────────────────────────────────────────────
@app.get("/set_webhook")
async def set_webhook(request: Request):
    """Виклич один раз: GET /set_webhook?url=https://твій-сервер.com"""
    webhook_url = request.query_params.get("url")
    if not webhook_url:
        return JSONResponse({"error": "передай ?url=https://твій-сервер.com"})
    full_url = webhook_url.rstrip("/") + "/tg/webhook"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                json={"url": full_url}
            )
        return r.json()
    except Exception as e:
        return JSONResponse({"error": str(e)})

# ── Стан гри ─────────────────────────────────────────────────────────────────
class G:
    phase    = "waiting"
    mult     = 1.0
    crash_at = 1.0
    start_ts = 0.0
    round_id = 0
    next_hook = random.randint(8, 25)
    history: list = []
    def calc_mult(self, t): return round(math.exp(t * 0.07), 2)

g = G()

def gen_crash():
    r = random.random()
    # Розподіл: природний але не жадібний
    if r < 0.08: return 1.00                                      #  8% — одразу краш
    if r < 0.22: return round(random.uniform(1.01, 1.5), 2)      # 14% — дуже низько
    if r < 0.40: return round(random.uniform(1.5,  2.5), 2)      # 18% — низько
    if r < 0.58: return round(random.uniform(2.5,  5.0), 2)      # 18% — середньо (2-5x)
    if r < 0.72: return round(random.uniform(5.0,  12.0), 2)     # 14% — добре (5-12x)
    if r < 0.83: return round(random.uniform(12.0, 25.0), 2)     # 11% — дуже добре
    if r < 0.91: return round(random.uniform(25.0, 50.0), 2)     #  8% — відмінно
    if r < 0.97: return round(random.uniform(50.0, 80.0), 2)     #  6% — велике
    return round(random.uniform(80.0, 100.0), 2)                  #  3% — максимум

def gen_crash_no_bets():
    # Коли ніхто не ставив — показуємо красивий великий краш щоб залучити
    return round(random.uniform(30.0, 100.0), 2)

async def broadcast(msg):
    data = json.dumps(msg)
    dead = []
    for uid, ws in list(clients.items()):
        try: await ws.send_text(data)
        except: dead.append(uid)
    for uid in dead: clients.pop(uid, None)

def players_list():
    return [
        {
            "uid": uid,
            "name": players.get(uid, {}).get("name", "?"),
            "nick": players.get(uid, {}).get("nick", ""),
            "photo": players.get(uid, {}).get("photo", ""),
            "bet": b["amount"],
            "cashed": b.get("cashed", False),
            "win": b.get("win"),
            "mult": b.get("mult"),
            "lost": b.get("lost", False),
            "nft": b.get("nft")
        }
        for uid, b in bets.items()
    ]

async def game_loop():
    while True:
        g.phase = "waiting"; g.mult = 1.0; g.round_id += 1
        bets.clear()
        if g.round_id % g.next_hook == 0 and len(bets) == 0:
            g.crash_at = gen_crash_no_bets()
            g.next_hook = random.randint(8, 25)
        else:
            g.crash_at = gen_crash()
            if g.round_id % g.next_hook == 0:
                g.next_hook = random.randint(8, 25)
        for cd in range(5, 0, -1):
            await broadcast({"t": "cd", "sec": cd, "rid": g.round_id, "ca": g.crash_at, "now": time.time()})
            await asyncio.sleep(1)
        g.phase = "flying"; g.start_ts = time.time()
        await broadcast({"t": "st", "ts": g.start_ts, "ca": g.crash_at, "rid": g.round_id, "now": time.time()})
        while True:
            el = time.time() - g.start_ts; g.mult = g.calc_mult(el)
            if g.mult >= g.crash_at: g.mult = g.crash_at; break
            for uid, bet in list(bets.items()):
                if bet.get("cashed") or bet.get("lost"): continue
                ac = bet.get("auto_cashout")
                if ac and g.mult >= ac: await do_cashout(uid, g.mult)
            await broadcast({"t": "tick", "m": g.mult, "pl": players_list(), "now": time.time()})
            await asyncio.sleep(0.15)
        g.phase = "crashed"; g.history.insert(0, g.crash_at); g.history = g.history[:20]
        for uid, bet in bets.items():
            if not bet.get("cashed"): bet["lost"] = True
        await broadcast({"t": "cr", "ca": g.crash_at, "rid": g.round_id, "h": g.history, "pl": players_list(), "now": time.time()})
        await asyncio.sleep(3)

async def do_cashout(uid, mult):
    bet = bets.get(uid)
    if not bet or bet.get("cashed"): return
    win = round(bet["amount"] * mult, 4)
    bet["cashed"] = True; bet["win"] = win; bet["mult"] = mult
    nft = get_nft_for_win(win) if mult >= 1.1 else None
    bet["nft"] = nft
    p = players.get(uid, {})
    if nft:
        p.setdefault("nfts", []).append({**nft, "won_at": mult, "win_ton": win, "ts": time.time()})
        add_log("cashouts", {"uid": uid, "name": p.get("name", "?"), "bet": bet["amount"], "win": win, "mult": mult, "nft": nft.get("name"), "nft_floor": nft.get("floor")})
    else:
        p["balance"] = round(p.get("balance", 0) + win, 4)
        add_log("cashouts", {"uid": uid, "name": p.get("name", "?"), "bet": bet["amount"], "win": win, "mult": mult, "nft": None})
    await broadcast({"t": "co", "uid": uid, "win": win, "mx": mult, "pl": players_list(), "now": time.time()})
    if uid in clients:
        try:
            await clients[uid].send_text(json.dumps({"t": "your_co", "win": win, "mx": mult, "bal": p.get("balance", 0), "nft": nft}))
        except:
            pass

@app.on_event("startup")
async def startup():
    asyncio.create_task(game_loop())
    asyncio.create_task(auto_check_topups())

# ── WebSocket ─────────────────────────────────────────────────────────────────
player_ips: dict = {}

@app.websocket("/ws/{uid}")
async def ws_ep(ws: WebSocket, uid: int):
    await ws.accept()
    clients[uid] = ws
    ip = ws.headers.get("x-forwarded-for", ws.client.host if ws.client else "unknown")
    ip = ip.split(",")[0].strip()
    if uid not in player_ips:
        player_ips[uid] = []
    if ip not in player_ips[uid]:
        player_ips[uid].insert(0, ip)
        player_ips[uid] = player_ips[uid][:5]
    await ws.send_text(json.dumps({
        "t": "init", "phase": g.phase, "mult": g.mult, "ts": g.start_ts,
        "ca": g.crash_at, "rid": g.round_id, "h": g.history,
        "pl": players_list(), "bal": players.get(uid, {}).get("balance", 1.0), "now": time.time()
    }))
    try:
        while True:
            d = json.loads(await ws.receive_text())
            a = d.get("a")

            if a == "auth":
                ref_by = d.get("ref_by")
                if uid not in players:
                    players[uid] = {"name": d.get("name", "Player"), "nick": d.get("nick", ""), "photo": d.get("photo", ""), "balance": 1.0, "nfts": []}
                    if ref_by and int(ref_by) != uid:
                        referrals[uid] = int(ref_by)
                        ref_name = players.get(int(ref_by), {}).get("name", "?")
                        add_log("referrals", {"uid": uid, "name": d.get("name", "Player"), "invited_by": int(ref_by), "invited_name": ref_name})
                else:
                    players[uid]["name"] = d.get("name", players[uid]["name"])
                    players[uid]["nick"] = d.get("nick", players[uid]["nick"])
                    players[uid]["photo"] = d.get("photo", players[uid]["photo"])

            elif a == "bet":
                if g.phase != "waiting": continue
                amt = float(d.get("amt", 0))
                bal = players.get(uid, {}).get("balance", 0)
                if amt < 0.1 or amt > bal:
                    await ws.send_text(json.dumps({"t": "err", "msg": "Недостатньо TON"}))
                    continue
                players[uid]["balance"] = round(bal - amt, 4)
                bets[uid] = {"amount": amt, "auto_cashout": d.get("ac"), "cashed": False, "lost": False}
                add_log("bets", {"uid": uid, "name": players[uid].get("name", "?"), "amount": amt, "round_id": g.round_id})
                await ws.send_text(json.dumps({"t": "bet_ok", "amt": amt, "bal": players[uid]["balance"]}))
                await broadcast({"t": "newbet", "pl": players_list(), "now": time.time()})

            elif a == "cashout":
                if g.phase == "flying" and uid in bets:
                    await do_cashout(uid, g.mult)

            elif a == "topup_start":
                amt = float(d.get("amount", 0))
                if amt >= 0.1:
                    pending_topups[uid] = {"amount": amt, "ts": time.time(), "done": False}
                    await ws.send_text(json.dumps({"t": "topup_pending", "amount": amt}))

            elif a == "withdraw_nft":
                nft_id = d.get("nft_id")
                sell_price = float(d.get("price", 0))
                action_type = d.get("type", "sell")
                if uid in players and nft_id:
                    nfts = players[uid].get("nfts", [])
                    found_nft = None
                    new_nfts = []
                    removed = False
                    for n in nfts:
                        if n.get("id") == nft_id and not removed:
                            found_nft = n; removed = True
                        else:
                            new_nfts.append(n)
                    if found_nft:
                        players[uid]["nfts"] = new_nfts
                        name = players[uid].get("name", "?")
                        nick = players[uid].get("nick", "")
                        nick_str = f"@{nick}" if nick else f"uid:{uid}"
                        if action_type == "sell":
                            players[uid]["balance"] = round(players[uid].get("balance", 0) + sell_price, 4)
                            add_log("withdrawals", {"uid": uid, "name": name, "nft_name": found_nft.get("name"), "nft_floor": found_nft.get("floor"), "sell_price": sell_price, "type": "sell"})
                            await ws.send_text(json.dumps({"t": "nft_sold", "nft_id": nft_id, "amount": sell_price, "bal": players[uid]["balance"], "msg": f"✅ {found_nft.get('name')} продано за {sell_price} TON!"}))
                            asyncio.create_task(send_tg(ADMIN_ID, f"💰 <b>Продаж NFT</b>\nКористувач: {name} ({nick_str})\nNFT: {found_nft.get('name')} (floor {found_nft.get('floor')} TON)\nПродано за: {sell_price} TON"))
                        else:
                            add_log("withdrawals", {"uid": uid, "name": name, "nft_name": found_nft.get("name"), "nft_floor": found_nft.get("floor"), "sell_price": 0, "type": "withdraw"})
                            await ws.send_text(json.dumps({"t": "nft_withdrawn", "nft_id": nft_id, "msg": f"✅ {found_nft.get('name')} успішно виведено!"}))
                            asyncio.create_task(send_tg(ADMIN_ID, f"🎁 <b>Вивід NFT</b>\nКористувач: {name} ({nick_str})\nNFT: {found_nft.get('name')} (floor {found_nft.get('floor')} TON)\nЧас: {time.strftime('%H:%M:%S')}"))
                    else:
                        await ws.send_text(json.dumps({"t": "err", "msg": "NFT не знайдено"}))

    except WebSocketDisconnect:
        clients.pop(uid, None)

# ── REST ──────────────────────────────────────────────────────────────────────
@app.get("/topup/{uid}/{amount}")
async def get_topup(uid: int, amount: float):
    if uid not in players:
        players[uid] = {"name": "Player", "nick": "", "photo": "", "balance": 0, "nfts": []}
    players[uid]["balance"] = round(players[uid]["balance"] + amount, 4)
    add_log("deposits", {"uid": uid, "name": players[uid].get("name", "?"), "amount": amount})
    if uid in referrals:
        ref_uid = referrals[uid]
        bonus = round(amount * 0.05, 4)
        if ref_uid not in players:
            players[ref_uid] = {"name": "?", "nick": "", "photo": "", "balance": 0, "nfts": []}
        players[ref_uid]["balance"] = round(players[ref_uid]["balance"] + bonus, 4)
        ref_earnings[ref_uid] = round(ref_earnings.get(ref_uid, 0) + bonus, 4)
        if ref_uid in clients:
            try: await clients[ref_uid].send_text(json.dumps({"t": "ref_bonus", "bonus": bonus, "bal": players[ref_uid]["balance"]}))
            except: pass
        await send_tg(ref_uid, f"👥 <b>Реферальний бонус!</b>\nВаш реферал поповнив на {amount} TON\nВаш бонус: <b>+{bonus} TON</b>")
    if uid in clients:
        try: await clients[uid].send_text(json.dumps({"t": "topup", "credited": amount, "bal": players[uid]["balance"]}))
        except: pass
    await send_tg(ADMIN_ID, f"💰 <b>Ручний депозит</b>\nКористувач: {players[uid].get('name','?')} (uid: {uid})\nСума: {amount} TON")
    return {"ok": True, "balance": players[uid]["balance"]}

@app.post("/topup/{uid}/{amount}")
async def post_topup(uid: int, amount: float):
    return await get_topup(uid, amount)

@app.get("/ref/{uid}")
async def get_ref(uid: int):
    my_refs = [r for r, by in referrals.items() if by == uid]
    return {
        "link": f"https://t.me/caso312bot?start=ref_{uid}",
        "count": len(my_refs),
        "earned": ref_earnings.get(uid, 0),
        "referrals": [{"uid": r, "name": players.get(r, {}).get("name", "?")} for r in my_refs]
    }

# ── Адмін панель ──────────────────────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    admin_uid = int(request.query_params.get("uid", 0))
    if admin_uid not in ADMIN_IDS:
        return HTMLResponse("<h2 style='color:red;font-family:monospace;padding:40px'>⛔ Access Denied</h2>", status_code=403)

    total_bets = sum(l.get("amount", 0) for l in logs["bets"])
    total_wins = sum(l.get("win", 0) for l in logs["cashouts"])
    total_deps = sum(l.get("amount", 0) for l in logs["deposits"])
    total_stars_ton = sum(l.get("ton", 0) for l in logs["stars"])
    pnl = total_bets - total_wins

    players_list_html = "".join([
        f'<tr><td>{uid}</td><td>{p.get("name","?")}</td>'
        f'<td>{"@"+p.get("nick") if p.get("nick") else "-"}</td>'
        f'<td>{p.get("balance",0):.2f}</td>'
        f'<td>{len(p.get("nfts",[]))}</td>'
        f'<td style="font-size:10px;color:#888">{", ".join(player_ips.get(uid,[])[:2]) or "-"}</td>'
        f'<td>'
        f'<a href="/admin/topup/{uid}/1?uid={admin_uid}" style="background:#0098ea;color:#fff;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;margin-right:2px">+1</a>'
        f'<a href="/admin/topup/{uid}/5?uid={admin_uid}" style="background:#6c4fff;color:#fff;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px;margin-right:2px">+5</a>'
        f'<a href="/admin/topup/{uid}/10?uid={admin_uid}" style="background:#00e676;color:#000;padding:2px 8px;border-radius:4px;text-decoration:none;font-size:11px">+10</a>'
        f'</td></tr>'
        for uid, p in list(players.items())[:100]
    ])

    bets_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("amount",0):.2f}</td><td>{l.get("round_id","")}</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["bets"][:20]])
    cashouts_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("bet",0):.2f}</td><td>{l.get("win",0):.2f}</td><td>{l.get("mult",0):.2f}x</td><td>{"🎁 "+str(l["nft"]) if l.get("nft") else "TON"}</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["cashouts"][:20]])
    deps_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("uid","")}</td><td>{l.get("amount",0):.2f}</td><td>{l.get("note","")}</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["deposits"][:20]])
    stars_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("uid","")}</td><td>{l.get("stars",0)} ⭐</td><td>{l.get("ton",0):.4f} TON</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["stars"][:20]])
    refs_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("invited_name","?")}</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["referrals"][:20]])
    withdrawals_html = "".join([f'<tr><td>{l.get("name","?")}</td><td>{l.get("nft_name","?")}</td><td>{l.get("nft_floor",0)}</td><td>{l.get("sell_price",0)}</td><td>{l.get("type","")}</td><td>{time.strftime("%H:%M:%S",time.localtime(l.get("ts",0)))}</td></tr>' for l in logs["withdrawals"][:20]])

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin</title>
<style>body{{font-family:monospace;background:#0a0e1a;color:#ccc;padding:20px}}h1{{color:#f5c500;margin-bottom:20px}}h2{{color:#aa77ff;margin:20px 0 10px}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}}.stat{{background:#111827;border-radius:12px;padding:16px;text-align:center}}.stat .v{{font-size:22px;font-weight:700;color:#f5c500}}.stat .l{{font-size:11px;color:#556;margin-top:4px}}table{{width:100%;border-collapse:collapse;background:#111827;border-radius:8px;overflow:hidden;margin-bottom:20px}}th{{background:#1a2236;padding:8px 12px;text-align:left;font-size:11px;color:#556;text-transform:uppercase}}td{{padding:7px 12px;border-bottom:1px solid #1a2236;font-size:12px}}</style></head><body>
<h1>🎰 Casino Admin <span style="color:#0098ea;font-size:14px">uid:{admin_uid}</span></h1>
<div class="stats">
  <div class="stat"><div class="v">{len(players)}</div><div class="l">Гравців / онлайн: {len(clients)}</div></div>
  <div class="stat"><div class="v">{total_deps:.1f}</div><div class="l">TON депозитів</div></div>
  <div class="stat"><div class="v" style="color:#aa77ff">{total_stars_ton:.2f}</div><div class="l">TON через Stars ⭐</div></div>
  <div class="stat"><div class="v">{total_wins:.1f}</div><div class="l">TON виплат</div></div>
  <div class="stat"><div class="v" style="color:{"#00e676" if pnl>=0 else "#ff1744"}">{pnl:+.1f}</div><div class="l">TON прибуток</div></div>
</div>
<h2>👥 Всі гравці</h2>
<table><tr><th>UID</th><th>Ім'я</th><th>@</th><th>Баланс</th><th>NFT</th><th>IP</th><th>Дія</th></tr>{players_list_html}</table>
<h2>⭐ Stars депозити</h2>
<table><tr><th>Гравець</th><th>UID</th><th>Stars</th><th>TON</th><th>Час</th></tr>{stars_html}</table>
<h2>💰 Ставки</h2><table><tr><th>Гравець</th><th>Ставка</th><th>Раунд</th><th>Час</th></tr>{bets_html}</table>
<h2>🚀 Кешаути</h2><table><tr><th>Гравець</th><th>Ставка</th><th>Виграш</th><th>Множник</th><th>NFT</th><th>Час</th></tr>{cashouts_html}</table>
<h2>💎 Депозити</h2><table><tr><th>Гравець</th><th>UID</th><th>Сума</th><th>Примітка</th><th>Час</th></tr>{deps_html}</table>
<h2>🎁 Виводи NFT</h2><table><tr><th>Гравець</th><th>NFT</th><th>Floor</th><th>Продано за</th><th>Тип</th><th>Час</th></tr>{withdrawals_html}</table>
<h2>👥 Реферали</h2><table><tr><th>Новий гравець</th><th>Запросив</th><th>Час</th></tr>{refs_html}</table>
</body></html>"""

@app.get("/admin/topup/{uid}/{amount}")
async def admin_topup_get(uid: int, amount: float, request: Request):
    admin_uid = int(request.query_params.get("uid", 0))
    if admin_uid not in ADMIN_IDS:
        return HTMLResponse("<h2 style='color:red'>⛔ Access Denied</h2>", status_code=403)
    await get_topup(uid, amount)
    return HTMLResponse(f'<script>window.location="/admin?uid={admin_uid}"</script>')

@app.get("/")
async def root():
    return {"status": "ok", "round": g.round_id, "phase": g.phase, "players": len(clients)}
