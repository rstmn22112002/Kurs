import logging
from flask import Flask, request, jsonify
import random
import requests
import json
import base64

app = Flask(__name__)


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
    e, N = public_key
    encrypted_message = [pow(ord(char), e, N) for char in message]
    return encrypted_message

def decrypt(encrypted_message, private_key):
    d, N = private_key
    decrypted_message = [chr(pow(char, d, N)) for char in encrypted_message]
    return ''.join(decrypted_message)



def save_keys_to_file(public_key, private_key, filename):
    with open(filename, 'w') as file:
        file.write(f"Public Key (e, N): {public_key}\n")
        file.write(f"Private Key (d, N): {private_key}\n")

def generate_keys():
    # Генерация ключей на сервере
    server_public_key, server_private_key = generate_keypair()
    print("Открытый ключ сервера (e, N):", server_public_key)
    print("Закрытый ключ сервера (d, N):", server_private_key)

    # Сохранение ключей сервера в файл
    save_keys_to_file(server_public_key, server_private_key, 'server_keys.txt')
    return server_public_key, server_private_key

@app.route('/keys', methods=['POST'])
def handle_request():
    if 'public_key_from_file' in request.json:
        # Получаем публичный ключ от клиента из файла
        client_public_key = request.json['public_key_from_file']
        print("Получен публичный ключ от клиента:", client_public_key)

        # Сохраняем публичный ключ от клиента в файле
        save_keys_to_file(client_public_key, None, 'client_keys.txt')

        # Генерируем свои ключи на сервере
        server_public_key, server_private_key = generate_keys()

        # Отправляем свой открытый ключ клиенту
        return jsonify(server_public_key)



@app.route('/', methods=['POST'])
def decrypt_message():
    encrypted_text = request.json['encrypted_text']
    print("Получен зашифрованный текст:", encrypted_text)
    
    # Используем закрытый ключ сервера для расшифровки текста

    try:
        with open('server_keys.txt', 'r') as file:
                lines = file.readlines()
                server_private_key = eval(lines[1].split(": ")[1])  # Получаем публичный ключ сервера из файла
    except FileNotFoundError:
            print("Файл с публичным ключом сервера не найден.")

    decrypted_message = decrypt(encrypted_text, server_private_key)  # Расшифровка текста
    print("Расшифрованный текст:", decrypted_message)
    return jsonify({'decrypted_text': decrypted_message})


@app.route('/send_encrypted', methods=['POST'])
def send_encrypted_message():
    # Загрузка публичного ключа клиента из файла
    try:
        with open('client_keys.txt', 'r') as file:
            lines = file.readlines()
            client_public_key = eval(lines[0].split(": ")[1])  # Получаем публичный ключ сервера из файла
    except FileNotFoundError:
            print("Файл с публичным ключом клиента не найден.")
            return
    if request.method == 'POST':
        # Получение текста с консоли сервером
        text_to_encrypt = input("Введите текст для шифрования и отправки клиенту: ")

        # Здесь происходит шифрование текста
        encrypted_message = encrypt(text_to_encrypt, client_public_key)

        # Отправляем зашифрованное сообщение клиенту
        return jsonify({'encrypted_message': encrypted_message})


if __name__ == "__main__":
    app.run(debug=True)



