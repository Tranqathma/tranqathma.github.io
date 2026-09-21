#!/usr/bin/env python3
"""
The Crew collector.

Reads the private Telegram group, brings across what the four of you wrote,
stores any photos permanently in the repository at a sensible size, and writes
everything into data/crew.json. The site builder turns that into the wire on
the Overview and the full Crew page.

Nobody needs an account anywhere. Telegram is the whole interface.

    python3 agents/crew.py

Needs TELEGRAM_TOKEN in the environment. Without it, it does nothing and says so.

Two commands, both used by replying to a message in the group:
    /drop   take that message off the site at the next run
    /pin    hold that message at the front of the wire
"""
import datetime, json, os, pathlib, sys, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data"
IMG = ROOT / "crew"
STATE = DATA / "crew_state.json"
CREW = DATA / "crew.json"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
NOW = datetime.datetime.now(IST).replace(microsecond=0).isoformat()

# Four voices, four colours. Used on the wire and on the Crew page.
PALETTE = ["#F2C14E", "#4FC3B0", "#7FB2F0", "#E8654A"]
MAX_MESSAGES = 400          # the wire keeps this many, oldest fall off
IMAGE_WIDTH = 1400          # phone photos are shrunk to this before storing


def api(token, method, **params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        out = json.loads(r.read())
    if not out.get("ok"):
        raise RuntimeError(f"{method}: {out}")
    return out["result"]


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def enrol(crew, user):
    """First four people to speak become the crew. Names are editable afterwards."""
    uid = str(user["id"])
    for m in crew["members"]:
        if m["telegram_id"] == uid:
            return m
    if len(crew["members"]) >= 4:
        return None                     # a fifth voice is ignored, not published
    m = {
        "telegram_id": uid,
        "name": user.get("first_name", "Crew"),
        "role": "Role not set yet",
        "colour": PALETTE[len(crew["members"]) % len(PALETTE)],
        "photo": None,
        "joined": NOW,
    }
    crew["members"].append(m)
    print(f"  enrolled {m['name']} as crew member {len(crew['members'])} of 4")
    return m


def fetch_photo(token, photo_sizes, msg_id):
    """Largest available size, shrunk, stored in the repository for good."""
    largest = max(photo_sizes, key=lambda p: p.get("file_size", 0))
    info = api(token, "getFile", file_id=largest["file_id"])
    url = f"https://api.telegram.org/file/bot{token}/{info['file_path']}"
    IMG.mkdir(parents=True, exist_ok=True)
    raw = IMG / f"{msg_id}.raw"
    with urllib.request.urlopen(url, timeout=60) as r, raw.open("wb") as f:
        f.write(r.read())
    out = IMG / f"{msg_id}.jpg"
    try:
        from PIL import Image
        im = Image.open(raw).convert("RGB")
        if im.width > IMAGE_WIDTH:
            im = im.resize((IMAGE_WIDTH, round(im.height * IMAGE_WIDTH / im.width)),
                           Image.LANCZOS)
        im.save(out, quality=84, optimize=True)
        raw.unlink()
    except ImportError:
        raw.rename(out)
    kb = out.stat().st_size / 1024
    print(f"  stored photo {out.name} at {kb:.0f} kB")
    return f"crew/{out.name}"


def command_name(text):
    """Return a Telegram command name, accepting /drop and /drop@bot."""
    if not text:
        return ""
    token = text.split(maxsplit=1)[0].casefold()
    return token.split("@", 1)[0]


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("crew: TELEGRAM_TOKEN is not set, nothing collected this run")
        return 0

    crew = load(CREW, {"members": [], "messages": []})
    state = load(STATE, {"offset": 0})

    try:
        updates = api(token, "getUpdates", offset=state["offset"], timeout=0, limit=100)
    except Exception as ex:                                   # noqa: BLE001
        print(f"crew: could not reach Telegram ({type(ex).__name__}), leaving the wire as it is")
        return 0

    if not updates:
        print("crew: nothing new in the group")
        return 0

    added = dropped = pinned = 0
    for u in updates:
        state["offset"] = u["update_id"] + 1
        msg = u.get("message") or u.get("channel_post")
        if not msg or "from" not in msg:
            continue

        text = (msg.get("text") or msg.get("caption") or "").strip()
        reply = msg.get("reply_to_message")
        command = command_name(text)

        # Moderation commands must never be published as ordinary messages.
        if command in {"/drop", "/pin"}:
            if not reply:
                print(
                    f"  {command} ignored: Telegram supplied no reply_to_message "
                    f"(update={u['update_id']}, message={msg.get('message_id')})"
                )
                continue

            target_id = str(reply["message_id"])
            if command == "/drop":
                before = len(crew["messages"])
                crew["messages"] = [m for m in crew["messages"] if m["id"] != target_id]
                dropped += before - len(crew["messages"])
                print(f"  dropped Telegram message {target_id}")
            else:
                for m in crew["messages"]:
                    if m["id"] == target_id:
                        m["pinned"] = True
                        pinned += 1
                print(f"  pinned Telegram message {target_id}")
            continue

        member = enrol(crew, msg["from"])
        if member is None:
            continue

        photo = None
        if msg.get("photo"):
            try:
                photo = fetch_photo(token, msg["photo"], msg["message_id"])
            except Exception as ex:                           # noqa: BLE001
                print(f"  photo on message {msg['message_id']} failed ({type(ex).__name__})")

        if not text and not photo:
            continue

        crew["messages"].append({
            "id": str(msg["message_id"]),
            "by": member["telegram_id"],
            "name": member["name"],
            "colour": member["colour"],
            "text": text,
            "photo": photo,
            "at": datetime.datetime.fromtimestamp(msg["date"], IST).replace(
                microsecond=0).isoformat(),
            "pinned": False,
        })
        added += 1

    crew["messages"].sort(key=lambda m: m["at"])
    crew["messages"] = crew["messages"][-MAX_MESSAGES:]
    crew["updated"] = NOW
    save(CREW, crew)
    save(STATE, state)

    print(f"crew: {added} new, {dropped} dropped, {pinned} pinned, "
          f"{len(crew['messages'])} on the wire, {len(crew['members'])} of 4 enrolled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
