from environs import Env
env = Env()
env.read_env()

import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from assistant import is_instagram, is_youtube, download_video, initialize_chrome_driver
from selenium.common.exceptions import TimeoutException
from pytube.exceptions import AgeRestrictedError

API_TOKEN = env.str("API_TOKEN")
MY_CHAT_ID = env.int("MY_CHAT_ID")
YOUTUBE_API_KEY = env.str("YOUTUBE_API_KEY")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def download_and_send_video(message: types.Message, loop):
    driver = initialize_chrome_driver()
    try:
        video_data, chat_action_task = await asyncio.gather(
            loop.run_in_executor(None, download_video, message.text, driver, YOUTUBE_API_KEY),
            bot.send_chat_action(MY_CHAT_ID, action="upload_video")
        )
        await bot.send_video(MY_CHAT_ID, video_data)
    except TimeoutException:
        await message.reply("Videoni yuklab bo‘lmadi\n\nBerilgan url haqiqiy ekanligiga ishonch hosil qiling !")
    except AgeRestrictedError:
        await message.reply("Bu video yoshlar uchun taqiqlangan va faqat kirish orqali ko‘rish mumkin.")
    except Exception as e:
        logging.error(f"Videoni yuklab olishda xatolik yuz berdi: {e}")
        await message.reply(f"Videoni yuklab olishda kutilmagan xatolik yuz berdi: {e}")
    finally:
        driver.quit()

@dp.message_handler(lambda message: message.chat.id == MY_CHAT_ID)
async def send_welcome(message: types.Message):
    if message.chat.id == MY_CHAT_ID:
        if not is_instagram(message.text) and not is_youtube(message.text):
            await message.reply("Qo'llab-quvvatlanmaydigan video platformasi yoki noto'g'ri URL")
        else:
            await message.reply("Iltimos kuting video yuklanmoqda...")
            tasks = [
                asyncio.create_task(download_and_send_video(message, loop)),
                asyncio.create_task(bot.send_chat_action(MY_CHAT_ID, action="upload_video"))
            ]
            await asyncio.gather(*tasks)

if __name__ == '__main__':
    from aiogram import executor
    loop = asyncio.get_event_loop()
    executor.start_polling(dp, loop=loop, skip_updates=True)
