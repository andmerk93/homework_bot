import logging
from logging.handlers import RotatingFileHandler
import os
import time

from dotenv import load_dotenv
from requests import RequestException #for homework_tests
from requests import HTTPError #for homework_tests
import requests
import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HOMEWORK_STATUS = 'Изменился статус проверки работы "{0}". {1}'
TOKENS_PROBLEM = 'Problem with token {0}'
API_GENERAL_ERROR_LOG = (
    'Some troubles with url={0}; params={1}; headers={2}; caused error {3}'
)
API_STATUS_CODE_ERROR_LOG = (
    'Bad answer from API Endpoint. Some troubles with '
    'url={0}; params={1}; headers={2}; caused status code {3}'
)
WRONG_TYPE_OF_RESPONSE = 'Got wrong type of response'
RESPONSE_STRUCTURE_NO_HOMEWORKS = (
    'Got error with response structure, no homeworks'
)
ERROR_IN_HOMEWORKS_JSON = 'Got error with homeworks structure'
NO_HOMEWORKS_IN_RESPONSE = 'Didnt get any homeworks'
WRONG_STATUS_IN_PARSED_HOMEWORK = 'Bad status {0} in homework {1}'
WRONG_NAME_IN_PARSED_HOMEWORK = 'Problems with homework_name in homework {0}'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    __file__ + '.log',
    maxBytes=50000000,
    backupCount=5
)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID'
    }
    for token in tokens:
        if not token:
            text = TOKENS_PROBLEM.format(tokens[token])
            logger.critical(text)
            raise NameError(text)


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('sent to user: ' + message)
    except Exception as error:
        logger.exception(error)
        logger.error('problems with ' + message)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            url=ENDPOINT,
            params=payload,
            headers=HEADERS
        )
    except RequestException as error:
        text = API_GENERAL_ERROR_LOG.format(
            ENDPOINT,
            payload,
            HEADERS,
            error
        )
        raise RequestException(text)
    if api_answer.status_code != 200:
        text = API_STATUS_CODE_ERROR_LOG.format(
            ENDPOINT,
            payload,
            HEADERS,
            api_answer.status_code
        )
        raise HTTPError(text)
    return api_answer.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if type(response) != dict:
        raise TypeError(WRONG_TYPE_OF_RESPONSE)
    if 'homeworks' not in response:
        raise KeyError(RESPONSE_STRUCTURE_NO_HOMEWORKS)
    if type(response['homeworks']) != list:
        raise TypeError(ERROR_IN_HOMEWORKS_JSON)
    if len(response['homeworks']) == 0:
        raise IndexError(NO_HOMEWORKS_IN_RESPONSE)


def parse_status(homework):
    """Извлекает работе статус домашней работы."""
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(
            WRONG_STATUS_IN_PARSED_HOMEWORK.format(status, homework)
        )
    verdict = HOMEWORK_VERDICTS[status]
    if 'homework_name' not in homework:
        raise KeyError(WRONG_NAME_IN_PARSED_HOMEWORK.format(homework))
    homework_name = homework['homework_name']
    return HOMEWORK_STATUS.format(homework_name, verdict)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    sent_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            logger.debug(response)
            check_response(response)
            message = parse_status(response['homeworks'][0])
            if sent_message != message:
                send_message(bot, message)
                sent_message = message
        except Exception as error:
            logger.exception(error)
            message = f'{error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
