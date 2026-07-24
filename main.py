import os
import sqlite3
import logging
import asyncio
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(
    os.getenv("ADMIN_ID", "0")
)

DB_FILE = "radius_users.db"

# Оператор
OPERATOR_USERNAME = "@RadiusSergeli"
OPERATOR_URL = "https://t.me/RadiusSergeli"

# Точка RADIUS
RADIUS_LATITUDE = 41.224346
RADIUS_LONGITUDE = 69.213793


# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return sqlite3.connect(DB_FILE)


def init_database():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            city TEXT,
            manager TEXT,
            created_at TEXT,
            last_seen_at TEXT,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    conn.commit()

    conn.close()

    logger.info("RADIUS database initialized")


# ============================================================
# СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def save_user(user):

    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name,
            last_name,
            created_at,
            last_seen_at,
            is_blocked
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            last_seen_at = excluded.last_seen_at,
            is_blocked = 0
    """, (
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        now,
        now
    ))

    conn.commit()

    conn.close()


# ============================================================
# СОХРАНЕНИЕ ТЕЛЕФОНА
# ============================================================

def save_phone(
    telegram_id,
    phone
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET phone = ?
        WHERE telegram_id = ?
    """, (
        phone,
        telegram_id
    ))

    conn.commit()

    conn.close()


# ============================================================
# СОХРАНЕНИЕ ГОРОДА
# ============================================================

def save_city(
    telegram_id,
    city
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET city = ?
        WHERE telegram_id = ?
    """, (
        city,
        telegram_id
    ))

    conn.commit()

    conn.close()


# ============================================================
# СОХРАНЕНИЕ МЕНЕДЖЕРА
# ============================================================

def save_manager(
    telegram_id,
    manager
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET manager = ?
        WHERE telegram_id = ?
    """, (
        manager,
        telegram_id
    ))

    conn.commit()

    conn.close()


# ============================================================
# ПОЛУЧЕНИЕ АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

def get_active_users():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT telegram_id
        FROM users
        WHERE is_blocked = 0
    """)

    users = cursor.fetchall()

    conn.close()

    return [
        user[0]
        for user in users
    ]


# ============================================================
# СТАТИСТИКА
# ============================================================

def get_user_stats():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE is_blocked = 0
    """)

    active = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE is_blocked = 1
    """)

    blocked = cursor.fetchone()[0]

    conn.close()

    return total, active, blocked


# ============================================================
# ПОМЕТИТЬ ЗАБЛОКИРОВАВШЕГО ПОЛЬЗОВАТЕЛЯ
# ============================================================

def mark_blocked(
    telegram_id
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_blocked = 1
        WHERE telegram_id = ?
    """, (
        telegram_id,
    ))

    conn.commit()

    conn.close()


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def main_keyboard():

    keyboard = [

        [
            KeyboardButton(
                "📝 Ro‘yxatdan o‘tish"
            )
        ],

        [
            KeyboardButton(
                "👨‍💼 Operator bilan bog‘lanish"
            )
        ]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# ============================================================
# КНОПКА ТЕЛЕФОНА
# ============================================================

def phone_keyboard():

    keyboard = [

        [
            KeyboardButton(
                "📱 Telefon raqamimni yuborish",
                request_contact=True
            )
        ]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ============================================================
# КНОПКА ОПЕРАТОРА
# ============================================================

def operator_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "👨‍💼 Operator bilan bog‘lanish",
                url=OPERATOR_URL
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# КНОПКА ОПЕРАТОРА ДЛЯ РАССЫЛКИ
# ============================================================

def broadcast_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "👨‍💼 Operator bilan bog‘lanish",
                url=OPERATOR_URL
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    save_user(user)

    context.user_data.clear()

    await update.message.reply_text(

        "Assalomu alaykum! 👋\n\n"

        "RADIUS kompaniyasining "
        "rasmiy botiga xush kelibsiz! 🛍️\n\n"

        "Yangiliklar, aksiyalar va "
        "chegirmalardan birinchilardan "
        "bo‘lib xabardor bo‘lish uchun "
        "ro‘yxatdan o‘ting. 🔥\n\n"

        "Kerakli bo‘limni tanlang 👇",

        reply_markup=main_keyboard()

    )


# ============================================================
# НАЧАЛО РЕГИСТРАЦИИ
# ============================================================

async def start_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data[
        "registration"
    ] = True

    context.user_data[
        "step"
    ] = "name"

    await update.message.reply_text(

        "📝 RADIUS RO‘YXATDAN O‘TISH\n\n"

        "Sizni ro‘yxatdan o‘tkazamiz. ✅\n\n"

        "1️⃣ Ismingizni yozing:",

        reply_markup=ReplyKeyboardRemove()

    )


# ============================================================
# ОПЕРАТОР
# ============================================================

async def operator(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "👨‍💼 Operator bilan bog‘lanish\n\n"

        "Savollaringiz bo‘lsa, "
        "operatorimiz bilan bog‘lanishingiz mumkin.",

        reply_markup=operator_keyboard()

    )


# ============================================================
# ОБРАБОТКА ТЕКСТА
# ============================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    text = update.message.text


    # ========================================================
    # ГЛАВНОЕ МЕНЮ
    # ========================================================

    if text == "📝 Ro‘yxatdan o‘tish":

        await start_registration(
            update,
            context
        )

        return


    if text == "👨‍💼 Operator bilan bog‘lanish":

        await operator(
            update,
            context
        )

        return


    # ========================================================
    # РАССЫЛКА
    # ========================================================

    if context.user_data.get(
        "broadcast_mode"
    ):

        if user.id != ADMIN_ID:

            return

        context.user_data[
            "broadcast_text"
        ] = text

        users = get_active_users()

        count = len(users)

        keyboard = [

            [
                InlineKeyboardButton(
                    "✅ Отправить всем",
                    callback_data="confirm_broadcast"
                )
            ],

            [
                InlineKeyboardButton(
                    "❌ Отмена",
                    callback_data="cancel_broadcast"
                )
            ]

        ]

        await update.message.reply_text(

            "📢 PREVIEW АКЦИИ / СКИДКИ\n\n"

            f"{text}\n\n"

            "━━━━━━━━━━━━━━\n"

            f"👥 Получателей: {count}\n\n"

            "Отправить сообщение всем?",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # ========================================================
    # РЕГИСТРАЦИЯ
    # ========================================================

    if context.user_data.get(
        "registration"
    ):

        step = context.user_data.get(
            "step"
        )


        # ====================================================
        # ИМЯ
        # ====================================================

        if step == "name":

            context.user_data[
                "name"
            ] = text

            context.user_data[
                "step"
            ] = "city"

            await update.message.reply_text(

                "2️⃣ Qaysi shahar/tumanda yashaysiz?"

            )

            return


        # ====================================================
        # ГОРОД / РАЙОН
        # ====================================================

        if step == "city":

            context.user_data[
                "city"
            ] = text

            save_city(
                user.id,
                text
            )

            context.user_data[
                "step"
            ] = "phone"

            await update.message.reply_text(

                "3️⃣ Telefon raqamingizni yuboring 📱\n\n"

                "Quyidagi tugmani bosing:",

                reply_markup=phone_keyboard()

            )

            return


        # ====================================================
        # МЕНЕДЖЕР
        # ====================================================

        if step == "manager":

            manager_name = text

            context.user_data[
                "manager"
            ] = manager_name

            save_manager(
                user.id,
                manager_name
            )

            await finish_registration(
                update,
                context
            )

            return


    # ========================================================
    # НЕИЗВЕСТНОЕ СООБЩЕНИЕ
    # ========================================================

    await update.message.reply_text(

        "Iltimos, menyudan kerakli "
        "bo‘limni tanlang 👇",

        reply_markup=main_keyboard()

    )


# ============================================================
# ОБРАБОТКА ТЕЛЕФОНА
# ============================================================

async def contact_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    contact = update.message.contact


    # ========================================================
    # ПРОВЕРКА ВЛАДЕЛЬЦА НОМЕРА
    # ========================================================

    if contact.user_id != user.id:

        await update.message.reply_text(

            "❌ Iltimos, faqat o‘zingizning "
            "telefon raqamingizni yuboring.\n\n"

            "Quyidagi tugmani bosing 👇",

            reply_markup=phone_keyboard()

        )

        return


    # ========================================================
    # ПРОВЕРКА РЕГИСТРАЦИИ
    # ========================================================

    if not context.user_data.get(
        "registration"
    ):

        await update.message.reply_text(

            "Iltimos, avval ro‘yxatdan o‘ting.",

            reply_markup=main_keyboard()

        )

        return


    if context.user_data.get(
        "step"
    ) != "phone":

        return


    # ========================================================
    # СОХРАНЯЕМ ТЕЛЕФОН
    # ========================================================

    phone = contact.phone_number

    save_phone(
        user.id,
        phone
    )

    context.user_data[
        "phone"
    ] = phone


    # ========================================================
    # ПЕРЕХОД К ВОПРОСУ О МЕНЕДЖЕРЕ
    # ========================================================

    context.user_data[
        "step"
    ] = "manager"


    await update.message.reply_text(

        "4️⃣ Sizga qaysi menejer xizmat ko‘rsatdi?\n\n"

        "✍️ Menejer ismini yozing:",

        reply_markup=ReplyKeyboardRemove()

    )


# ============================================================
# ЗАВЕРШЕНИЕ РЕГИСТРАЦИИ
# ============================================================

async def finish_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    # ========================================================
    # ПОЛУЧАЕМ ДАННЫЕ
    # ========================================================

    name = context.user_data.get(
        "name",
        "Noma'lum"
    )

    city = context.user_data.get(
        "city",
        "Noma'lum"
    )

    phone = context.user_data.get(
        "phone",
        "Noma'lum"
    )

    manager_name = context.user_data.get(
        "manager",
        "Noma'lum"
    )

    username = (

        f"@{user.username}"

        if user.username

        else "Username yo‘q"

    )


    # ========================================================
    # УВЕДОМЛЕНИЕ АДМИНИСТРАТОРУ
    # ========================================================

    admin_message = (

        "🆕 YANGI REGISTRATSIYA!\n\n"

        "🏢 RADIUS\n\n"

        f"👤 Ism: {name}\n"

        f"📍 Shahar/tuman: {city}\n"

        f"📱 Telefon: {phone}\n"

        f"👨‍💼 Menejer: {manager_name}\n\n"

        f"👤 Username: {username}\n"

        f"🆔 Telegram ID: {user.id}"

    )


    try:

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=admin_message

        )

        logger.info(
            f"Registration notification sent: {user.id}"
        )

    except Exception as error:

        logger.error(

            f"Admin notification error: {error}"

        )


    # ========================================================
    # ОЧИЩАЕМ СОСТОЯНИЕ
    # ========================================================

    context.user_data.clear()


    # ========================================================
    # ПОЗДРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # ========================================================

    await update.message.reply_text(

        "🎉 Tabriklaymiz!\n\n"

        "Siz RADIUS kompaniyasida "
        "muvaffaqiyatli ro‘yxatdan o‘tdingiz! ✅\n\n"

        "Endi siz eng so‘nggi aksiyalar, "
        "chegirmalar va maxsus takliflardan "
        "birinchilardan bo‘lib xabardor bo‘lasiz! 🛍️🔥",

        reply_markup=main_keyboard()

    )


    # ========================================================
    # ОТПРАВЛЯЕМ ТОЧКУ RADIUS
    # ========================================================

    await update.message.reply_location(

        latitude=RADIUS_LATITUDE,

        longitude=RADIUS_LONGITUDE

    )


# ============================================================
# /BROADCAST
# ============================================================

async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        await update.message.reply_text(

            "❌ Sizda ruxsat yo‘q."

        )

        return


    context.user_data[
        "broadcast_mode"
    ] = True


    await update.message.reply_text(

        "📢 AKSIYA / CHEGIRMA RASSYLKASI\n\n"

        "Yuboriladigan xabarni yuboring.\n\n"

        "❌ Bekor qilish uchun /cancel yozing."

    )


# ============================================================
# /CANCEL
# ============================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id == ADMIN_ID:

        context.user_data.clear()

        await update.message.reply_text(

            "❌ Rassylka bekor qilindi.",

            reply_markup=main_keyboard()

        )


# ============================================================
# /USERS
# ============================================================

async def users_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        return


    total, active, blocked = get_user_stats()


    await update.message.reply_text(

        "👥 RADIUS FOYDALANUVCHILARI\n\n"

        f"👥 Jami: {total}\n"

        f"🟢 Faol: {active}\n"

        f"🔴 Bloklagan: {blocked}\n\n"

        f"🆔 Admin ID: {ADMIN_ID}"

    )


# ============================================================
# /TEST_BROADCAST
# ============================================================

async def test_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user.id != ADMIN_ID:

        return


    await context.bot.send_message(

        chat_id=ADMIN_ID,

        text=(

            "🧪 TEST AKSIYA XABARI\n\n"

            "Bu test xabari. Agar siz uni "
            "ko‘rsangiz, reklama va aksiya "
            "rassylkasi ishlayapti. ✅"

        ),

        reply_markup=broadcast_keyboard()

    )


# ============================================================
# CALLBACK-КНОПКИ
# ============================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    # ========================================================
    # ПОДТВЕРЖДЕНИЕ РАССЫЛКИ
    # ========================================================

    if query.data == "confirm_broadcast":

        if query.from_user.id != ADMIN_ID:

            return


        message_text = context.user_data.get(
            "broadcast_text"
        )


        if not message_text:

            await query.edit_message_text(

                "❌ Xabar topilmadi."

            )

            return


        users = get_active_users()


        success = 0

        failed = 0

        blocked = 0


        await query.edit_message_text(

            "📢 Rassylka boshlandi...\n\n"

            f"👥 Jami: {len(users)}"

        )


        for user_id in users:

            try:

                await context.bot.send_message(

                    chat_id=user_id,

                    text=message_text,

                    reply_markup=broadcast_keyboard()

                )

                success += 1


                await asyncio.sleep(
                    0.05
                )


            except Exception as error:

                failed += 1

                error_text = str(
                    error
                ).lower()


                if (

                    "blocked" in error_text

                    or

                    "deactivated" in error_text

                    or

                    "chat not found" in error_text

                ):

                    mark_blocked(
                        user_id
                    )

                    blocked += 1


                logger.error(

                    f"Broadcast error "
                    f"for {user_id}: {error}"

                )


        context.user_data.clear()


        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(

                "✅ RASSYLKA YAKUNLANDI!\n\n"

                f"👥 Jami: {len(users)}\n"

                f"📨 Yuborildi: {success}\n"

                f"❌ Xatolik: {failed}\n"

                f"🚫 Bloklaganlar: {blocked}"

            ),

            reply_markup=main_keyboard()

        )

        return


    # ========================================================
    # ОТМЕНА РАССЫЛКИ
    # ========================================================

    if query.data == "cancel_broadcast":

        context.user_data.clear()


        await query.edit_message_text(

            "❌ Rassylka bekor qilindi."

        )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(

            "BOT_TOKEN topilmadi. "
            "Replit Secrets ga BOT_TOKEN qo‘shing."

        )


    if not ADMIN_ID:

        raise ValueError(

            "ADMIN_ID topilmadi. "
            "Replit Secrets ga ADMIN_ID qo‘shing."

        )


    # Инициализация базы

    init_database()


    # Создание приложения

    application = (

        Application.builder()

        .token(BOT_TOKEN)

        .build()

    )


    # ========================================================
    # КОМАНДЫ
    # ========================================================

    application.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    application.add_handler(

        CommandHandler(
            "broadcast",
            broadcast
        )

    )


    application.add_handler(

        CommandHandler(
            "users",
            users_command
        )

    )


    application.add_handler(

        CommandHandler(
            "test_broadcast",
            test_broadcast
        )

    )


    application.add_handler(

        CommandHandler(
            "cancel",
            cancel
        )

    )


    # ========================================================
    # ТЕЛЕФОН
    # ========================================================

    application.add_handler(

        MessageHandler(

            filters.CONTACT,

            contact_handler

        )

    )


    # ========================================================
    # INLINE-КНОПКИ
    # ========================================================

    application.add_handler(

        CallbackQueryHandler(

            callback_handler

        )

    )


    # ========================================================
    # ТЕКСТ
    # ========================================================

    application.add_handler(

        MessageHandler(

            filters.TEXT
            & ~filters.COMMAND,

            message_handler

        )

    )


    logger.info(
        "RADIUS BOT IS RUNNING..."
    )


    application.run_polling()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()