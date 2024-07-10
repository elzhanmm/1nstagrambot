import logging
from instagrapi import Client
import time
import telebot
from telebot import apihelper, types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

apihelper.SESSION_TIME_TO_LIVE = 5 * 60
apihelper.TIMEOUT = 40

insta_bot = Client()

TELEGRAM_API_KEY = '6906802031:AAHztmYTHWMfGzLmzWgkHZ0ksjxufccz33U'
tg_bot = telebot.TeleBot(TELEGRAM_API_KEY)

instagram_username = None
instagram_password = None
pause_task = False
stop_task = False

def load_commented_posts(filename="commented_posts.txt"):
    try:
        with open(filename, "r") as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def save_commented_post(post_id, filename="commented_posts.txt"):
    with open(filename, "a") as file:
        file.write(post_id + "\n")

def follow_users_by_hashtag(hashtag, chat_id):
    tg_bot.send_message(chat_id, "Пожалуйста подождите я обрабатываю ваш хэштег")
    show_pause_stop_buttons(chat_id)
    global stop_task
    stop_task = False
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)
        for media in medias:
            if stop_task:
                break
            while pause_task:
                time.sleep(1)
            try:
                user_info = insta_bot.media_info(media.id).user
                insta_bot.user_follow(user_info.pk)
                output = f"Пользователь: {user_info.username}\nУспешная подписка"
                logger.info(output)
                tg_bot.send_message(chat_id, output)
                for _ in range(10):
                    if stop_task:
                        break
                    while pause_task:
                        time.sleep(1)
                    time.sleep(1)
            except Exception as e:
                error_output = f"Пользователь: {user_info.username}\nОшибка при подписке\Причина: {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)
            if stop_task:
                break
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Error fetching media: {e}")
    hide_pause_resume_buttons(chat_id)
    show_service_choice(chat_id)

def like_posts_by_hashtag(hashtag, chat_id):
    tg_bot.send_message(chat_id, "Пожалуйста подождите я обрабатываю ваш хэштег")
    show_pause_stop_buttons(chat_id)
    global stop_task
    stop_task = False
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)
        for media in medias:
            if stop_task:
                break
            while pause_task:
                time.sleep(1)
            try:
                user_info = insta_bot.media_info(media.id).user
                insta_bot.media_like(media.id)
                media_url = f"https://www.instagram.com/p/{media.code}/"
                output = f"Пользователь: {user_info.username}\nПост: <a href='{media_url}'>{media.id}</a>\nЛайк успешно поставлен"
                logger.info(output)
                tg_bot.send_message(chat_id, output, parse_mode='HTML')
                for _ in range(6):
                    if stop_task:
                        break
                    while pause_task:
                        time.sleep(1)
                    time.sleep(1)
            except Exception as e:
                error_output = f"Пост: {media.id}\nОшибка при лайке\nПричина: {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)
            if stop_task:
                break
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Error fetching media: {e}")
    hide_pause_resume_buttons(chat_id)
    show_service_choice(chat_id)

def comment_on_posts_by_hashtag(hashtag, comment_text, chat_id):
    tg_bot.send_message(chat_id, "Подождите немного мы обрабатываем ваш хэштег")
    show_pause_stop_buttons(chat_id) 
    commented_posts = load_commented_posts()
    global stop_task
    stop_task = False 
    try:
        medias = insta_bot.hashtag_medias_recent(hashtag.strip('#'), amount=10)
        for media in medias:
            if stop_task:
                break
            while pause_task:
                time.sleep(1)
            if media.id in commented_posts:
                logger.info(f'Skipping post: {media.id} (already commented)')
                continue
            try:
                user_info = insta_bot.media_info(media.id).user
                insta_bot.media_comment(media.id, comment_text)
                save_commented_post(media.id)
                media_url = f"https://www.instagram.com/p/{media.code}/"
                output = f"Пользователь: {user_info.username}\nПост: <a href='{media_url}'>{media.id}</a>\nКомментарий успешно оставлен"
                logger.info(output)
                tg_bot.send_message(chat_id, output, parse_mode='HTML')
                for _ in range(10):
                    if stop_task:
                        break
                    while pause_task:
                        time.sleep(1)
                    time.sleep(1)
            except Exception as e:
                error_output = f"Пользователь: {user_info.username}\nПост: {media.id}\nОшибка при комментирование\n {str(e)}"
                logger.error(error_output)
                tg_bot.send_message(chat_id, error_output)
                if stop_task:
                    break
    except Exception as e:
        logger.error(f"Error during fetching media: {e}")
        tg_bot.send_message(chat_id, f"Ошибка при получении медиа: {e}")
    hide_pause_resume_buttons(chat_id)
    show_service_choice(chat_id)

def show_pause_stop_buttons(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    pause_button = types.KeyboardButton('Пауза')
    stop_button = types.KeyboardButton('Стоп')
    markup.add(pause_button, stop_button)
    tg_bot.send_message(chat_id, "Вы можете пристановить или остановить выполнение задачи:", reply_markup=markup)
def show_resume_button(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    resume_button = types.KeyboardButton('Продолжить')
    stop_button = types.KeyboardButton('Стоп')
    markup.add(resume_button, stop_button)
    tg_bot.send_message(chat_id, "Задание пристановлено", reply_markup=markup )

def hide_pause_resume_buttons(chat_id):
    markup = types.ReplyKeyboardRemove()
    tg_bot.send_message(chat_id, "Задание завершено.", reply_markup=markup)

def show_service_choice(chat_id):
    msg = tg_bot.send_message(chat_id, "Выберите услугу:\n1. Подписка по хэштегу\n2. Лайки по хэштегу\n3. Комментарий по хэштегу\nВведите номер услуг:")
    tg_bot.register_next_step_handler(msg, handle_service_choice)

@tg_bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = tg_bot.reply_to(message, "Привет! Введите ваш логин от Instagram")
    tg_bot.register_next_step_handler(msg, get_instagram_username)

@tg_bot.message_handler(func=lambda message: message.text == 'Пауза')
def pause(message):
    global pause_task
    pause_task = True
    show_resume_button(message.chat.id)

@tg_bot.message_handler(func=lambda message: message.text == 'Продолжить')
def resume(message):
    global pause_task
    pause_task = False
    show_pause_stop_buttons(message.chat.id)

@tg_bot.message_handler(func=lambda message: message.text == 'Стоп')
def stop(message):
    global stop_task
    stop_task = True

def get_instagram_username(message):
    global instagram_username
    instagram_username = message.text
    msg = tg_bot.reply_to(message, "Введите пароль от instagram")
    tg_bot.register_next_step_handler(msg, get_instagram_password)

def get_instagram_password(message):
    global instagram_password
    instagram_password = message.text
    tg_bot.reply_to(message, "Пожалуйста подождите немного, я сейчас авторизуюсь.")
    authenticate_instagram(message)

def authenticate_instagram(message):
    global insta_bot, instagram_username, instagram_password
    try:
        insta_bot.login(username=instagram_username, password=instagram_password)
        show_service_choice(message.chat.id)
    except Exception as e:
        if 'two-factor authentication required' in str(e):
            msg = tg_bot.reply_to(message, "Требуется двухфакторная аутентификация. Пожалуйста, введите код подтверждения:")
            tg_bot.register_next_step_handler(msg, get_2fa_code)
        else:
            tg_bot.reply_to(message, f"Произошла ошибка: {e}")

def get_2fa_code(message):
    verification_code = message.text
    global insta_bot, instagram_username, instagram_password
    try:
        insta_bot.login(username=instagram_username, password=instagram_password, verification_code=verification_code)
    except Exception as e:
        tg_bot.reply_to(message, f"Произошла ошибка при двухфакторной аутентификации: {e}")

def handle_service_choice(message):
    try:
        service_choice = int(message.text)
        msg = tg_bot.reply_to(message, "Введите хэштег для выполнение услуги:")
        tg_bot.register_next_step_handler(msg, lambda m: handle_hashtag(m, service_choice, message.chat.id))
    except ValueError:
        tg_bot.reply_to(message, "Неверный выбор услуги!")
        show_service_choice(message.chat.id)

def handle_hashtag(message, service_choice, chat_id):
    user_hashtag = message.text
    if service_choice == 1:
        follow_users_by_hashtag(user_hashtag, chat_id)
    elif service_choice == 2:
        like_posts_by_hashtag(user_hashtag, chat_id)
    elif service_choice == 3:
        msg = tg_bot.reply_to(message, "Пожалуйста, напишите свой комментарий:")
        tg_bot.register_next_step_handler(msg, lambda m: handle_comment(m, user_hashtag, chat_id))
    else:
        output = "Неверный ввод. Пожалуйста, укажите допустимое действие."
        tg_bot.reply_to(message, output)

def handle_comment(message, user_hashtag, chat_id):
    comment_text = message.text
    comment_on_posts_by_hashtag(user_hashtag, comment_text, chat_id)

while True:
    try:
        tg_bot.polling(none_stop=True, interval=0, timeout=40)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        time.sleep(15)
