import csv
from itertools import product
import locale
import os
from pathlib import Path
import requests

from exceptions import APIResponseError
from logging_config import logger
from db_models import BigTransaction, session, UsualTransaction

# получаем путь до каталога, где лежит отдельно скрипт и отдельно папка demo с csv-файлами
MAIN_DIR = Path(__file__).resolve().parent.parent
CENTRAL_BANK_API = 'https://www.cbr-xml-daily.ru/daily_json.js'
# настраиваем локаль, что файлы, найденные через os.walk, во всех ОС были отсортированы одинаково
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def get_files(path):
    """Получает пути к csv-файлам для дальнейшего
    использования их в функции compile_data."""
    files = []
    for roots, dirs, file_names in os.walk(path):
        for file_name in file_names:
            if file_name.endswith('.csv'):
                file_path = os.path.join(roots, file_name)
                files.append(file_path)
        if not files:
            logger.critical('В папке "demo" не найдены csv-файлы для обработки')
            # сразу выходим из программы, если csv-файлы не обнаружены
            raise SystemExit

    return files


def process_csv(csv_file):
    """Считывает данные из csv-файлов."""
    with open(csv_file, newline='', encoding='UTF-8') as file:
        data = [row for row in csv.reader(file)]
        return data


def compile_data(csv_list):
    """Создает все возможные сочетания из
    содержимого csv-файлов при помощи функции product."""
    preprocessed_data = []
    for i in range(3):
        package = process_csv(csv_list[i])
        preprocessed_data.append(package)
    return list(product(*preprocessed_data))


def get_info_from_bank():
    try:
        # получаем JSON от банка
        bank_data = requests.get(CENTRAL_BANK_API)
        converted_data = bank_data.json().get('Valute')
    except requests.exceptions.RequestException:
        logger.error('Ошибка взаимодействия с API ЦБ РФ')
        raise APIResponseError('Ошибка взаимодействия с API ЦБ РФ')
    return converted_data


def process_client_name(name_array: list) -> str:
    """Укорачивает имя и отчество, если длина
    фамилии более 8-ми символов."""
    separated_array = name_array[0].split(' ')
    if len(separated_array[0]) > 8:
        separated_array[0] += ' '
        separated_array[1] = separated_array[1][0] + '.'
        separated_array[2] = separated_array[2][0] + '.'
        return ''.join(separated_array)
    else:
        return ' '.join(name_array)


def convert_to_rubles(user_curr, trans_amount, currency_info):
    """Пересчитывает валюту в рубли; проверяет, что такая валюта
    действительно поддерживается ЦБ РФ и предотвращает связанные с этим ошибки."""
    # если валюта операции - RUB, конверсия не производится
    if user_curr == 'RUB':
        return int(trans_amount)
    # если валюта - не RUB, то подсчитываем рублевый эквивалент операции
    else:
        # сначала предусматриваем KeyError - если валюта отсутствует в JSON от ЦБ РФ
        try:
            currency_course = currency_info[user_curr]['Value']
        except KeyError:
            logger.error(f'Попытка совершения транзакции с валютой {user_curr}. Операция отклонена,'
                         f'т.к. валюта {user_curr} не поддерживается ЦБ РФ.')
            # возвращаем None, т.к. далее, ориентируясь на него, вызовем continue в цикле for
            return None
        # если валюта успешно найдена - пересчитываем в рубли с округлением до копеек
        ruble_sum = round(float(trans_amount) * currency_course, 2)
        return ruble_sum


def write_to_db(csv_combos, currency_attrs):
    """Записывает в две разные таблицы информацию
    о финансовых операциях."""
    id_counter = 1
    for element in csv_combos:
        # получаем ФИО клиента из комбинаций csv
        name = process_client_name(element[1])
        # получаем валюту пользователя из комбинаций csv
        user_currency = element[2][0]
        # получаем сумму операции пользователя
        transaction_amount = element[0][0]
        # получаем рублевую сумму операции, если валюта поддерживается ЦБ РФ
        ruble_sum = convert_to_rubles(user_currency, transaction_amount, currency_attrs)
        if ruble_sum is None:
            # если функция пересчета в рубли вернула None по причине того, что валюта
            # не поддерживается ЦБ РФ - сразу переходим в следующую итерацию цикла
            continue

        # записываем данные в таблицы
        if ruble_sum > 1000:
            transaction = BigTransaction(
                id=id_counter,
                name=name,
                currency=user_currency,
                volume=ruble_sum
                )
        else:
            transaction = UsualTransaction(
                id=id_counter,
                name=name,
                currency=user_currency,
                volume=ruble_sum
                )
        session.add(transaction)
        session.commit()

        id_counter += 1
    logger.info('Информация успешно внесена в базу данных.')


def main():
    """Главная логика работы скрипта."""
    # вычисляем путь к папке с csv-файлами
    csv_dir = os.path.join(MAIN_DIR, 'demo')
    # получаем все csv-файлы с полными путями
    csv_list = get_files(csv_dir)
    # сортируем найденные файлы в алфавитном порядке независимо от локали
    sorted_csv = sorted(csv_list, key=lambda x: locale.strxfrm(x))
    # получаем все возможные комбинации данных из csv-файлов
    csv_combos = compile_data(sorted_csv)
    # получаем от ЦБ РФ информацию о конкретной валюте
    bank_data = get_info_from_bank()
    # производим запись данных в таблицы БД
    write_to_db(csv_combos, bank_data)


if __name__ == '__main__':
    main()
