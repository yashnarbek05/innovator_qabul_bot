import logging
import os
import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler, CallbackContext,
)

from bot.models.user import User
from config import GROUP_CHAT_ID, SHEET_NAME
from image.service import prepare_badge
from sheet.service import get_values_from_sheet, update_allowing, update_given, write_part_id, write_user_info_to_sheet

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

LANGUAGE, FULLNAME, NUMBER, AGE, WORK, GMAIL, HUDUD, DIRECTION, OFFERS, PHOTO, REGENERATE, PHOTO_TO_REGENERATE = range(0, 12)


users_apply_certificate = list()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    keyboard = [
        [InlineKeyboardButton("English🇺🇸", callback_data="en")],
        [InlineKeyboardButton("O'zbek🇺🇿", callback_data="uz")],
        [InlineKeyboardButton("Русский🇷🇺", callback_data="ru")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Tilni tanlang:", reply_markup=reply_markup)

    return LANGUAGE


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer("Progress...")
    

    keyboard = [[KeyboardButton("📞 Share Your Number", request_contact=True)]]
    reply_markup1 = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


    messages = {
        'en': f"Hello, {query.from_user.first_name}! Share your number:",
        'ru': f"Здравствуйте, {query.from_user.first_name}! Поделитесь своим номером:",
        'uz': f"Assalomu alaykum, {query.from_user.first_name}! Raqamingizni ulashing:"
    }

    
    await query.message.reply_text(text = messages.get(query.data), reply_markup=reply_markup1)

    context.user_data['language'] = query.data

    return NUMBER


async def receive_number(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact

    requested = any(contact.phone_number == userr.get_number() for userr in
                    users_apply_certificate)

    if requested:
        messages = {
            'uz': "Sizning ma'lumotlaringiz allaqachon adminlarga yuborildi, iltimos ularning javobini kuting😐",
            'ru': "Ваша информация уже отправлена администраторам, дождитесь ответа😐",
            'en': "Your information has already been sent to the admins, please wait for their response😐"
        }

        await update.message.reply_text(messages.get(context.user_data.get('language')))
        return ConversationHandler.END


    new_datas = await get_values_from_sheet(SHEET_NAME)

    for i in range(1, len(new_datas)):
        user_from_excel = new_datas[i]
        if (contact.phone_number == user_from_excel[0] and
                (len(user_from_excel) <= 8 or user_from_excel[9] == 'FALSE') and  # is_given
                (len(user_from_excel) <= 9 or user_from_excel[10] == 'FALSE')  # is_allowed
        ):

            messages = {
                'en': f"Enter your first and last name to register!",
                'ru': f"Введите свое имя и фамилию для регистрации!",
                'uz': f"Roʻyxatdan oʻtish uchun ism va familiyangizni kiriting!"
            }
    
    
            context.user_data["number"] = contact.phone_number
    
            await update.message.reply_text(messages.get(context.user_data.get('language')), reply_markup=ReplyKeyboardRemove())

            return FULLNAME

        elif (contact.phone_number == user_from_excel[0]
              and user_from_excel[9] == 'TRUE'  # is_given
        ):
            messages = {
                'uz': "Men sizning guvohnomangizni allaqachon yaratdim, agar qayta tiklamoqchi bo'lsangiz, \n/regenerate yuboring...",
                'ru': 'Я уже создал ваш бежик, отправьте \n/regenerate, если хотите восстановить…',
                'en': "I generated your badge already, send \n/regenerate if you want regenerate..."
            }

            await update.message.reply_text(
                messages.get(context.user_data.get('language'))
            )

            context.user_data['fullname'] = user_from_excel[2]
            context.user_data['part_id'] = user_from_excel[12]

            new_datas.clear()

            return REGENERATE



    messages = {
        'en': f"Enter your first and last name to register!",
        'ru': f"Введите свое имя и фамилию для регистрации!",
        'uz': f"Roʻyxatdan oʻtish uchun ism va familiyangizni kiriting!"
    }
    
    
    context.user_data["number"] = contact.phone_number
    
    await update.message.reply_text(messages.get(context.user_data.get('language')), reply_markup=ReplyKeyboardRemove())

    return FULLNAME

def clear_datas(context):
    context.chat_data.clear()
    context.user_data.clear()


async def fullname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_fullname = update.message.text

    result = all(not char.isdigit() for char in user_fullname)

    if not result:
        messages = {
            'uz': f"Siz to'liq ismingizni noto'g'ri kiritdingiz, \"{user_fullname}\"😕, \nqayta yuboring...",
            'ru': f"Вы неправильно ввели свое полное имя: \"{user_fullname}\"😕, \nотправьте еще раз...",
            'en': f"You have entered your full name incorrectly: \"{user_fullname}\"😕, \nsend again..."
        }
        await update.message.reply_text(messages.get(context.user_data.get('language')))
        return FULLNAME

    requested = any(int(user.id) == int(userr.get_chat_id()) or user_fullname == userr.get_fullname() for userr in
                    users_apply_certificate)

    if requested:
        messages = {
            'uz': "Sizning ma'lumotlaringiz allaqachon adminlarga yuborildi, iltimos ularning javobini kuting😐",
            'ru': "Ваша информация уже отправлена администраторам, дождитесь ответа😐",
            'en': "Your information has already been sent to the admins, please wait for their response😐"
        }

        await update.message.reply_text(messages.get(context.user_data.get('language')))
        return ConversationHandler.END

    context.user_data["fullname"] = user_fullname

    messages = {
        'en': f"Enter your age!",
        'ru': f"Введите свой возраст!",
        'uz': f"Yoshingizni kiriting!"
    }

    
    await update.message.reply_text(messages.get(context.user_data.get('language')))

    return AGE


async def age(update: Update, context: CallbackContext) -> None:
    age = update.message.text

    if not age.isdigit() or int(age) < 0:
        messages = {
        'en': f"Please enter the correct number!",
        'ru': f"Пожалуйста, введите правильный номер!",
        'uz': f"Iltimos to'g'ri son kiriting!"
        }
        
    
        await update.message.reply_text(messages.get(context.user_data.get('language')))

        return AGE

    messages = {
        'en': f"Enter your place of study or work!",
        'ru': f"Введите место учебы или работы!",
        'uz': f"Oʻqish yoki ish joyingizni kiriting!"
    }

    context.user_data["age"] = int(age)
    
    await update.message.reply_text(messages.get(context.user_data.get('language')))

    return WORK


async def work(update: Update, context: CallbackContext) -> None:
    work = update.message.text

    context.user_data["work"] = work.strip()

    messages = {
        'en': f"Enter your email!",
        'ru': f"Введите свой адрес электронной почты!",
        'uz': f"Elektron pochtangizni kiriting!"
    }
    
    await update.message.reply_text(messages.get(context.user_data.get('language')))

    return GMAIL


async def gmail(update: Update, context: CallbackContext) -> None:
    gmail = update.message.text


    if not re.match("^[a-zA-Z0-9._%+-]+@gmail\.com$", gmail.strip()):
        messages = {
        'en': f"Please enter your email address correctly!",
        'ru': f"Пожалуйста, введите адрес электронной почты правильно!",
        'uz': f"Elektron pochtangizni to'g'ri kiriting!"
        }
    
        await update.message.reply_text(messages.get(context.user_data.get('language')))

        return GMAIL



    context.user_data["gmail"] = gmail.strip()

    keyboard = [
        [KeyboardButton("Toshkent shahar")],
        [KeyboardButton("Toshkent viloyati"), KeyboardButton("Andijon viloyati")],
        [KeyboardButton("Surxondaryo viloyati"), KeyboardButton("Sirdaryo viloyati")],
        [KeyboardButton("Samarqand viloyati"), KeyboardButton("Qashqadaryo viloyati")],
        [KeyboardButton("Navoiy viloyati"), KeyboardButton("Namangan viloyati")],
        [KeyboardButton("Xorazm viloyati"), KeyboardButton("Jizzax viloyati")],
        [KeyboardButton("Farg‘ona viloyati"), KeyboardButton("Buxoro viloyati")],
        [KeyboardButton("Farg‘ona viloyati"), KeyboardButton("Buxoro viloyati")],
        [KeyboardButton("Qoraqalpog‘iston Respublikasi")],
                
                
    ]
    reply_markup1 = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


    messages = {
        'en': f"Select your region:",
        'ru': f"Выберите свой регион:",
        'uz': f"Hududingizni tanlang:"
    }

    
    await update.message.reply_text(text = messages.get(context.user_data.get('language')), reply_markup=reply_markup1)

    return HUDUD

async def hudud(update: Update, context: CallbackContext) -> None:
    hudud = update.message.text


    context.user_data["hudud"] = hudud

    keyboard = [
        [KeyboardButton("  SOCIAL MEDIA MARKETING")],
        [KeyboardButton("  ROBOTOTEXNOLOGIYA")],
        [KeyboardButton("  FRILIANSERLIK ISTIQBOLLARI")],
        [KeyboardButton("   IJTIMOIY START-UPLAR YARATISH")],
        [KeyboardButton("  SUNʼIY INTELLEKT")],
                
                
    ]
    reply_markup1 = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


    messages = {
        'en': f"Choose a forum direction!",
        'ru': f"Выбирайте направление форума!",
        'uz': f"Forum yoʻnalishini tanlang!"
    }

    
    await update.message.reply_text(text = messages.get(context.user_data.get('language')), reply_markup=reply_markup1)

    return DIRECTION

async def direction(update: Update, context: CallbackContext) -> None:
    direction = update.message.text


    context.user_data["direction"] = direction

    messages = {
        'en': f"What suggestions do you have and what kind of project do you want to promote?",
        'ru': f"Какие у вас есть предложения и какой проект вы хотите продвигать?",
        'uz': f"Qanday takliflaringiz bor va siz tomoningizdan qanday loyihani ilgari surmoqchisiz?"
    }
    
    await update.message.reply_text(messages.get(context.user_data.get('language')), reply_markup=ReplyKeyboardRemove())

    return OFFERS

async def offers(update: Update, context: CallbackContext) -> None:
    offers = update.message.text


    context.user_data["offers"] = offers

    messages = {
                'uz': "Sizning roʻyxatdan oʻtganingiz tasdiqlandi. Bizga rasmiy rasmingizni yuboring.\nRasm talablari:\n1. Tiniq va yuz qism toʻliq tushsin.\n2. Rasm oʻlchamiga eʼtibor bering. \n3. Yoki namunaga qarang",
                'ru': 'Ваша регистрация подтверждена. Пожалуйста, пришлите нам свою официальную фотографию.\nТребования к фотографии:\n1. Четкое и анфас.\n2. Обратите внимание на размер фотографии. \n3. Или посмотрите образец',
                'en': "Your registration has been confirmed. Please send us your official photo.\nPhoto requirements:\n1. Clear and full face.\n2. Pay attention to the size of the photo. \n3. Or see a sample"
            }

    await update.message.reply_photo("images/example_avatar_photo.png",
                                             caption=messages.get(context.user_data.get('language'))
                                             )
    
    return PHOTO


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive(f"images/user_photo/{context.user_data.get('fullname')}.jpg")

    from datetime import datetime

    now = datetime.now()  # Get current date and time
    formatted_time = now.strftime("%B %d, %H:%M:%S")


    caption = (f"New forum participate🥳 \n\nuser-id: "
               + f"`{update.effective_user.id}`"
               + f"\nfull-name: {context.user_data.get('fullname')}"
                 f"\nJoined: {formatted_time}")

    with open(f"images/user_photo/{context.user_data.get('fullname')}.jpg", "rb") as photo:
        keyboard = [
            [InlineKeyboardButton("✅", callback_data=f"{update.effective_user.id} ✅"),
             InlineKeyboardButton("❌", callback_data=f"{update.effective_user.id} ❌")],
            [InlineKeyboardButton('ℹ️', callback_data=f'{update.effective_user.id} ℹ️')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=photo, caption=caption, parse_mode='Markdown',
                                     reply_markup=reply_markup)


    messages = {
        'uz': "Ajoyib! Endi maʼlumotlaringizni adminlarga joʻnatdim, ruxsat berishsa tez orada guvohnomangizni yuboraman. Meni kuting...",
        'ru': "Отлично! Теперь я отправил ваши данные администраторам, если они мне позволят, то пришлю ваши бежик в ближайшее время. Подождите меня...",
        'en': "Great! Now I've sent your details to the admins, I'll send your credentials soon if they'll let me. Wait for me..."
    }

    await update.message.reply_text(
        messages.get(context.user_data.get('language'))
    )

    users_apply_certificate.append(User(update.effective_user.id,
                                        formatted_time,
                                        context.user_data.get("number"),
                                        context.user_data.get("fullname"),
                                        context.user_data.get("age"),
                                        context.user_data.get("work"),
                                        context.user_data.get("gmail"),
                                        context.user_data.get('hudud'),
                                        context.user_data.get("direction"),
                                        f"images/user_photo/{context.user_data.get('fullname')}.jpg", 
                                        context.user_data.get("offers"),
                                        context.user_data.get("language")))

    return ConversationHandler.END


async def error_handler(update: Update, context: CallbackContext):
    """Log the error and send a message to the user."""
    # Log the error
    logger.error(f"Exception occurred: {context.error}")
    await context.bot.send_message(chat_id=GROUP_CHAT_ID,
                                   text=f"Xatolik yuz berdi😢: \n\n{context.error}")
    

async def cancel(update: Update, context: CallbackContext):
    messages = {
        'uz': 'Bekor qilindi!',
        'ru': 'Отменено!',
        'en': 'Cancelled!'
    }
    await update.message.reply_text(messages.get(context.user_data.get('language')))
    clear_datas(context)
    return ConversationHandler.END


async def design_user_data(datas):
    text = ""
    for i in range(1, len(datas) + 1):
        text = text + f"{i}) " + str(datas[i - 1]) + "\n\n"

    return text



async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query


    await query.answer("Progress...")

    query_splited = query.data.split(" ")

    new_datas = await get_values_from_sheet(SHEET_NAME)


    user = ""
    for i in range(len(users_apply_certificate)):


        user = users_apply_certificate[i]

        if str(query_splited[0]) == str(user.get_chat_id()):


            if query_splited[1] == "✅":
                await write_user_info_to_sheet(len(new_datas), user, SHEET_NAME)
                await update_allowing(len(new_datas), True, SHEET_NAME)

                await context.bot.send_message(chat_id=GROUP_CHAT_ID,
                                               text=f"{update.effective_user.first_name} tomonidan {user.get_fullname()} ga guvohnoma olishiga ruxsat berildi✅")

                photo_name = await prepare_badge(user.get_fullname(),
                                                 len(new_datas),
                                                 user.get_user_photo())

                with open(photo_name, "rb") as prepared_badge:
                    logging.info("Photo opened for sending to user!")

                    messages = {
                        'uz': "Tabriklaymiz🎉, Sizning  guvohnomangiz tayyor boʻldi va  muvaffaqiyatli roʻyxatdan oʻtingiz. Yosh innovatorlar forumi 3-mavsumida faol ishtirok etishingizni tilaymiz.\nYanada koʻproq maʼlumotni shu yerdan oling: https://ezgu.uz/",
                        'ru': 'Поздравляем🎉, ваш ID готов и вы успешно зарегистрировались. Желаем вам активного участия в 3-м сезоне Форума молодых инноваторов.\nБолее подробную информацию можно получить здесь: https://ezgu.uz/',
                        'en': "Congratulations🎉, Your ID is ready and you have successfully registered. We wish you active participation in the 3rd season of the Young Innovators Forum.\nGet more information here: https://ezgu.uz/"
                    }

                    await context.bot.send_photo(chat_id=user.get_chat_id(),
                                                 photo=prepared_badge,
                                                 caption=messages.get(user.get_language()))

                    await update_given(len(new_datas), True, SHEET_NAME)
                    await write_part_id(len(new_datas), SHEET_NAME, str(len(new_datas)))
                    
                users_apply_certificate.pop(i)

                clear_datas(context)

                if os.path.exists(photo_name):
                    os.remove(photo_name)  # Delete the file
                    os.remove(user.get_user_photo())  # Delete the file
                else:
                    print(f"The file {photo_name} does not exist.")

                return

            elif query_splited[1] == "❌":

                context.chat_data["pending_rejection"] = user
                context.chat_data["user_list_index"] = i

                prompt_message = await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"Iltimos, {user.get_fullname()} ga nega ruxsat bermaganingizni sababini yozing(til: {user.get_language()}):"
                )

                context.chat_data["rejection_prompt_message_id"] = prompt_message.message_id
                return

            elif query_splited[1] == "ℹ️":
                designed_user_data = await design_user_data(user.to_list())
                await context.bot.send_message(GROUP_CHAT_ID, designed_user_data)
                return

    await context.bot.send_message(chat_id=GROUP_CHAT_ID,
                                   text=f"Bunday {query_splited[0]} idli odam topilmadi!")


async def capture_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not 'pending_rejection' in context.chat_data.keys(): return
    user = context.chat_data.get("pending_rejection")
    prompt_message_id = context.chat_data.get("rejection_prompt_message_id")

    # Validate the reply
    if not user.get_chat_id() or not prompt_message_id:
        await update.message.reply_text("No pending rejection reason.")
        return

    if not update.message.reply_to_message or update.message.reply_to_message.message_id != prompt_message_id:
        return

    # Save the reason and clear the state
    reason = update.message.text
    del context.chat_data["pending_rejection"]
    del context.chat_data["rejection_prompt_message_id"]

    # Notify the group and the user
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=f"{update.effective_user.first_name} tomonidan {user.get_fullname()} ga guvohnoma olishiga ruxsat berilmadi❌ \nsabab: " + reason
    )

    messages = {
        'uz': f"Uzur, sizning yuborgan ma'lumotlaringiz adminlar tomonidan rad etildi.\n{'' if not reason else 'sabab: ' + reason + "\n\nDavom etish uchun yana /start buyrug'ini yuboring"}",
        'ru': f"К сожалению, предоставленная вами информация была отклонена администраторами.\n{'' if not reason else 'причина: ' + reason + "\n\nOтправьте команду /start еще раз, чтобы продолжить"}",
        'en': f"Sorry, your submitted information has been rejected by admins.\n{'' if not reason else 'cause: ' + reason + "\n\nSend /start command again to continue"}"
    }

    await context.bot.send_message(chat_id=user.get_chat_id(),
                                   text=messages.get(user.get_language()))


    users_apply_certificate.pop(context.chat_data.get("user_list_index"))

    del context.chat_data["user_list_index"]

    if os.path.exists(user.get_user_photo()):
        os.remove(user.get_user_photo())
        clear_datas(context)
    else:
        print(f"The file {user.get_user_photo()} does not exist.")

    return


async def regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    messages = {
        'uz': "Bizga rasmiy rasmingizni yuboring.\nRasm talablari:\n1. Tiniq va yuz qism toʻliq tushsin.\n2. Rasm oʻlchamiga eʼtibor bering. \n3. Yoki namunaga qarang",
        'ru': 'Пожалуйста, пришлите нам свою официальную фотографию.\nТребования к фотографии:\n1. Четкое и анфас.\n2. Обратите внимание на размер фотографии. \n3. Или посмотрите образец',
        'en': "Please send us your official photo.\nPhoto requirements:\n1. Clear and full face.\n2. Pay attention to the size of the photo. \n3. Or see a sample"
    }

    await update.message.reply_photo("images/example_avatar_photo.png",
                                     caption=messages.get(context.user_data.get('language'))
                                     )
    return PHOTO_TO_REGENERATE


async def photo_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    messages = {
        'uz': "Iltimos kuting. Men sizning guvohnomangizni tayyorlayapman ...",
        'ru': "Пожалуйста, подождите. Я готовлю твой бежик...",
        'en': "Please wait. I am preparing your badge..."
    }
    await update.message.reply_text(
        messages.get(context.user_data.get('language'))
    )

    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive(f"images/user_photo/{context.user_data.get('fullname')}.jpg")

    photo_name = await prepare_badge(context.user_data.get('fullname'),
                                     str(context.user_data.get("part_id")),
                                     f"images/user_photo/{context.user_data.get('fullname')}.jpg")
    messages = {
        'uz': "Tabriklaymiz🎉, Sizning  guvohnomangiz tayyor boʻldi va  muvaffaqiyatli roʻyxatdan oʻtingiz. Yosh innovatorlar forumi 3-mavsumida faol ishtirok etishingizni tilaymiz.\nYanada koʻproq maʼlumotni shu yerdan oling: https://ezgu.uz/",
        'ru': 'Поздравляем🎉, ваш ID готов и вы успешно зарегистрировались. Желаем вам активного участия в 3-м сезоне Форума молодых инноваторов.\nБолее подробную информацию можно получить здесь: https://ezgu.uz/',
        'en': "Congratulations🎉, Your ID is ready and you have successfully registered. We wish you active participation in the 3rd season of the Young Innovators Forum.\nGet more information here: https://ezgu.uz/"
    }

    with open(photo_name, "rb") as prepared_badge:
        await update.message.reply_photo(prepared_badge,
                                         caption=messages.get(context.user_data.get('language')))

    if os.path.exists(photo_name):
        os.remove(photo_name)  # Delete the file
        os.remove(f"images/user_photo/{context.user_data.get('fullname')}.jpg")
    else:
        print(f"The file {photo_name} does not exist.")

    clear_datas(context)
    return ConversationHandler.END


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id,
                                   text="Uzur, bu bot sizning guruhingiz uchun emas!\nThis bot is not working in your group😣")
    await context.bot.leave_chat(update.message.chat_id)


async def alll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_CHAT_ID:
        await update.message.reply_text(GROUP_CHAT_ID, text=text, parse_mode="Markdown")

    text = "Guvohnoma olmoqchi bo'lgan volontiyorlar yoq!"

    if not users_apply_certificate:
        await context.bot.send_message(GROUP_CHAT_ID, text=text, parse_mode="Markdown")

    for volunteer in users_apply_certificate:
        text = (
            f"New volunteer🥳 \n\n"
            f"user-id: `{volunteer.get_chat_id()}`\n"
            f"full-name: {volunteer.get_fullname()}\n"
            f"Joined: {volunteer.get_time()}"
        )

        keyboard = [
            [InlineKeyboardButton("✅", callback_data=f"{volunteer.get_chat_id()} ✅"),
             InlineKeyboardButton("❌", callback_data=f"{volunteer.get_chat_id()} ❌")],
            [InlineKeyboardButton('ℹ️', callback_data=f'{volunteer.get_chat_id()} ℹ️')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text, parse_mode='Markdown',
                                       reply_markup=reply_markup)

    if users_apply_certificate:
        await context.bot.send_message(GROUP_CHAT_ID,
                                       f'{len(users_apply_certificate)} nafar volontiyorga javob berilmadi⁉️')


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != GROUP_CHAT_ID:
        await update.message.reply_text("Bu buyruq siz uchun emas!\nthis command is not for you!")
        return

    text = update.message.text


    if not re.match(r"^/search [0-9]+$" , text) and not re.match(r'^/search (?!.*\d).+$' , text):
        await context.bot.send_message(GROUP_CHAT_ID,
                                       f'Xato context kiritildi')
        return
    
    vol_id = text.split(' ', 1)[1]
    
        
    new_datas = await get_values_from_sheet(SHEET_NAME)


    for i in range(1, len(new_datas)):
        user_from_excel = new_datas[i]
        if (len(user_from_excel) == 12 and user_from_excel[11] == str(vol_id)) or str(vol_id) in user_from_excel[2].strip(): # volunteer_id
            designed_data = await design_user_data(user_from_excel)
            await context.bot.send_message(GROUP_CHAT_ID, designed_data)
            return
    
    
    new_datas.clear
    await context.bot.send_message(GROUP_CHAT_ID, f'Bunaqa volontiyor topilmadi!')

