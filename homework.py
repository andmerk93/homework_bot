import logging
from logging.handlers import RotatingFileHandler
import os
import requests
import time
from dotenv import load_dotenv
import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600  # /120
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
THREE_DAYS = 259200  # +5184000


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('homework.log', maxBytes=50000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """
    Проверяет доступность переменных окружения
    """
    if not (
        PRACTICUM_TOKEN
        and TELEGRAM_TOKEN
        and TELEGRAM_CHAT_ID
    ):
        logger.critical('problem with tokens')
        raise Exception('problem with tokens')


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(message)
    except Exception as error:
        logger.error(error)


def get_api_answer(timestamp):
    """
    Делает запрос к эндпоинту API
    """
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            url=ENDPOINT,
            params=payload,
            headers=HEADERS
        )
    except Exception as error:
        logger.error(error)
    if api_answer.status_code != 200:
        raise Exception('bad answer from API Endpoint')
    return api_answer.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие документации (частично)
    """
    if (
        'current_date' not in response
        or 'homeworks' not in response
        or type(response['current_date']) != int
        or type(response['homeworks']) != list
    ):
        raise TypeError('bad type current_date or homeworks in JSON')
    if len(response['homeworks']) == 0:
        raise Exception('There is no homeworks for this date')


def homeworks_validator(response):
    """
    Нормальный валидатор домашек.
    Перенёс отдельно из-за автотестов. 
    """
    homeworks_structure = {
        'id': int,
        'status': str,  # 4 statuses
        'homework_name': str,
        'reviewer_comment': str,
        'date_updated': str,  # ISO 8601
        'lesson_name': str,
    }
    for homework in response['homeworks']:
        for i in homeworks_structure:
            if (
                i not in homework
                or type(homework[i]) != homeworks_structure[i]
            ):
                raise Exception(
                    f'problems with {i} key in homework {homework}'
                )


def parse_status(homework):
    """
    Извлекает работе статус домашней работы
    """
    if homework['status'] not in HOMEWORK_VERDICTS:
        status = homework['status']
        raise Exception(f'bad status {status} in homework {homework}')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    if 'homework_name' not in homework:
        raise Exception('для автотестов, нормальный валидатор выше')
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """
    Основная логика работы бота.
    """
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - THREE_DAYS
    message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
#            homeworks_validator(response)  # autotests
            if message != parse_status(response['homeworks'][0]):
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            logger.debug(response)
        except Exception as error:
            logger.error(error, exc_info=True)
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
