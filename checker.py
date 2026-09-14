import sqlite3
from datetime import datetime, timedelta
import telebot

TOKEN = "8808969338:AAFUEyeZ35_1pYFsOXBXdWSj_5Z_eMWymoc"
bot = telebot.TeleBot(TOKEN)
DB_PATH = "reminders.db"

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

def update_reminder_time(reminder_id, new_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET remind_at = ? WHERE id = ?', (new_time, reminder_id))
    conn.commit()
    conn.close()

def check_reminders():
    now = datetime.now()
    reminders = get_all_pending_reminders()
    
    for r in reminders:
        r_id, user_id, text, remind_at, repeat = r
        try:
            remind_time = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
        except:
            continue
        
        # Если время пришло (с погрешностью 1 минута)
        if now >= remind_time and now < remind_time + timedelta(minutes=2):
            try:
                bot.send_message(user_id, f"⏰ *НАПОМИНАНИЕ:*\n{text}", parse_mode="Markdown")
            except:
                pass
            
            if repeat == 'daily':
                new_time = remind_time + timedelta(days=1)
                update_reminder_time(r_id, new_time.strftime("%Y-%m-%d %H:%M"))
            elif repeat == 'weekly':
                new_time = remind_time + timedelta(weeks=1)
                update_reminder_time(r_id, new_time.strftime("%Y-%m-%d %H:%M"))
            else:
                delete_reminder_by_id(r_id)

if __name__ == "__main__":
    print("🔍 Проверка напоминаний...")
    check_reminders()
    print("✅ Проверка завершена")
