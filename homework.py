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
    'Some troubles with url={url}; params={params}; ',
    'headers={headers}; caused error {error}'
)
API_STATUS_CODE_ERROR_LOG = (
    'Bad answer from API Endpoint. Some troubles with '
    'url={url}; params={params}; headers={header}; caused status code {code}'
)
ERROR_IN_JSON = (
    'Got error in JSON: {key}: {value}. ',
    'Requested url={url}; params={params}; headers={header};'
)
WRONG_TYPE_OF_RESPONSE = 'Got wrong type of response: {0}'
RESPONSE_STRUCTURE_NO_HOMEWORKS = (
    'Got error with response structure, no homeworks'
)
TYPE_ERROR_IN_HOMEWORKS_JSON = 'Got {0} homeworks instead of list'
WRONG_STATUS_IN_PARSED_HOMEWORK = 'Bad status {0} in paresd homework'
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


class APIEndpointError(Exception):
    """Bad answer from API Endpoint."""


def check_tokens():
    """Проверяет доступность переменных окружения."""
    problems = [name for name in TOKENS_NAMES if not globals()[name]]
    if problems:
        text = TOKENS_PROBLEM.format(problems)
        logger.critical(text)
        raise NameError(text)


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        message = bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(SENT_TO_USER.format(message))
        return message
    except Exception:
        logger.exception(PROBLEMS_WITH.format(message))
        return ''


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    params = dict(
        url=ENDPOINT,
        params={'from_date': timestamp},
        headers=HEADERS
    )
    try:
        api_answer = requests.get(**params)
    except requests.RequestException as error:
        raise ConnectionError(
            API_GENERAL_ERROR_LOG.format(
                **params,
                error=error
            )
        )
    if api_answer.status_code != 200:
        raise APIEndpointError(
            API_STATUS_CODE_ERROR_LOG.format(
                **params,
                code=api_answer.status_code
            )
        )
    json = api_answer.json()
    for key in ['error', 'code']:
        if key in json:
            raise ValueError(
                ERROR_IN_JSON.format(
                    key=key,
                    value=json[key],
                    **params,
                )
            )
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
            WRONG_STATUS_IN_PARSED_HOMEWORK.format(status)
        )
    if 'homework_name' not in homework:
        raise KeyError(WRONG_NAME_IN_PARSED_HOMEWORK.format(homework))
    return HOMEWORK_STATUS.format(
        homework['homework_name'],
        HOMEWORK_VERDICTS[status]
    )


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
            if response['homeworks']:
                message = parse_status(response['homeworks'][0])
                if sent_message != message:
                    sent_message = send_message(bot, message)
        except Exception as error:
            message = MESSAGE_FOR_LAST_EXCEPTION.format(error)
            logger.exception(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
