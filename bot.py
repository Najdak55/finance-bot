import telebot
import sqlite3
from datetime import datetime, timedelta
import threading
import time
import os

# ===== ТОКЕН =====
TOKEN = "8808969338:AAFUEyeZ35_1pYFsOXBXdWSj_5Z_eMWymoc"
# =================

bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
DB_PATH = "reminders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            plan TEXT DEFAULT 'free',
            reminders_created INTEGER DEFAULT 0,
            registered_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            remind_at TEXT,
            repeat TEXT DEFAULT 'none',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ===== ФУНКЦИИ БАЗЫ =====

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at) VALUES (?, ?, ?, ?)',
        (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

def get_user_plan(user_id):
    user = get_user(user_id)
    if user:
        return user[3]
    return 'free'

def get_user_reminders_count(user_id):
    user = get_user(user_id)
    if user:
        return user[4]
    return 0

def add_reminder(user_id, text, remind_at, repeat='none'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO reminders (user_id, text, remind_at, repeat, created_at) VALUES (?, ?, ?, ?, ?)',
        (user_id, text, remind_at, repeat, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()
    # Увеличиваем счётчик
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET reminders_created = reminders_created + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user_reminders(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, text, remind_at, repeat FROM reminders WHERE user_id = ? ORDER BY remind_at', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def delete_reminder(reminder_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
    conn.commit()
    conn.close()

def get_all_pending_reminders():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, text, remind_at, repeat FROM reminders')
    data = cursor.fetchall()
    conn.close()
    return data

def delete_reminder_by_id(reminder_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

# ===== ПЛАНИРОВЩИК =====

def check_reminders():
    """Проверяет напоминания каждые 30 секунд"""
    while True:
        try:
            now = datetime.now()
            reminders = get_all_pending_reminders()
            
            for r in reminders:
                r_id, user_id, text, remind_at, repeat = r
                try:
                    remind_time = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
                except:
                    continue
                
                # Если время пришло (с погрешностью 1 минута)
                if now >= remind_time and now < remind_time + timedelta(minutes=1):
                    try:
                        bot.send_message(user_id, f"⏰ *НАПОМИНАНИЕ:*\n{text}", parse_mode="Markdown")
                    except:
                        pass
                    
                    if repeat == 'daily':
                        # Переносим на следующий день
                        new_time = remind_time + timedelta(days=1)
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?', 
                                     (new_time.strftime("%Y-%m-%d %H:%M"), r_id))
                        conn.commit()
                        conn.close()
                    elif repeat == 'weekly':
                        new_time = remind_time + timedelta(weeks=1)
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?', 
                                     (new_time.strftime("%Y-%m-%d %H:%M"), r_id))
                        conn.commit()
                        conn.close()
                    else:
                        delete_reminder_by_id(r_id)
        except Exception as e:
            print(f"Ошибка планировщика: {e}")
        
        time.sleep(30)

# Запускаем планировщик в отдельном потоке
scheduler_thread = threading.Thread(target=check_reminders, daemon=True)
scheduler_thread.start()

# ===== КОМАНДЫ БОТА =====

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    create_user(user_id, username, first_name)
    
    bot.send_message(
        message.chat.id,
        "⏰ *Привет! Я твой личный напоминальник.*\n\n"
        "📌 *Команды:*\n"
        "`/remind 18:00 позвонить маме` — напомнить сегодня в 18:00\n"
        "`/remind 18:00 25.12 купить подарки` — напомнить в конкретную дату\n"
        "`/daily 09:00 зарядка` — ежедневное напоминание\n"
        "`/list` — показать все напоминания\n"
        "`/delete 3` — удалить напоминание №3\n"
        "`/stats` — статистика\n\n"
        "💎 *Бесплатно:* 3 напоминания\n"
        "⭐ *Pro (149 ₽/мес):* безлимит + повторяющиеся",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['remind'])
def remind(message):
    user_id = message.from_user.id
    plan = get_user_plan(user_id)
    count = get_user_reminders_count(user_id)
    
    if plan == 'free' and count >= 3:
        bot.reply_to(
            message,
            "⛔ *Лимит бесплатных напоминаний исчерпан (3/3).*\n\n"
            "💎 Оформи Pro за 149 ₽/мес — безлимит напоминаний.\n"
            "Напиши /subscribe чтобы узнать подробнее.",
            parse_mode="Markdown"
        )
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(
                message,
                "❌ *Формат:*\n"
                "`/remind 18:00 текст` — сегодня в 18:00\n"
                "`/remind 18:00 25.12 текст` — 25 декабря в 18:00",
                parse_mode="Markdown"
            )
            return
        
        time_part = parts[1]
        rest = parts[2]
        
        # Проверяем, есть ли дата в rest
        rest_parts = rest.split(maxsplit=1)
        if len(rest_parts) == 2 and '.' in rest_parts[0] and len(rest_parts[0].split('.')) == 2:
            # Это дата: 25.12
            date_part = rest_parts[0]
            text = rest_parts[1]
            day, month = date_part.split('.')
            year = datetime.now().year
            # Если дата уже прошла в этом году — берём следующий год
            remind_date = datetime(year, int(month), int(day))
            if remind_date < datetime.now():
                remind_date = datetime(year + 1, int(month), int(day))
            remind_at = f"{remind_date.strftime('%Y-%m-%d')} {time_part}"
        else:
            # Это просто время: 18:00
            text = rest
            today = datetime.now().strftime("%Y-%m-%d")
            remind_at = f"{today} {time_part}"
            # Если время уже прошло — переносим на завтра
            remind_dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
            if remind_dt < datetime.now():
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                remind_at = f"{tomorrow} {time_part}"
        
        add_reminder(user_id, text, remind_at, 'none')
        
        remind_dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
        bot.reply_to(
            message,
            f"✅ *Напоминание создано!*\n\n"
            f"📝 {text}\n"
            f"⏰ {remind_dt.strftime('%d.%m.%Y в %H:%M')}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}\n\nПроверь формат: `/remind 18:00 текст`", parse_mode="Markdown")

@bot.message_handler(commands=['daily'])
def daily(message):
    user_id = message.from_user.id
    plan = get_user_plan(user_id)
    
    if plan == 'free':
        bot.reply_to(
            message,
            "⛔ *Ежедневные напоминания доступны только в Pro.*\n\n"
            "💎 Оформи Pro за 149 ₽/мес — безлимит + повторяющиеся.\n"
            "Напиши /subscribe чтобы узнать подробнее.",
            parse_mode="Markdown"
        )
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(
                message,
                "❌ *Формат:* `/daily 09:00 зарядка`",
                parse_mode="Markdown"
            )
            return
        
        time_part = parts[1]
        text = parts[2]
        
        today = datetime.now().strftime("%Y-%m-%d")
        remind_at = f"{today} {time_part}"
        remind_dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
        if remind_dt < datetime.now():
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            remind_at = f"{tomorrow} {time_part}"
        
        add_reminder(user_id, text, remind_at, 'daily')
        
        bot.reply_to(
            message,
            f"✅ *Ежедневное напоминание создано!*\n\n"
            f"📝 {text}\n"
            f"⏰ Каждый день в {time_part}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['list'])
def list_reminders(message):
    user_id = message.from_user.id
    reminders = get_user_reminders(user_id)
    
    if not reminders:
        bot.reply_to(message, "📭 У тебя нет напоминаний.\n\nСоздай первое: `/remind 18:00 позвонить маме`", parse_mode="Markdown")
        return
    
    msg = "📋 *Твои напоминания:*\n\n"
    for r in reminders:
        r_id, text, remind_at, repeat = r
        try:
            dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
            time_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            time_str = remind_at
        
        repeat_icon = "🔁" if repeat == 'daily' else ""
        msg += f"*{r_id}.* {text}\n"
        msg += f"   ⏰ {time_str} {repeat_icon}\n\n"
    
    msg += "🗑 Чтобы удалить: `/delete НОМЕР`"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['delete'])
def delete(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Формат: `/delete НОМЕР`\n\nПосмотри номера: /list", parse_mode="Markdown")
            return
        reminder_id = int(parts[1])
        delete_reminder(reminder_id, user_id)
        bot.reply_to(message, f"✅ Напоминание №{reminder_id} удалено.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        bot.reply_to(message, "Напиши /start чтобы начать.")
        return
    
    plan = user[3]
    count = user[4]
    reminders = get_user_reminders(user_id)
    
    plan_name = "💎 Pro" if plan == 'pro' else "🆓 Бесплатный"
    limit = "∞" if plan == 'pro' else "3"
    
    msg = f"📊 *Твоя статистика:*\n\n"
    msg += f"👤 План: {plan_name}\n"
    msg += f"📝 Создано напоминаний: {count}\n"
    msg += f"📋 Активных: {len(reminders)}\n"
    msg += f"🎯 Лимит: {limit}\n"
    
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    bot.reply_to(
        message,
        "💎 *Pro-подписка (149 ₽/мес):*\n\n"
        "✅ Безлимит напоминаний\n"
        "✅ Ежедневные напоминания\n"
        "✅ Приоритетная поддержка\n\n"
        "💳 *Оплата:* скоро подключим. Пока напиши @твой_ник для ручного оформления.",
        parse_mode="Markdown"
    )

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("🚀 Бот-напоминальник запущен!")
    bot.polling(none_stop=True)
