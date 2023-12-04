import argparse
import sys
import random
import requests

# Функция для проверки числа на простоту
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

# Функция для нахождения простого числа в заданном диапазоне
def generate_prime_number(min_value, max_value):
    prime = random.randint(min_value, max_value)
    while not is_prime(prime):
        prime = random.randint(min_value, max_value)
    return prime

# Функция для нахождения НОДа двух чисел
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

# Функция для нахождения обратного элемента по модулю
def mod_inverse(a, m):
    m0, x0, x1 = m, 0, 1
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += m0
    return x1

# Генерация ключей
def generate_keypair():
    p = generate_prime_number(100, 1000)  # Генерация случайного простого числа p
    q = generate_prime_number(100, 1000)  # Генерация случайного простого числа q
    N = p * q  # Вычисление N = p * q
    phi = (p - 1) * (q - 1)  # Вычисление функции Эйлера phi(N)

    # Выбор числа e
    e = random.randint(2, phi - 1)
    while gcd(e, phi) != 1:
        e = random.randint(2, phi - 1)

    # Вычисление числа d (обратное к e по модулю phi(N))
    d = mod_inverse(e, phi)

    return (e, N), (d, N)  # Возвращение открытого и закрытого ключей

# Шифрование и дешифрование

def encrypt(message, public_key):
    e, N = public_key  # Распаковываем открытый ключ на экспоненту и модуль
    encrypted_message = [pow(ord(char), e, N) for char in message]  # Шифрование каждого символа в тексте
    return encrypted_message  # Возвращает список зашифрованных символов


def decrypt(encrypted_message, private_key):
    d, N = private_key
    decrypted_message = [chr(pow(char, d, N)) for char in encrypted_message]
    return ''.join(decrypted_message)


def save_keys_to_file(public_key, private_key, filename):
    with open(filename, 'w') as file:
        file.write(f"Public Key (e, N): {public_key}\n")
        file.write(f"Private Key (d, N): {private_key}\n")


def send_public_key_from_file():
    # Генерация ключей
    public_key, private_key = generate_keypair()
    print("Открытый ключ (e, N):", public_key)
    print("Закрытый ключ (d, N):", private_key)
    # Сохранение ключей в файл
    save_keys_to_file(public_key, private_key,'keys.txt')

    # Отправка ключей на сервер
    url = 'http://127.0.0.1:5000/keys'  # Адрес сервера Flask

    try:
        with open('keys.txt', 'r') as file:
            lines = file.readlines()
            public_key = eval(lines[0].split(": ")[1])  # Получаем публичный ключ из файла
    except FileNotFoundError:
        print("Файл с ключами не найден.")
        return

    # Отправляем публичный ключ на сервер
    response = requests.post(url, json={'public_key_from_file': public_key})

    if response.status_code == 200:
        print("Открытый ключ из файла успешно отправлен на сервер!")

        # Получаем публичный ключ от сервера
        server_public_key = response.json()
        

        # Сохраняем полученный публичный ключ от сервера в файле
        save_keys_to_file(server_public_key, None,  'server_public_key.txt')
        print("Полученный открытый ключ от сервера сохранен в файле.", server_public_key )
    else:
        print("Что-то пошло не так при отправке открытого ключа из файла.")

def send_text_to_server(server_public_key):
    url = 'http://127.0.0.1:5000/'  # Адрес сервера Flask

    # Получение текста для отправки
    text_to_send = input("Введите текст для отправки на сервер: ")

    # Шифрование текста открытым ключом сервера
    encrypted_msg = encrypt(text_to_send, server_public_key)
    print("Зашифрованный текст:", encrypted_msg)
    
    # Отправляем публичный ключ на сервер
    response = requests.post(url, json={'encrypted_text': encrypted_msg})

    if response.status_code == 200:
        print("Зашифрованный текст успешно отправлен на сервер!")
    else:
        print("Что-то пошло не так при отправке зашифрованного текста.")


def main():
    parser = argparse.ArgumentParser(description='Описание вашей программы')
    parser.add_argument('-keys', action='store_true', help='Генерация ключей и отправка на сервер')
    parser.add_argument('-send', action='store_true', help='Отправка текста на сервер')

    args = parser.parse_args()

    if args.keys:
        send_public_key_from_file()
    elif args.send:
        # Чтение публичного ключа сервера из файла
        try:
            with open('server_public_key.txt', 'r') as file:
                lines = file.readlines()
                server_public_key = eval(lines[0].split(": ")[1])  # Получаем публичный ключ сервера из файла
        except FileNotFoundError:
            print("Файл с публичным ключом сервера не найден.")
            return
        send_text_to_server(server_public_key)
    else:
        parser.print_help(sys.stderr)

if __name__ == "__main__":
    main()