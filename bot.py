import telebot
import sqlite3
from datetime import datetime, timedelta
import os
import time

# ===== ТВОЙ ТОКЕН =====
TOKEN = "8808969338:AAFUEyeZ35_1pYFsOXBXdWSj_5Z_eMWymoc"
# ======================

bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
DB_PATH = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TEXT,
            subscription_end TEXT,
            language TEXT DEFAULT 'ru'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT CHECK(type IN ('income', 'expense')),
            amount REAL,
            category TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(user_id, username, lang='ru'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    first_seen = datetime.now().strftime("%Y-%m-%d %H:%M")
    subscription_end = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    cursor.execute(
        'INSERT INTO users (user_id, username, first_seen, subscription_end, language) VALUES (?, ?, ?, ?, ?)',
        (user_id, username, first_seen, subscription_end, lang)
    )
    conn.commit()
    conn.close()

def get_user_language(user_id):
    user = get_user(user_id)
    if user and len(user) >= 5:
        return user[4]
    return 'ru'

def check_subscription(user_id):
    user = get_user(user_id)
    if not user:
        return False
    subscription_end = user[3]
    if subscription_end and datetime.now().strftime("%Y-%m-%d") <= subscription_end:
        return True
    return False

def add_transaction(user_id, trans_type, amount, category):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        'INSERT INTO transactions (user_id, type, amount, category, date) VALUES (?, ?, ?, ?, ?)',
        (user_id, trans_type, amount, category, date)
    )
    conn.commit()
    conn.close()

def get_transactions(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT type, amount, category, date FROM transactions WHERE user_id = ? ORDER BY date DESC',
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    return data

def get_stats(user_id):
    transactions = get_transactions(user_id)
    total_income = 0
    total_expense = 0
    expenses_by_category = {}
    
    for t in transactions:
        trans_type, amount, category, date = t
        if trans_type == 'income':
            total_income += amount
        else:
            total_expense += amount
            expenses_by_category[category] = expenses_by_category.get(category, 0) + amount
    
    balance = total_income - total_expense
    
    expense_percentages = {}
    if total_expense > 0:
        for category, amount in expenses_by_category.items():
            expense_percentages[category] = round((amount / total_expense) * 100, 1)
    
    sorted_expenses = sorted(expense_percentages.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'expense_percentages': sorted_expenses,
        'transaction_count': len(transactions)
    }

# ===== КОМАНДЫ БОТА =====

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    user = get_user(user_id)
    if not user:
        create_user(user_id, username)
        bot.send_message(
            message.chat.id,
            "🎉 Добро пожаловать!\n\n"
            "Ты получил **3 дня бесплатного доступа**.\n\n"
            "📌 Команды:\n"
            "/add 500 еда - добавить расход\n"
            "/income 1000 зарплата - добавить доход\n"
            "/stats - показать статистику\n"
            "/check - проверить подписку",
            parse_mode="Markdown"
        )
    else:
        subscription_end = user[3]
        days_left = (datetime.strptime(subscription_end, "%Y-%m-%d") - datetime.now()).days
        if days_left < 0:
            days_left = 0
        bot.send_message(
            message.chat.id,
            f"👋 С возвращением! Осталось дней: {days_left}\n\n"
            "📌 Команды:\n"
            "/add 500 еда - добавить расход\n"
            "/income 1000 зарплата - добавить доход\n"
            "/stats - показать статистику",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['add'])
def add_expense(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        bot.reply_to(message, "⛔ Подписка истекла. Напиши /start для продления.")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Формат: /add СУММА КАТЕГОРИЯ\nПример: /add 500 еда")
            return
        amount = float(parts[1])
        category = parts[2].lower()
        add_transaction(user_id, 'expense', amount, category)
        bot.reply_to(message, f"✅ Расход: {amount} руб. на '{category}'")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['income'])
def add_income(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        bot.reply_to(message, "⛔ Подписка истекла. Напиши /start для продления.")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Формат: /income СУММА КАТЕГОРИЯ\nПример: /income 1000 зарплата")
            return
        amount = float(parts[1])
        category = parts[2].lower()
        add_transaction(user_id, 'income', amount, category)
        bot.reply_to(message, f"✅ Доход: +{amount} руб. за '{category}'")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        bot.reply_to(message, "⛔ Подписка истекла. Напиши /start для продления.")
        return
    
    data = get_stats(user_id)
    
    if data['transaction_count'] == 0:
        bot.reply_to(message, "📭 Нет транзакций.")
        return
    
    msg = "📊 *Статистика:*\n\n"
    msg += f"💰 Доходы: {data['total_income']:.2f} руб.\n"
    msg += f"💸 Расходы: {data['total_expense']:.2f} руб.\n"
    msg += f"📊 Баланс: {data['balance']:.2f} руб.\n"
    msg += f"📝 Записей: {data['transaction_count']}\n\n"
    
    if data['expense_percentages']:
        msg += "📉 *Расходы по категориям (%):*\n"
        for category, percent in data['expense_percentages']:
            msg += f"  • {category}: {percent}%\n"
    
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        bot.reply_to(message, "❌ Пользователь не найден. Напиши /start")
        return
    subscription_end = user[3]
    days_left = (datetime.strptime(subscription_end, "%Y-%m-%d") - datetime.now()).days
    if days_left > 0:
        bot.reply_to(message, f"✅ Подписка активна. Осталось {days_left} дней.")
    else:
        bot.reply_to(message, "⛔ Подписка истекла. Напиши /start для продления.")

# ===== ЗАПУСК БОТА =====
if __name__ == "__main__":
    print("🚀 Бот запущен!")
    bot.polling(none_stop=True)