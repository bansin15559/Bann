import re
import sqlite3
import asyncio

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError


# =========================
# TELEGRAM CONFIG
# =========================

API_ID = 27403368              # <-- PUT YOUR API ID HERE
API_HASH = "7cfc7759b82410f5d90641d6a6fc415f"    # <-- PUT YOUR API HASH HERE

RAIDAR_ID = 5994885234
GROUP_ID = -4670140041

SESSION_NAME = "raidar_smash"


# =========================
# DATABASE
# =========================

db = sqlite3.connect(
    "processed_links.db",
    check_same_thread=False
)

db.execute("""
    CREATE TABLE IF NOT EXISTS processed_links (
        link TEXT PRIMARY KEY,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

db.commit()


def already_processed(link):
    result = db.execute(
        "SELECT 1 FROM processed_links WHERE link = ?",
        (link,)
    ).fetchone()

    return result is not None


def save_link(link):
    db.execute(
        "INSERT OR IGNORE INTO processed_links (link) VALUES (?)",
        (link,)
    )
    db.commit()


# =========================
# LINK EXTRACTION
# =========================

def extract_link(text):
    pattern = r"https?://(?:www\.)?(?:x\.com|twitter\.com)/[^\s]+"

    match = re.search(pattern, text or "")

    if not match:
        return None

    return match.group(0).rstrip(".,)>]}\"'")


# =========================
# TELEGRAM CLIENT
# =========================

client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)


# =========================
# MESSAGE HANDLER
# =========================

@client.on(events.NewMessage(chats=GROUP_ID))
async def raidar_handler(event):

    # Only accept messages from Raidar
    if event.sender_id != RAIDAR_ID:
        return

    message = event.message

    print("\n==============================")
    print("Raidar message detected!")

    # Extract X/Twitter link
    link = extract_link(message.raw_text)

    if not link:
        print("No X/Twitter link found.")
        return

    print("Link:", link)

    # Check database
    if already_processed(link):
        print("Already smashed before → SKIPPING")
        return

    print("New link → looking for Smash button...")

    # Make sure there are buttons
    if not message.buttons:
        print("No buttons found.")
        return

    # Search buttons
    for row in message.buttons:

        for button in row:

            button_text = button.text or ""

            print("Found button:", repr(button_text))

            # Detect Smash button
            if "👊" in button_text or "smash" in button_text.lower():

                print("Smash button found!")

                try:

                    await message.click(text=button_text)

                    print("👊 SMASH SUCCESSFUL!")

                    # Save ONLY after successful click
                    save_link(link)

                    print("Link saved to database.")

                except FloodWaitError as e:

                    print(
                        f"Telegram requested a wait of "
                        f"{e.seconds} seconds."
                    )

                except Exception as e:

                    print("Smash failed:", repr(e))

                return

    print("Smash button was not found.")


# =========================
# START
# =========================

async def main():

    print("===================================")
    print("     RAIDAR SMASHER")
    print("===================================")
    print("Raidar ID :", RAIDAR_ID)
    print("Group ID  :", GROUP_ID)
    print("Status    : Listening...")
    print("===================================")

    await client.start()

    print("Telegram connected successfully!")
    print("Waiting for Raidar messages...\n")

    await client.run_until_disconnected()


while True:

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print("\nConnection error:", repr(e))
        print("Reconnecting in 10 seconds...\n")

        import time
        time.sleep(10)