"""
Запусти цей скрипт ОДИН РАЗ локально щоб отримати URL фото всіх NFT:
    pip install httpx
    python fetch_gifts.py
"""
import asyncio, json, httpx

BOT_TOKEN = "8757352545:AAGlu9yQu97JHfGljZH4ocqOBU_-sJm1KR8"  # твій токен

async def main():
    async with httpx.AsyncClient() as client:
        # Отримуємо всі доступні подарунки
        r = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getAvailableGifts")
        data = r.json()
        
        if not data.get("ok"):
            print("Error:", data)
            return
            
        gifts = data["result"]["gifts"]
        print(f"Знайдено {len(gifts)} подарунків\n")
        
        results = {}
        for gift in gifts:
            gift_id = gift.get("id")
            sticker = gift.get("sticker", {})
            file_id = sticker.get("file_id", "")
            thumb = sticker.get("thumbnail", {}) or {}
            thumb_id = thumb.get("file_id", "")
            
            # Отримуємо file_path
            for fid in [thumb_id, file_id]:
                if not fid:
                    continue
                r2 = await client.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                    params={"file_id": fid}
                )
                d2 = r2.json()
                if d2.get("ok"):
                    path = d2["result"]["file_path"]
                    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{path}"
                    results[str(gift_id)] = {
                        "id": gift_id,
                        "url": url,
                        "file_path": path,
                        "star_count": gift.get("star_count", 0),
                    }
                    print(f"Gift {gift_id}: {url[:80]}...")
                    break
        
        # Зберігаємо результат
        with open("gift_urls.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nЗбережено в gift_urls.json")

asyncio.run(main())
