import requests
from  datetime import datetime
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater
import ids

#load_dotenv()


PRACTICUM_TOKEN = ids.PRACTICUM_TOKEN
TELEGRAM_TOKEN = ids.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = ids.TELEGRAM_CHAT_ID

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    pass


def send_message(bot, message):
    pass


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    api_answer = requests.get(url=ENDPOINT, params=payload, headers=HEADERS)
    return api_answer.json()


def check_response(response):
    homeworks_structure = {
        'id': int,
        'status': str, # 4 statuses
        'homework_name': str,
        'reviewer_comment': str,
        'date_updated': str, # ISO 8601
        'lesson_name': str,
    }
    try:
        if (
            type(response['current_date']) != int and
            type(response['homeworks']) != list
        ):
            print('bad type current_date or homeworks in JSON')
    except KeyError:
        print('no current_date or homeworks in JSON')
    for homework in response['homeworks']:
        try:
            for i in homeworks_structure:
                if type(homework[i]) != homeworks_structure[i]:
                    print(f'bad type {homework[i]} in homework {homework}')
            if homework['status'] not in HOMEWORK_VERDICTS.keys():
                status = homework['status']
                print(f'bad status {status} in homework {homework}')
            try:
                datetime.strptime(
                    homework['date_updated'],
                    '%Y-%m-%dT%H:%M:%SZ'
                )
            except ValueError:
                date = homework['date_updated']
                print(f'bad date format {date} in homework {homework}')
        except KeyError:
            print(f'there is no {i} in homework {homework}')


def parse_status(homework):
    pass

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    pass

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    print()

    while True:
        try:

            print()

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print()
        print()


if __name__ == '__main__':
#    main()
    response = get_api_answer(1665226552)
    check_response(response)
