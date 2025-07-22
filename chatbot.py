import os
import json
import datetime
from dotenv import load_dotenv
import chainlit as cl
from openai import AzureOpenAI


# Load environment variables truqutruet
load_dotenv("chatbot.env")

# Azure OpenAI configuration
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2025-01-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
SESSION_FILE = "chat_history.json"

def timestamp_now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_global_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Corrupted JSON file. Starting fresh.")
            return []
    return []

def save_global_session(new_session):
    try:
        sessions = load_global_sessions()
        sessions.append(new_session)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
        print(f"✅ Session saved. Total sessions: {len(sessions)}")
    except Exception as e:
        print(f"❌ Error saving session: {e}")

@cl.on_chat_start
async def start():
    cl.user_session.set("chat_history", [])
    cl.user_session.set("session_saved", False)
    await cl.Message(content="`/history` to view logs").send()
    # Inicializa el historial de chat y las sesiones pasadas en la sesión del usuario.

@cl.on_message
async def main(message: cl.Message):
    content = message.content.strip()

    if content == "/history":
        sessions = load_global_sessions()

        if not sessions:
            await cl.Message(content="🕘 No past sessions found.").send()
            return
        summary_lines = [
            f"**Session {i + 1}: {s['title']}**: {s['summary']}" for i, s in enumerate(sessions)
        ]
        summaries_text = "\n".join(summary_lines)
        await cl.Message(content=f"🗂️ Past Sessions:\n{summaries_text}").send()
        return
    
    # View full session log via `/session#` (e.g. /session2)
    if content.lower().startswith("/session"):
        sessions = load_global_sessions()
        try:
            idx = int(content.replace("/session", "").strip()) - 1
            if idx < 0 or idx >= len(sessions):
                raise IndexError
            log = sessions[idx]["full_log"]
            await cl.Message(content=f"📜 Full Log for Session {idx + 1}:\n\n{log}").send()
        except (ValueError, IndexError):
            await cl.Message(content="❌ Invalid session number. Use `/history` to view valid sessions.").send()
        return

    chat_history = cl.user_session.get("chat_history") or []
    chat_history.append({"role":"user", "content": message.content, "timestamp": timestamp_now()})

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        *[{"role": m["role"], "content": m["content"]} for m in chat_history]
    ]
    # Build the full message history (excluding timestamps for OpenAI)

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    
    # Llama a la API de OpenAI para obtener una respuesta del modelo.
    reply = response.choices[0].message.content
    # Extrae el contenido de la respuesta generada por el modelo.

    chat_history.append({"role":"assistant", "content": reply, "timestamp": timestamp_now()})
    # Añade la respuesta del modelo al historial de chat.

    cl.user_session.set("chat_history", chat_history)
    await cl.Message(content=reply).send()
    # Envía la respuesta al usuario a través de Chainlit.
    

@cl.on_chat_end
async def store_full_session():
    chat_history = cl.user_session.get("chat_history") or []
    if not chat_history:
        return

    # Full readable chat log
    log_text = "\n".join(
        f"[{m['timestamp']}] {m['role'].capitalize()}: {m['content']}"
        for m in chat_history
    )

    # Title generation
    title_prompt = [
        {"role": "system", "content": "Write a short 5–8 word title for this chat."},
        {"role": "user", "content": log_text}
    ]
    title_response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=title_prompt
    )
    title = title_response.choices[0].message.content.strip()

    # Summary generation
    summary_prompt = [
        {"role": "system", "content": "Summarize this chat in 1–2 short sentences."},
        {"role": "user", "content": log_text}
    ]
    summary_response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=summary_prompt
    )
    summary = summary_response.choices[0].message.content.strip()

    # Save to file
    save_global_session({
        "title": title,
        "summary": summary,
        "full_log": log_text,
        "timestamp": timestamp_now()
    })