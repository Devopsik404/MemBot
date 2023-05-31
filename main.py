import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

bot = Bot(token='6144098770:AAGEjPD4NfqYPBKZe-TANwyrFui88nmYuzs')
dp = Dispatcher(bot, storage=MemoryStorage())

class MemCreationStates(StatesGroup):
    WAITING_FOR_IMAGE = State()
    WAITING_FOR_CAPTION = State()

@dp.message_handler(Command('start'))
async def start_cmd_handler(message: types.Message):
    await message.answer('Привет! Я бот для создания мемов. Отправь мне изображение с командой /new_mem и я попрошу тебя ввести текст для мема.')

@dp.message_handler(Command('new_mem'))
async def new_mem_cmd_handler(message: types.Message):
    await message.answer('Пожалуйста, отправьте изображение.')
    await MemCreationStates.WAITING_FOR_IMAGE.set()
    
@dp.message_handler(content_types=types.ContentType.PHOTO, state=MemCreationStates.WAITING_FOR_IMAGE)
async def process_image(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    photo_bytes = await bot.download_file_by_id(photo.file_id)
    image = Image.open(photo_bytes)
    await message.answer('Пожалуйста, введите текст для мема.')
    await MemCreationStates.WAITING_FOR_CAPTION.set()
    await state.update_data(image=image)

@dp.message_handler(state=MemCreationStates.WAITING_FOR_CAPTION)
async def process_caption(message: types.Message, state: FSMContext):
    data = await state.get_data()
    image = data.get('image')
    if message.text:
        border_width = 10
        border_height = 50

        # Расчет размеров изображения внутри рамки
        image_width = image.width - 2 * border_width
        image_height = image.height - border_height - 2 * border_width
        aspect_ratio = image_width / image_height

        # Уменьшение изображения
        if aspect_ratio > 1:
            new_image_width = 500
            new_image_height = int(new_image_width / aspect_ratio)
        else:
            new_image_height = 500
            new_image_width = int(new_image_height * aspect_ratio)

        resized_image = image.resize((new_image_width, new_image_height), Image.ANTIALIAS)

        # Создание рамки
        border_color = 'black'
        border_image_width = new_image_width + 2 * border_width
        border_image_height = new_image_height + border_height + 2 * border_width
        border_image = Image.new('RGB', (border_image_width, border_image_height), border_color)
        border_image.paste(resized_image, ((border_image_width - new_image_width) // 2, border_width))

        # Добавление текста на рамку
        draw = ImageDraw.Draw(border_image)
        font = ImageFont.truetype('arial.ttf', size=25)
        text = message.text
        text_width, text_height = draw.textsize(text, font)
        text_position = ((border_image_width - text_width) // 2, new_image_height + border_width + (border_height - text_height) // 2)
        draw.text(text_position, text, fill='white', font=font)

        output = BytesIO()
        border_image.save(output, format='JPEG')
        output.seek(0)
        await bot.send_photo(message.chat.id, photo=output)
    else:
        await message.answer('Извините, я не получил текст. Пожалуйста, попробуйте еще раз.')
    await state.finish()



if __name__ == '__main__':
    executor.start_polling(dp)