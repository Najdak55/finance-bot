import telebot
from flask import Flask, request
import json
import sqlite3
from datetime import datetime, timedelta
import os

# ===== ТВОЙ НОВЫЙ ТОКЕН =====
TOKEN = "8808969338:AAFUEyeZ35_1pYFsOXBXdWSj_5Z_eMWymoc"
# =============================

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===== ПЕРЕВОДЫ НА ВСЕ ЯЗЫКИ =====
LANGUAGES = {
    'ru': {
        'name': 'Русский',
        'welcome': "🎉 Добро пожаловать, {name}!\n\nТы получил **3 дня бесплатного доступа** к финансовому трекеру.\n\n📌 Команды:\n/add 500 еда - добавить расход\n/income 1000 зарплата - добавить доход\n/stats - показать статистику\n/check - проверить подписку\n/lang - сменить язык\n\nПример: /add 350 кофе",
        'expense_added': "✅ Расход записан: {amount} руб. на '{category}'",
        'income_added': "✅ Доход записан: +{amount} руб. за '{category}'",
        'no_transactions': "📭 У тебя пока нет транзакций. Добавь /add или /income",
        'stats_header': "📊 *Твоя финансовая статистика:*\n\n💰 Доходы: {income} руб.\n💸 Расходы: {expense} руб.\n📊 Баланс: {balance} руб.\n📝 Всего записей: {count}\n\n📉 *Структура расходов (% от общих):*",
        'stats_item': "  • {category}: {percent}%",
        'subscription_active': "✅ Подписка активна. Осталось {days} дней.",
        'subscription_expired': "⛔ Подписка истекла. Используйте /subscribe для продления.",
        'user_not_found': "❌ Пользователь не найден. Напиши /start для регистрации.",
        'subscribe_msg': "💳 Оплата будет подключена позже. Пока просто продли подписку вручную:\nНапиши администратору @твой_ник_поддержки для продления.",
        'error_format': "❌ Формат: /add СУММА КАТЕГОРИЯ\nПример: /add 500 еда",
        'error_general': "❌ Ошибка: {error}",
        'subscription_expired_short': "⛔ Ваша подписка истекла. Используйте /subscribe для продления.",
        'lang_changed': "🌐 Язык изменён на русский!",
        'welcome_back': "👋 С возвращением! Осталось дней подписки: {days}\n\n📌 Команды:\n/add 500 еда - добавить расход\n/income 1000 зарплата - добавить доход\n/stats - показать статистику\n/lang - сменить язык",
        'lang_choose': "🌐 Выберите язык / Choose language / Choisissez la langue / اختر اللغة:",
        'lang_btn_ru': "🇷🇺 Русский",
        'lang_btn_en': "🇬🇧 English",
        'lang_btn_fr': "🇫🇷 Français",
        'lang_btn_ar': "🇸🇦 العربية"
    },
    'en': {
        'name': 'English',
        'welcome': "🎉 Welcome, {name}!\n\nYou got **3 days of free access** to the finance tracker.\n\n📌 Commands:\n/add 500 food - add expense\n/income 1000 salary - add income\n/stats - show statistics\n/check - check subscription\n/lang - change language\n\nExample: /add 350 coffee",
        'expense_added': "✅ Expense recorded: {amount} RUB on '{category}'",
        'income_added': "✅ Income recorded: +{amount} RUB for '{category}'",
        'no_transactions': "📭 You have no transactions yet. Use /add or /income",
        'stats_header': "📊 *Your financial statistics:*\n\n💰 Income: {income} RUB\n💸 Expenses: {expense} RUB\n📊 Balance: {balance} RUB\n📝 Total entries: {count}\n\n📉 *Expense structure (% of total):*",
        'stats_item': "  • {category}: {percent}%",
        'subscription_active': "✅ Subscription is active. {days} days left.",
        'subscription_expired': "⛔ Subscription expired. Use /subscribe to renew.",
        'user_not_found': "❌ User not found. Type /start to register.",
        'subscribe_msg': "💳 Payment will be added later. For now, renew manually:\nContact admin @your_support_nick for renewal.",
        'error_format': "❌ Format: /add AMOUNT CATEGORY\nExample: /add 500 food",
        'error_general': "❌ Error: {error}",
        'subscription_expired_short': "⛔ Your subscription has expired. Use /subscribe to renew.",
        'lang_changed': "🌐 Language changed to English!",
        'welcome_back': "👋 Welcome back! Days left on subscription: {days}\n\n📌 Commands:\n/add 500 food - add expense\n/income 1000 salary - add income\n/stats - show statistics\n/lang - change language",
        'lang_choose': "🌐 Choose language / Выберите язык / Choisissez la langue / اختر اللغة:",
        'lang_btn_ru': "🇷🇺 Russian",
        'lang_btn_en': "🇬🇧 English",
        'lang_btn_fr': "🇫🇷 French",
        'lang_btn_ar': "🇸🇦 Arabic"
    },
    'fr': {
        'name': 'Français',
        'welcome': "🎉 Bienvenue, {name} !\n\nVous avez **3 jours d'accès gratuit** au suivi financier.\n\n📌 Commandes :\n/add 500 nourriture - ajouter une dépense\n/income 1000 salaire - ajouter un revenu\n/stats - voir les statistiques\n/check - vérifier l'abonnement\n/lang - changer de langue\n\nExemple : /add 350 café",
        'expense_added': "✅ Dépense enregistrée : {amount} RUB pour '{category}'",
        'income_added': "✅ Revenu enregistré : +{amount} RUB pour '{category}'",
        'no_transactions': "📭 Vous n'avez pas encore de transactions. Utilisez /add ou /income",
        'stats_header': "📊 *Vos statistiques financières :*\n\n💰 Revenus : {income} RUB\n💸 Dépenses : {expense} RUB\n📊 Solde : {balance} RUB\n📝 Total d'entrées : {count}\n\n📉 *Structure des dépenses (% du total) :*",
        'stats_item': "  • {category} : {percent}%",
        'subscription_active': "✅ Abonnement actif. {days} jours restants.",
        'subscription_expired': "⛔ Abonnement expiré. Utilisez /subscribe pour renouveler.",
        'user_not_found': "❌ Utilisateur non trouvé. Tapez /start pour vous inscrire.",
        'subscribe_msg': "💳 Le paiement sera ajouté plus tard. Pour l'instant, renouvelez manuellement :\nContactez l'admin @votre_nick_support pour le renouvellement.",
        'error_format': "❌ Format : /add MONTANT CATÉGORIE\nExemple : /add 500 nourriture",
        'error_general': "❌ Erreur : {error}",
        'subscription_expired_short': "⛔ Votre abonnement a expiré. Utilisez /subscribe pour renouveler.",
        'lang_changed': "🌐 Langue changée en français !",
        'welcome_back': "👋 Bon retour ! Jours restants sur l'abonnement : {days}\n\n📌 Commandes :\n/add 500 nourriture - ajouter une dépense\n/income 1000 salaire - ajouter un revenu\n/stats - voir les statistiques\n/lang - changer de langue",
        'lang_choose': "🌐 Choisissez la langue / Выберите язык / Choose language / اختر اللغة:",
        'lang_btn_ru': "🇷🇺 Russe",
        'lang_btn_en': "🇬🇧 Anglais",
        'lang_btn_fr': "🇫🇷 Français",
        'lang_btn_ar': "🇸🇦 Arabe"
    },
    'ar': {
        'name': 'العربية',
        'welcome': "🎉 مرحباً بك، {name}!\n\nلقد حصلت على **3 أيام من الوصول المجاني** إلى متتبع المصاريف.\n\n📌 الأوامر:\n/add 500 طعام - إضافة مصروف\n/income 1000 راتب - إضافة دخل\n/stats - عرض الإحصائيات\n/check - التحقق من الاشتراك\n/lang - تغيير اللغة\n\nمثال: /add 350 قهوة",
        'expense_added': "✅ تم تسجيل المصروف: {amount} روبل على '{category}'",
        'income_added': "✅ تم تسجيل الدخل: +{amount} روبل من '{category}'",
        'no_transactions': "📭 ليس لديك معاملات بعد. استخدم /add أو /income",
        'stats_header': "📊 *إحصائياتك المالية:*\n\n💰 الدخل: {income} روبل\n💸 المصروفات: {expense} روبل\n📊 الرصيد: {balance} روبل\n📝 إجمالي الإدخالات: {count}\n\n📉 *هيكل المصروفات (٪ من الإجمالي):*",
        'stats_item': "  • {category}: {percent}٪",
        'subscription_active': "✅ الاشتراك نشط. متبقي {days} أيام.",
        'subscription_expired': "⛔ انتهى الاشتراك. استخدم /subscribe للتجديد.",
        'user_not_found': "❌ المستخدم غير موجود. اكتب /start للتسجيل.",
        'subscribe_msg': "💳 سيتم إضافة الدفع لاحقاً. الآن، جدد يدوياً:\nاتصل بالإداري @your_support_nick للتجديد.",
        'error_format': "❌ التنسيق: /add المبلغ الفئة\nمثال: /add 500 طعام",
        'error_general': "❌ خطأ: {error}",
        'subscription_expired_short': "⛔ انتهى اشتراكك. استخدم /subscribe للتجديد.",
        'lang_changed': "🌐 تم تغيير اللغة إلى العربية!",
        'welcome_back': "👋 مرحباً بعودتك! الأيام المتبقية في الاشتراك: {days}\n\n📌 الأوامر:\n/add 500 طعام - إضافة مصروف\n/income 1000 راتب - إضافة دخل\n/stats - عرض الإحصائيات\n/lang - تغيير اللغة",
        'lang_choose': "🌐 اختر اللغة / Choose language / Выберите язык / Choisissez la langue:",
        'lang_btn_ru': "🇷🇺 الروسية",
        'lang_btn_en': "🇬🇧 الإنجليزية",
        'lang_btn_fr': "🇫🇷 الفرنسية",
        'lang_btn_ar': "🇸🇦 العربية"
    }
}

# ===== БАЗА ДАННЫХ =====
DB_PATH = "/home/Najdak/mysite/finance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей (добавляем поле language)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TEXT,
            subscription_end TEXT,
            language TEXT DEFAULT 'ru'
        )
    ''')
    
    # Таблица транзакций
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

# ===== ФУНКЦИИ РАБОТЫ С БАЗОЙ =====

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

def update_language(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
    conn.commit()
    conn.close()

def get_user_language(user_id):
    user = get_user(user_id)
    if user and len(user) >= 5:
        return user[4]  # language
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

# ===== КЛАВИАТУРА ДЛЯ ВЫБОРА ЯЗЫКА =====
def language_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        telebot.types.InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
        telebot.types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")
    )
    return keyboard

# ===== ОБРАБОТЧИКИ КОМАНД =====

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    
    user = get_user(user_id)
    if not user:
        # Сначала создаём пользователя с языком по умолчанию (ru)
        create_user(user_id, username, 'ru')
        # Показываем выбор языка
        bot.send_message(
            message.chat.id,
            LANGUAGES['ru']['lang_choose'],
            reply_markup=language_keyboard()
        )
    else:
        lang = get_user_language(user_id)
        subscription_end = user[3]
        days_left = (datetime.strptime(subscription_end, "%Y-%m-%d") - datetime.now()).days
        
        if days_left < 0:
            days_left = 0
        
        msg = LANGUAGES[lang]['welcome_back'].format(days=days_left)
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['lang'])
def lang_command(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    bot.send_message(
        message.chat.id,
        LANGUAGES[lang]['lang_choose'],
        reply_markup=language_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def language_callback(call):
    user_id = call.from_user.id
    lang = call.data.split('_')[1]
    
    # Обновляем язык в БД
    update_language(user_id, lang)
    
    # Отвечаем пользователю
    bot.answer_callback_query(call.id, LANGUAGES[lang]['lang_changed'])
    bot.send_message(
        call.message.chat.id,
        LANGUAGES[lang]['lang_changed'],
        parse_mode="Markdown"
    )
    
    # Если пользователь новый, отправляем приветствие после выбора языка
    user = get_user(user_id)
    if user and user[1]:  # если есть username
        subscription_end = user[3]
        days_left = (datetime.strptime(subscription_end, "%Y-%m-%d") - datetime.now()).days
        if days_left < 0:
            days_left = 0
        
        if days_left == 3:  # новый пользователь
            msg = LANGUAGES[lang]['welcome'].format(name=call.from_user.first_name)
            bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
        else:
            msg = LANGUAGES[lang]['welcome_back'].format(days=days_left)
            bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_expense(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    if not check_subscription(user_id):
        bot.reply_to(message, LANGUAGES[lang]['subscription_expired_short'], parse_mode="Markdown")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, LANGUAGES[lang]['error_format'], parse_mode="Markdown")
            return
        
        amount = float(parts[1])
        category = parts[2].lower()
        
        add_transaction(user_id, 'expense', amount, category)
        bot.reply_to(
            message,
            LANGUAGES[lang]['expense_added'].format(amount=amount, category=category),
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, LANGUAGES[lang]['error_general'].format(error=e), parse_mode="Markdown")

@bot.message_handler(commands=['income'])
def add_income(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    if not check_subscription(user_id):
        bot.reply_to(message, LANGUAGES[lang]['subscription_expired_short'], parse_mode="Markdown")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, LANGUAGES[lang]['error_format'], parse_mode="Markdown")
            return
        
        amount = float(parts[1])
        category = parts[2].lower()
        
        add_transaction(user_id, 'income', amount, category)
        bot.reply_to(
            message,
            LANGUAGES[lang]['income_added'].format(amount=amount, category=category),
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, LANGUAGES[lang]['error_general'].format(error=e), parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    
    if not check_subscription(user_id):
        bot.reply_to(message, LANGUAGES[lang]['subscription_expired_short'], parse_mode="Markdown")
        return
    
    data = get_stats(user_id)
    
    if data['transaction_count'] == 0:
        bot.reply_to(message, LANGUAGES[lang]['no_transactions'], parse_mode="Markdown")
        return
    
    msg = LANGUAGES[lang]['stats_header'].format(
        income=data['total_income'],
        expense=data['total_expense'],
        balance=data['balance'],
        count=data['transaction_count']
    )
    
    if data['expense_percentages']:
        for category, percent in data['expense_percentages']:
            msg += "\n" + LANGUAGES[lang]['stats_item'].format(category=category, percent=percent)
    
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    user = get_user(user_id)
    
    if not user:
        bot.reply_to(message, LANGUAGES[lang]['user_not_found'], parse_mode="Markdown")
        return
    
    subscription_end = user[3]
    days_left = (datetime.strptime(subscription_end, "%Y-%m-%d") - datetime.now()).days
    
    if days_left > 0:
        status = LANGUAGES[lang]['subscription_active'].format(days=days_left)
    else:
        status = LANGUAGES[lang]['subscription_expired']
    
    bot.reply_to(message, status, parse_mode="Markdown")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    bot.reply_to(message, LANGUAGES[lang]['subscribe_msg'], parse_mode="Markdown")

# ===== ВЕБХУК =====

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        if not json_string:
            return "Empty request", 400
        
        update_dict = json.loads(json_string)
        update = telebot.types.Update.de_json(update_dict)
        bot.process_new_updates([update])
        
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return f"Error: {e}", 500

@app.route('/')
def index():
    return "Finance Bot is running! 🚀", 200

# ===== ПЕРЕМЕННАЯ ДЛЯ PYTHONANYWHERE =====
application = app

# ===== НАСТРОЙКА ВЕБХУКА =====
webhook_url = 'https://najdak.pythonanywhere.com/webhook'
try:
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"Webhook set to {webhook_url}")
except Exception as e:
    print(f"Error setting webhook: {e}")
