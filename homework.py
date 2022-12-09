import os
import requests
import time
from dotenv import load_dotenv
import telegram


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
THREE_DAYS = 259200


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    if not (
        PRACTICUM_TOKEN and
        TELEGRAM_TOKEN and
        TELEGRAM_CHAT_ID
    ):
        raise Exception('problem with tokens')


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    api_answer = requests.get(url=ENDPOINT, params=payload, headers=HEADERS)
    if api_answer.status_code != 200:
        raise Exception('bad answer from API Endpoint')
    return api_answer.json()


def check_response(response):
    homeworks_structure = {
        'id': int,
        'status': str,  # 4 statuses
        'homework_name': str,
        'reviewer_comment': str,
        'date_updated': str,  # ISO 8601
        'lesson_name': str,
    }
    if (
        'current_date' not in response or
        'homeworks' not in response or
        type(response['current_date']) != int or
        type(response['homeworks']) != list
    ):
        raise Exception('bad type current_date or homeworks in JSON')
    if len(response['homeworks']) == 0:
        raise Exception('There is no homeworks for this date')
    for homework in response['homeworks']:
        for i in homeworks_structure:
            if (
                i not in homework or
                type(homework[i]) != homeworks_structure[i]
            ):
                raise Exception(
                    f'problems with {i} key in homework {homework}'
                )


def parse_status(homework):
    if homework['status'] not in HOMEWORK_VERDICTS:
        status = homework['status']
        raise Exception(f'bad status {status} in homework {homework}')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - THREE_DAYS
    message = ''
    while True:
        try:
            response = get_api_answer(timestamp - 5184000 // 2)  # del later
            check_response(response)
            if message != parse_status(response['homeworks'][0]):
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            print(response)  # del later
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD/120)  # del later


if __name__ == '__main__':
    main()
