import serial
import time
import pymysql
from datetime import datetime  # 날짜 모듈 추가

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
    ser.flushInput()  # 버퍼 초기화

    while True:
        byte = ser.read(1)
        if byte and byte[0] == 0xFA:
            break

    data = ser.read(10)
    return data

def save_to_database(avg_hr, avg_spo2, measurement_date):
    # MySQL 데이터베이스에 연결 (필요에 맞게 데이터베이스 정보 수정)
    connection = pymysql.connect(
        host='localhost',           # 데이터베이스 호스트 (로컬일 경우 localhost)
        user='root',       # MySQL 사용자 이름
        password='1234',   # MySQL 사용자 비밀번호
        database='choi',   # 데이터베이스 이름
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # SensorData 테이블에 데이터 삽입, 날짜 포함
            sql = "INSERT INTO sensordata (hr, spo2, measurement_date) VALUES (%s, %s, %s)"
            cursor.execute(sql, (avg_hr, avg_spo2, measurement_date))
        
        # 변경 사항 저장 (commit)
        connection.commit()
        print("Average values and date saved to the database successfully.")
    
    except Exception as e:
        print(f"Error saving data to the database: {e}")
    
    finally:
        connection.close()

def main():
    ser = open_serial()

    try:
        # 5초 동안 측정된 HR, SPO2 값을 저장할 리스트
        hr_values = []
        spo2_values = []

        for _ in range(5):  # 1초 간격으로 5번 데이터를 읽음
            data = read_data(ser)

            if len(data) < 6:
                print("Data read error")
                continue

            # HR (맥박) 및 SPO2 (산소포화도) 값 추출
            hr = conv_value(data[2]) * 100 + conv_value(data[3])
            spo2 = conv_value(data[4]) * 100 + conv_value(data[5])

            # 측정된 값 리스트에 저장
            hr_values.append(hr)
            spo2_values.append(spo2)

            print(f"HR: {hr}, SPO2: {spo2}")

            time.sleep(1)  # 1초 간격으로 데이터 읽기

        # 5초 동안 측정된 HR, SPO2 값의 평균 계산
        avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
        avg_spo2 = sum(spo2_values) / len(spo2_values) if spo2_values else 0

        # 현재 날짜를 구해서 저장
        measurement_date = datetime.now().date()

        # 평균값과 날짜를 데이터베이스에 저장
        save_to_database(avg_hr, avg_spo2, measurement_date)

    except KeyboardInterrupt:
        # 프로그램 종료 시 시리얼 포트 닫기
        close_serial(ser)

if __name__ == '__main__':
    main()
