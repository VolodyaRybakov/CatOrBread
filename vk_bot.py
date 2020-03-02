import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
import difflib
import json
import logging
import pymysql.cursors

logging.basicConfig(format=u'[%(asctime)s]  %(message)s',
                    level=logging.INFO, filename=u'vk_bot.log')

YES_ANSWERS = ["да", "конечно", "ага", "пожалуй"]
NO_ANSWERS = ["нет", "нет, конечно", "ноуп", "найн"]

full_keyboard = open('keyboards/full_keyboard.json', 'r', encoding='utf-8').read()
finish_keyboard = open("keyboards/finish_keyboard.json", "r", encoding="UTF-8").read()


# try:
#     connection = pymysql.connect(
#         host='localhost',
#         user='root',
#         db='VkBotLogging',
#         charset='utf8mb4',
#         cursorclass=pymysql.cursors.DictCursor,
#         password='admin'
#     )
# except Exception:
#     logging.error("Cannot connect to database")
#     exit(0)


# def writeToDatabase(user_id, message, state):
#     with connection.cursor() as cursor:
#         sql = "INSERT INTO `user_messages` (`user_id`, `umessage`, `state`) VALUES (%s, %s, %s)"
#         cursor.execute(sql, (user_id, message, state))
#         connection.commit()


def write_msg(user_id, message, keyboard=full_keyboard):
    vk.method('messages.send', {
              'user_id': user_id, 'message': message, 'random_id': random.randint(0, 2048), 'keyboard': keyboard})


currentState = {}


def upload_photo(upload, photo):
    response = upload.photo_messages(photo)[0]

    owner_id = response['owner_id']
    photo_id = response['id']
    access_key = response['access_key']

    return owner_id, photo_id, access_key


def send_photo(vk, user_id, owner_id, photo_id, access_key):
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    vk.method('messages.send', {
              'user_id': user_id, 'attachment': attachment, 'random_id': random.randint(0, 2048)})
    logging.debug(f"Sending photo to user {user_id}")


def isSimilar(chk_str, etln_arr):
    normalized = chk_str.lower()
    max_ratio = 0.
    for etalon in etln_arr:
        matcher = difflib.SequenceMatcher(None, normalized, etalon)
        if matcher.ratio() > max_ratio:
            max_ratio = matcher.ratio()
    logging.debug(
        f'message {normalized} responds reference value {etln_arr} on {max_ratio}')
    return True if max_ratio > 0.9 else False


def start(event):
    request = event.text
    global currentState

    logging.info(
        f"User with id {event.user_id} sent message {request} to state 'start'")
    # writeToDatabase(event.user_id, request, 'start')

    if str.lower(request) == "/start":
        write_msg(
            event.user_id, "Привет! Я помогу отличить кота от хлеба! Объект перед тобой квадратный?")
        currentState[event.user_id] = isObjectSquare
    else:
        write_msg(event.user_id, "Не понял твоего ответа. Введи команду '/start'")


def isObjectSquare(event):
    request = event.text
    global currentState

    logging.info(
        f"User with id {event.user_id} sent message {request} to state 'isObjectSquare'")
    # writeToDatabase(event.user_id, request, 'isObjectSquare')

    if str.lower(request) == "/start":
        write_msg(
            event.user_id, "Привет! Я помогу отличить кота от хлеба! Объект перед тобой квадратный?")
        currentState[event.user_id] = isObjectSquare
    elif str.lower(request) in YES_ANSWERS:
        write_msg(
            event.user_id, "У него есть уши?")
        currentState[event.user_id] = isObjectHasEars
    elif isSimilar(request, NO_ANSWERS):
        write_msg(
            event.user_id, "Это кот, а не хлеб! Не ешь его!", finish_keyboard)
        send_photo(vk, event.user_id, *upload_photo(upload, 'images/cat.jpg'))
        currentState[event.user_id] = start

    else:
        write_msg(event.user_id, "Не понял твоего ответа. Попробуй ещё раз.")


def isObjectHasEars(event):
    request = event.text
    global currentState

    logging.info(
        f"User with id {event.user_id} sent message {request} to state 'isObjectHasEars'")
    # writeToDatabase(event.user_id, request, 'isObjectHasEars')

    if str.lower(request) == "/start":
        write_msg(
            event.user_id, "Привет! Я помогу отличить кота от хлеба! Объект перед тобой квадратный?")
        currentState[event.user_id] = isObjectSquare
        return
    elif str.lower(request) in NO_ANSWERS:
        write_msg(
            event.user_id, "Это хлеб, а не кот! Ешь его!", finish_keyboard)
        send_photo(vk, event.user_id, *upload_photo(upload, 'images/bread.jpg'))
        currentState[event.user_id] = start
    elif str.lower(request) in YES_ANSWERS:
        write_msg(
            event.user_id, "Это кот, а не хлеб! Не ешь его!", finish_keyboard)
        send_photo(vk, event.user_id, *upload_photo(upload, 'images/cat.jpg'))
        currentState[event.user_id] = start
    else:
        write_msg(event.user_id, "Не понял твоего ответа. Попробуй ещё раз.")


token = "0a8f1000ad741ddb75fbc55b6c4b2e04c6ad605d53284c7b6e43b81335588f1cd7f7868fdb9582a50d558"

vk = vk_api.VkApi(token=token)

longpoll = VkLongPoll(vk)
upload = VkUpload(vk)

for event in longpoll.listen():

    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            try:
                currentState[event.user_id](event)
            except KeyError:
                currentState[event.user_id] = start
                currentState[event.user_id](event)
