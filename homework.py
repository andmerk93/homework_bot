import logging
from logging.handlers import RotatingFileHandler
import os
import time

from dotenv import load_dotenv
import requests
import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TOKENS_NAMES = [
    'PRACTICUM_TOKEN',
    'TELEGRAM_TOKEN',
    'TELEGRAM_CHAT_ID',
]

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HOMEWORK_STATUS = 'Изменился статус проверки работы "{0}". {1}'
TOKENS_PROBLEM = 'Problems with tokens: {0}'
SENT_TO_USER = 'Sent to user: {0}'
PROBLEMS_WITH = 'Problems with {0}'
API_GENERAL_ERROR_LOG = (
    'Some troubles with url={0}; params={1}; headers={2}; caused error {3}'
)
API_STATUS_CODE_ERROR_LOG = (
    'Bad answer from API Endpoint. Some troubles with '
    'url={0}; params={1}; headers={2}; caused status code {3}'
)
ERROR_IN_JSON = 'Got error in JSON: {0}'
ERROR_IN_JSON_WOTH_CODE = 'Got error in JSON with code: {0}'
WRONG_TYPE_OF_RESPONSE = 'Got wrong type of response: {0}'
RESPONSE_STRUCTURE_NO_HOMEWORKS = (
    'Got error with response structure, no homeworks'
)
TYPE_ERROR_IN_HOMEWORKS_JSON = 'Got {0} homeworks instead of list'
NO_HOMEWORKS_IN_RESPONSE = 'Didnt get any homeworks'
WRONG_STATUS_IN_PARSED_HOMEWORK = 'Bad status {0} in homework {1}'
WRONG_NAME_IN_PARSED_HOMEWORK = 'Problems with homework_name in homework {0}'
MESSAGE_FOR_LAST_EXCEPTION = 'Got error while running: {0}'

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
    problems = ''
    for name in TOKENS_NAMES:
        if not globals()[name]:
            problems += (name + ', ')
    if problems:
        text = TOKENS_PROBLEM.format(problems)[:-2]
        logger.critical(text)
        raise NameError(text)


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        sent = bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(SENT_TO_USER.format(sent))
        return sent
    except Exception:
        logger.exception(PROBLEMS_WITH.format(message))


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            url=ENDPOINT,
            params=payload,
            headers=HEADERS
        )
    except requests.RequestException as error:
        raise OSError(
            API_GENERAL_ERROR_LOG.format(
                ENDPOINT,
                payload,
                HEADERS,
                error
            )
        )
    if api_answer.status_code != 200:
        raise OSError(
            API_STATUS_CODE_ERROR_LOG.format(
                ENDPOINT,
                payload,
                HEADERS,
                api_answer.status_code
            )
        )
    json = api_answer.json()
    if 'error' in json:
        raise OSError(ERROR_IN_JSON.format(json['error']))
    if 'code' in json:
        raise OSError(ERROR_IN_JSON_WOTH_CODE.format(json['code']))
    return json


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    def test_instance(var, typ, message):
        type_var = type(var)
        if not (isinstance(type_var, typ) or issubclass(type_var, typ)):
            raise TypeError(message.format(type_var))
    test_instance(response, dict, WRONG_TYPE_OF_RESPONSE)
    if 'homeworks' not in response:
        raise KeyError(RESPONSE_STRUCTURE_NO_HOMEWORKS)
    test_instance(response['homeworks'], list, TYPE_ERROR_IN_HOMEWORKS_JSON)


def parse_status(homework):
    """Извлекает работе статус домашней работы."""
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
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
            if len(response['homeworks']) != 0:
                message = parse_status(response['homeworks'][0])
            else:
                message = NO_HOMEWORKS_IN_RESPONSE
            if sent_message != message:
                sent_message = send_message(bot, message)
        except Exception as error:
            message = MESSAGE_FOR_LAST_EXCEPTION.format(error)
            logger.exception(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
