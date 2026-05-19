import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Meta WhatsApp Cloud API Config
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_RECIPIENT_PHONES = os.getenv("WHATSAPP_RECIPIENT_PHONES") # E.g., "1234567890,9876543210" (comma-separated, no +)

def shorten_url(url):
    try:
        response = requests.get(
            f"https://tinyurl.com/api-create.php?url={url}",
            timeout=5
        )

        if response.status_code == 200:
            return response.text

    except Exception:
        pass

    return url

def format_whatsapp_message(df: pd.DataFrame) -> str:
    timestamp = datetime.now().strftime("%d %b %Y")
    
    # WhatsApp uses *bold* for headers
    lines = [f"🚨 *Daily Pharma News Update* - {timestamp}\n"]
    
    grouped = df.groupby("company")
    for company, group in grouped:
        lines.append(f"🏢 *{company.upper()}*")
        for _, row in group.iterrows():
            headline = row.get("title", "No Title")
            source_url = row.get("link", "")
            source = row.get("source", "")
            tag = row.get("tag", "News")
            
            lines.append(f"📰 {headline}")
            lines.append(f"[{tag}] _({source})_")
            short_url = shorten_url(source_url)
            lines.append(f"🔗 Read Article:\n{short_url}\n")
            
    lines.append("_Regards, Synapse News Bot_")
    return "\n".join(lines)

def chunk_message(message: str, max_len=4000):
    """Split message into chunks if it exceeds WhatsApp's 4096 limit."""
    if len(message) <= max_len:
        return [message]
    
    chunks = []
    current_chunk = ""
    for line in message.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_len:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def send_whatsapp_alert(df: pd.DataFrame) -> bool:
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_RECIPIENT_PHONES:
        print("⚠️ WhatsApp credentials not found in .env. Skipping WhatsApp alert.")
        print("Required: WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_RECIPIENT_PHONES")
        return False

    if df.empty:
        print("No relevant news to send via WhatsApp.")
        return False

    full_message = format_whatsapp_message(df)
    message_chunks = chunk_message(full_message)

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    recipients = [p.strip() for p in WHATSAPP_RECIPIENT_PHONES.split(",") if p.strip()]

    all_success = True
    for recipient in recipients:
        print(f"📱 Sending WhatsApp alert to {recipient}...")
        for idx, chunk in enumerate(message_chunks):
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": chunk}
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                print(f"  ✅ Chunk {idx+1}/{len(message_chunks)} sent successfully!")
            except requests.exceptions.RequestException as e:
                print(f"  ❌ Failed to send chunk {idx+1}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"  Details: {e.response.text}")
                all_success = False
            
    return all_success
