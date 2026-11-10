"""Update docs/data.json: prices + weekly pivot levels (yfinance) and Thai news/outlook (Claude API + web search).

Run:  ANTHROPIC_API_KEY=... python scripts/update.py
Prices work without the key; the AI part is skipped if the key is missing.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "data.json"
TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def th_date(d):
    return f"{d.day} {TH_MONTHS[d.month - 1]}"


def r2(x):
    return None if x is None else round(float(x), 2)


def pivots(h, l, c):
    p = (h + l + c) / 3
    rng = h - l
    return {"S2": r2(p - rng), "S1": r2(2 * p - h), "P": r2(p), "R1": r2(2 * p - l), "R2": r2(p + rng)}


def price_block(daily):
    """daily: DataFrame indexed by date with High/Low/Close columns (one ticker)."""
    daily = daily.dropna(subset=["Close"])
    if daily.empty:
        return None
    last = daily.iloc[-1]
    prev_close = float(daily["Close"].iloc[-2]) if len(daily) > 1 else None
    last_day = daily.index[-1]
    weekly = daily.resample("W-FRI").agg({"High": "max", "Low": "min", "Close": "last"}).dropna()
    # The current week counts as complete only if the last bar is a Friday.
    if len(weekly) and weekly.index[-1].date() > last_day.date():
        weekly = weekly.iloc[:-1]
    out = {
        "last_close": r2(last["Close"]),
        "last_date": th_date(last_day),
        "day_change_pct": r2((float(last["Close"]) / prev_close - 1) * 100) if prev_close else None,
        "levels": None, "wk_label": "", "trend": "ทรงตัว",
    }
    if len(weekly):
        w = weekly.iloc[-1]
        out["levels"] = pivots(float(w["High"]), float(w["Low"]), float(w["Close"]))
        end = weekly.index[-1]
        start = end - pd.Timedelta(days=4)
        out["wk_label"] = f"{start.day}–{end.day} {TH_MONTHS[end.month - 1]}"
        if len(weekly) > 1:
            chg = float(w["Close"]) / float(weekly["Close"].iloc[-2]) - 1
            out["trend"] = "ขึ้น" if chg > 0.01 else "ลง" if chg < -0.01 else "ทรงตัว"
    lv = out["levels"]
    if lv:
        c = out["last_close"]
        out["zone"] = ("ต่ำกว่า S1" if c < lv["S1"] else "สูงกว่า R1" if c > lv["R1"] else "ระหว่าง S1–R1")
    return out


def fetch_prices(tickers):
    import yfinance as yf
    data = yf.download(tickers, period="3mo", interval="1d", group_by="ticker", auto_adjust=False, progress=False, threads=True)
    result = {}
    for t in tickers:
        try:
            df = data[t] if len(tickers) > 1 else data
            result[t] = price_block(df[["High", "Low", "Close"]])
        except Exception as e:  # keep going for other tickers
            print(f"price error {t}: {e}", file=sys.stderr)
            result[t] = None
    return result


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model reply")
    return json.loads(m.group(0))


def ai_commentary(rows):
    import anthropic
    client = anthropic.Anthropic()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = []
    for r in rows:
        lv = r.get("levels") or {}
        lines.append(f"- {r['ticker']} ({r['name']}, กลุ่ม {r['group']}): ปิด {r.get('last_close')} ({r.get('last_date')}), "
                     f"เปลี่ยน {r.get('day_change_pct')}% วันล่าสุด, แนวโน้มสัปดาห์ {r.get('trend')}, "
                     f"S1 {lv.get('S1')} R1 {lv.get('R1')}, ตอนนี้ {r.get('zone', '-')}")
    prompt = f"""วันนี้ {today} (UTC). คุณช่วยนักลงทุนรายย่อยติดตามพอร์ตหุ้นสหรัฐฯ
โปรไฟล์: {CONFIG['investor_profile']}
แผนปัจจุบัน: {CONFIG['plan']}

ข้อมูลราคา (คำนวณแล้ว เชื่อถือตัวเลขนี้ อย่าแก้):
{chr(10).join(lines)}

ใช้ web search หาข่าวสำคัญล่าสุด (1-3 วันทำการ) ของตลาดและของหุ้นแต่ละตัว ค้นอย่างประหยัด รวมหลายตัวในการค้นครั้งเดียวได้
แล้วตอบเป็น JSON อย่างเดียว ไม่มีข้อความอื่น ตามรูปแบบ:
{{"market": "สรุปภาพตลาด 2-3 ประโยคภาษาไทย (Nasdaq/S&P, ชิป, น้ำมัน, ดอกเบี้ย)",
  "next_events": "เหตุการณ์สำคัญสัปดาห์หน้าที่เกี่ยวกับพอร์ต 1-2 ประโยค",
  "stocks": {{"TICKER": {{"news": "ข่าวล่าสุด 1-2 ประโยค", "outlook": "มุมมองทิศทาง 1 ประโยค และอะไรจะเปลี่ยนมุมมอง", "action": "สิ่งที่ควรทำสั้นๆ ให้สอดคล้องกับแผน"}}}}}}
ภาษาไทยทั้งหมด ห้ามแต่งตัวเลขที่ไม่ได้มาจากข้อมูลข้างบนหรือแหล่งข่าว ถ้าไม่มีข่าวเฉพาะตัวให้บอกตรงๆ"""
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": int(CONFIG.get("max_searches", 8))}]
    text_parts, sources = [], []
    for _ in range(5):  # server-tool turns can pause; continue them
        resp = client.messages.create(model=CONFIG["model"], max_tokens=6000, messages=messages, tools=tools)
        for b in resp.content:
            if b.type == "text":
                text_parts.append(b.text)
                for c in getattr(b, "citations", None) or []:
                    url = getattr(c, "url", None)
                    if url and url not in [s["url"] for s in sources]:
                        sources.append({"url": url, "title": getattr(c, "title", "") or url})
        if resp.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": resp.content}]
    parsed = extract_json("".join(text_parts))
    parsed["sources"] = sources[:12]
    return parsed


def main():
    holdings = CONFIG["holdings"]
    tickers = [h["ticker"] for h in holdings]
    old = {}
    if OUT.exists():
        try:
            old = {s["ticker"]: s for s in json.loads(OUT.read_text(encoding="utf-8")).get("stocks", [])}
        except Exception:
            old = {}
    prices = fetch_prices(tickers)
    rows = []
    for h in holdings:
        r = dict(h)
        r.update(prices.get(h["ticker"]) or {k: old.get(h["ticker"], {}).get(k) for k in
                 ("last_close", "last_date", "day_change_pct", "levels", "wk_label", "trend", "zone")})
        rows.append(r)

    ai = {}
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            ai = ai_commentary(rows)
        except Exception as e:
            print(f"AI step failed, keeping previous text: {e}", file=sys.stderr)
    else:
        print("ANTHROPIC_API_KEY not set: skipping news/outlook", file=sys.stderr)

    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    ai_stocks = ai.get("stocks", {})
    for r in rows:
        t = r["ticker"]
        a = ai_stocks.get(t) or {}
        for k in ("news", "outlook", "action"):
            r[k] = a.get(k) or old.get(t, {}).get(k) or ""
    data = {
        "title": CONFIG["title"],
        "plan": CONFIG["plan"],
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "market": ai.get("market") or prev.get("market", ""),
        "next_events": ai.get("next_events") or prev.get("next_events", ""),
        "sources": ai.get("sources") or prev.get("sources", []),
        "ai_ok": bool(ai),
        "stocks": rows,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({len(rows)} stocks, ai={'yes' if ai else 'no'})")


if __name__ == "__main__":
    main()
