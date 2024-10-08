import serial
import time
import pymysql
import sys  # 사용자 ID를 인자로 받기 위해 추가
from datetime import datetime

DEVICE = 'COM7'
BAUDRATE = 38400

def open_serial():
    try:
        ser = serial.Serial(DEVICE, BAUDRATE, timeout=1)
        if ser.is_open:
            print(f"Serial port {DEVICE} opened successfully")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port {DEVICE}: {e}")
        exit(1)

def close_serial(ser):
    if ser.is_open:
        ser.close()
        print(f"Serial port {DEVICE} closed")

def conv_value(n):
    val = (n & 0xF0) >> 4
    val = val * 10 + (n & 0x0F)
    return val

def read_data(ser):
    ser.flushInput()

    while True:
        byte = ser.read(1)
        if byte and byte[0] == 0xFA:
            break

    data = ser.read(10)
    return data

def save_to_database(avg_hr, avg_spo2, measurement_date, user_id):
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='choi',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # SensorData 테이블에 데이터 삽입 (user_id 포함)
            sql = "INSERT INTO sensordata (hr, spo2, measurement_date, user_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (avg_hr, avg_spo2, measurement_date, user_id))

        connection.commit()
        print("Average values and user ID saved to the database successfully.")

    except Exception as e:
        print(f"Error saving data to the database: {e}")

    finally:
        connection.close()

def main():
    ser = open_serial()

    try:
        # 파라미터로부터 user_id 가져오기
          # 인자가 전달되지 않으면 기본값 설정 (예: user_id = 1)
        if len(sys.argv) > 1:
            user_id = sys.argv[1]
        else:
            user_id = 1  # 기본 사용자 ID를 설정

        # 5초 동안 측정된 HR, SPO2 값을 저장할 리스트
        hr_values = []
        spo2_values = []

        for _ in range(5):
            data = read_data(ser)

            if len(data) < 6:
                print("Data read error")
                continue

            hr = conv_value(data[2]) * 100 + conv_value(data[3])
            spo2 = conv_value(data[4]) * 100 + conv_value(data[5])

            hr_values.append(hr)
            spo2_values.append(spo2)

            print(f"HR: {hr}, SPO2: {spo2}")
            time.sleep(1)

        avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
        avg_spo2 = sum(spo2_values) / len(spo2_values) if spo2_values else 0

        # 현재 날짜를 구해서 저장
        measurement_date = datetime.now().date()

        # 평균값과 사용자 ID를 데이터베이스에 저장
        save_to_database(avg_hr, avg_spo2, measurement_date, user_id)

    except KeyboardInterrupt:
        close_serial(ser)

if __name__ == '__main__':
    main()