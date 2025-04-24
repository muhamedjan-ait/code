import serial
import time
import requests
import json

# URL API
API_URL = "http://194.110.55.54:8082/data"

# Функция для расчета контрольной суммы
def calculate_checksum(data):
    return (~sum(data[1:25]) + 1) & 0xFF

# Функция отправки данных на сервер
def send_data_to_server(data):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(API_URL, json=data, headers=headers)
        if response.status_code == 200:
            print("✅ Данные успешно отправлены:", response.json())
        else:
            print(f"❌ Ошибка при отправке: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print("❌ Ошибка соединения:", e)

# Функция чтения данных с датчика Winsen
def read_sensor_data(serial_port):
    values = bytearray([0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79])
    serial_port.write(values)
    res = serial_port.read(26)

    if len(res) < 26:
        print("⚠ Incomplete data received")
        return

    checksum = calculate_checksum(res)
    if checksum != res[25]:
        print("❌ Checksum error: data may be corrupted")
        return

    data = {
        "pm1": res[2] * 256 + res[3],
        "pm25": res[4] * 256 + res[5],
        "pm10": res[6] * 256 + res[7],
        "co2": res[8] * 256 + res[9],
        "voc": res[10],
        "temp": ((res[11] * 256 + res[12]) - 500) * 0.1,
        "hum": res[13] * 256 + res[14],
        "ch2o": (res[15] * 256 + res[16]) * 0.001,
        "co": (res[17] * 256 + res[18]) * 0.1,
        "o3": (res[19] * 256 + res[20]) * 0.01,
        "no2": (res[21] * 256 + res[22]) * 0.01
    }

    print(json.dumps(data, indent=4))
    send_data_to_server(data)

# Основной цикл работы
try:
    s = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)  # Укажите правильный порт
    print("✅ Подключение к датчику установлено!")

    while True:
        read_sensor_data(s)
        time.sleep(5)  # Интервал между запросами

except serial.SerialException:
    print("❌ Ошибка: невозможно открыть COM-порт")
except KeyboardInterrupt:
    print("🛑 Программа остановлена пользователем")
finally:
    if 's' in locals() and s.is_open:
        s.close()