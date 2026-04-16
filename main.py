import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class RegistrationStates(StatesGroup):
    full_name = State()
    phone_number = State()
    address = State()

class TelegramMultimediaBot:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN not found in environment variables")
        
        self.bot = Bot(token=self.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.users_file = "users.json"
        
        self.setup_handlers()
    
    def load_users(self):
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_users(self, users):
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    def get_user(self, chat_id):
        users = self.load_users()
        for user in users:
            if user['chat_id'] == str(chat_id):
                return user
        return None
    
    def add_user(self, chat_id, full_name, phone_number, address):
        users = self.load_users()
        users.append({
            'chat_id': str(chat_id),
            'full_name': full_name,
            'phone_number': phone_number,
            'address': address
        })
        self.save_users(users)
    
    def get_main_keyboard(self):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Video"), KeyboardButton(text="Image")],
                [KeyboardButton(text="PDF Document"), KeyboardButton(text="Audio")],
                [KeyboardButton(text="About Bot"), KeyboardButton(text="User Info")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Choose an option..."
        )
        return keyboard
    
    def setup_handlers(self):
        @self.dp.message(CommandStart())
        async def handle_start(message: Message, state: FSMContext):
            chat_id = message.chat.id
            user = self.get_user(chat_id)
            
            if user:
                await message.answer(
                    f"Welcome back, {user['full_name']}! You are already registered.",
                    reply_markup=self.get_main_keyboard()
                )
                await state.clear()
            else:
                await message.answer(
                    "Welcome to the Telegram Multimedia Bot! Please register first.\n"
                    "What is your full name?",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                await state.set_state(RegistrationStates.full_name)
        
        @self.dp.message(RegistrationStates.full_name)
        async def process_full_name(message: Message, state: FSMContext):
            full_name = message.text.strip()
            if len(full_name) < 2:
                await message.answer("Please enter a valid full name (at least 2 characters):")
                return
            
            await state.update_data(full_name=full_name)
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]],
                resize_keyboard=True
            )
            await message.answer("Telefon raqamingizni ulashing:", reply_markup=keyboard)
            await state.set_state(RegistrationStates.phone_number)
        
        @self.dp.message(RegistrationStates.phone_number, F.contact)
        async def process_phone_contact(message: Message, state: FSMContext):
            phone_number = message.contact.phone_number
            await state.update_data(phone_number=phone_number)
            await message.answer("Rahmat! Endi manzilingizni kiriting:", reply_markup=types.ReplyKeyboardRemove())
            await state.set_state(RegistrationStates.address)
        
        @self.dp.message(RegistrationStates.phone_number)
        async def process_phone_number(message: Message, state: FSMContext):
            phone_number = message.text.strip()
            
            if not phone_number.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                await message.answer("Iltimos, to'g'ri telefon raqamini kiriting:")
                return
            
            await state.update_data(phone_number=phone_number)
            await message.answer("Perfect! Finally, please enter your address:")
            await state.set_state(RegistrationStates.address)
        
        @self.dp.message(RegistrationStates.address)
        async def process_address(message: Message, state: FSMContext):
            address = message.text.strip()
            if len(address) < 5:
                await message.answer("Please enter a valid address (at least 5 characters):")
                return
            
            user_data = await state.get_data()
            chat_id = message.chat.id
            
            self.add_user(
                chat_id,
                user_data['full_name'],
                user_data['phone_number'],
                address
            )
            
            await message.answer(
                f"Thank you for registering, {user_data['full_name']}! You can now use all bot features.",
                reply_markup=self.get_main_keyboard()
            )
            await state.clear()
        
        @self.dp.message(F.text == "Video")
        async def send_video(message: Message):
            video_url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
            try:
                await message.answer("Here's a sample video for you:")
                await message.answer_video(
                    video=video_url,
                    caption="Sample Video - Multimedia Content"
                )
            except Exception as e:
                await message.answer("Sorry, I couldn't send the video. Please try again later.")
                logger.error(f"Error sending video: {e}")
        
        @self.dp.message(F.text == "Image")
        async def send_image(message: Message):
            image_url = "https://picsum.photos/800/600"
            try:
                await message.answer("Here's a sample image for you:")
                await message.answer_photo(
                    photo=image_url,
                    caption="Sample Image - Multimedia Content"
                )
            except Exception as e:
                await message.answer("Sorry, I couldn't send the image. Please try again later.")
                logger.error(f"Error sending image: {e}")
        
        @self.dp.message(F.text == "PDF Document")
        async def send_pdf(message: Message):
            pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            try:
                await message.answer("Here's a sample PDF document for you:")
                await message.answer_document(
                    document=pdf_url,
                    caption="Sample PDF Document - Multimedia Content"
                )
            except Exception as e:
                await message.answer("Sorry, I couldn't send the PDF document. Please try again later.")
                logger.error(f"Error sending PDF: {e}")
        
        @self.dp.message(F.text == "Audio")
        async def send_audio(message: Message):
            audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
            try:
                await message.answer("Here's a sample audio file for you:")
                await message.answer_audio(
                    audio=audio_url,
                    title="Sample Audio",
                    performer="Multimedia Bot"
                )
            except Exception as e:
                await message.answer("Sorry, I couldn't send the audio file. Please try again later.")
                logger.error(f"Error sending audio: {e}")
        
        @self.dp.message(F.text == "About Bot")
        async def about_bot(message: Message):
            about_text = """
*Telegram Multimedia Bot* v1.0

This is a comprehensive multimedia bot that provides:
- Video sharing
- Image sharing
- PDF document sharing
- Audio file sharing
- User registration and management

Features:
- User registration with FSM
- Persistent user data storage
- Multimedia content delivery
- User-friendly keyboard interface

Created for demonstration purposes.
            """
            await message.answer(
                about_text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        @self.dp.message(F.text == "User Info")
        async def user_info(message: Message):
            chat_id = message.chat.id
            user = self.get_user(chat_id)
            
            if user:
                info_text = f"""
*Your User Information:*

*Full Name:* {user['full_name']}
*Phone Number:* {user['phone_number']}
*Address:* {user['address']}
*Chat ID:* {user['chat_id']}

Registration completed successfully!
                """
                await message.answer(
                    info_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await message.answer(
                    "You are not registered yet. Please use /start to register first."
                )
        
        @self.dp.message()
        async def handle_unknown_messages(message: Message):
            await message.answer(
                "Please use the keyboard buttons or /start command to interact with the bot.",
                reply_markup=self.get_main_keyboard()
            )
    
    async def run(self):
        logger.info("bot ishlamoqda")
        logger.info("Starting Telegram Multimedia Bot...")
        await self.dp.start_polling(self.bot)

def main():
    try:
        bot = TelegramMultimediaBot()
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
    finally:
        logger.info("bot toxtadi")

if __name__ == "__main__":
    main()
