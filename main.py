import csv
from itertools import product
from sys import stdout

import requests

from exceptions import APIResponseError
from orm_models import BigTransaction, session, UsualTransaction

CENTRAL_BANK_API = 'https://www.cbr-xml-daily.ru/daily_json.js'

# настроить получение .csv-файлов через os.walk

csv_list = ['clients.csv', 'currency.csv', 'volume.csv']


def get_files():
    """Finds .csv-files"""
    pass


def process_csv(csv_file):
    """Reads data from csv-file."""
    with open(csv_file, newline='', encoding='UTF-8') as file:
        data = [row for row in csv.reader(file)]
        return data


def compile_data():
    """Compiles data from several csv-files
    using python 'product' function."""
    preprocessed_data = []
    for i in range(3):
        package = process_csv(csv_list[i])
        preprocessed_data.append(package)
    all_combos = list(product(*preprocessed_data))
    return all_combos


def get_info_from_bank():
    try:
        # acquiring JSON from the bank
        bank_data = requests.get(CENTRAL_BANK_API)
        converted_data = bank_data.json().get('Valute')

    except requests.exceptions.RequestException:
        raise APIResponseError('Ошибка взаимодействия с API ЦБ РФ')
        # лог-сообщение в консоль об ошибке
    return converted_data


def process_client_name(name_array: list) -> str:
    """Shortens the first name and the patronymic, if
     the length of the second name is more, than 8 chars."""
    separated_array = name_array[0].split(' ')
    if len(separated_array[0]) > 8:
        separated_array[0] += ' '
        separated_array[1] = separated_array[1][0] + '.'
        separated_array[2] = separated_array[2][0] + '.'
        return ''.join(separated_array)
    else:
        return ' '.join(name_array)


def create_objects(combos, financial_data):
    id_counter = 1
    for element in combos:
        name = process_client_name(element[0])
        # ПРЕДУСМОТРЕТЬ ИСКЛЮЧЕНИЕ, ЕСЛИ НЕТ КОДА ВАЛЮТЫ!
        currency_course = financial_data[element[1][0]]['Value']
        ruble_sum = round(int(element[2][0]) * currency_course, 2)
        if ruble_sum > 1000:
            transaction = BigTransaction(
                id=id_counter,
                name=name,
                currency=element[1][0],
                volume=ruble_sum
                )
        else:
            transaction = UsualTransaction(
                id=id_counter,
                name=name,
                currency=element[1][0],
                volume=ruble_sum
                )
        session.add(transaction)
        session.commit()

        id_counter += 1

    stdout.write(
        'Information about the transactions has been successfully transferred to the database.')


def main():
    """Main logic."""
    csv_combos = compile_data()
    bank_data = get_info_from_bank()
    create_objects(csv_combos, bank_data)


if __name__ == '__main__':
    main()
