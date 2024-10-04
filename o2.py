import serial
import time
import requests  # requests 라이브러리 추가
import json

# 시리얼 포트 설정 (윈도우에서는 COM 포트를 사용, 장치에 맞는 COM 포트를 설정)
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
    # 값 변환 함수 (C 코드와 동일한 방식으로 변환)
    val = (n & 0xF0) >> 4
    val = val * 10 + (n & 0x0F)
    return val

def read_data(ser):
    # 시리얼 장치에서 데이터 읽기
    ser.flushInput()  # 버퍼 초기화

    while True:
        # 데이터를 1바이트씩 읽고 0xFA로 시작하는지 확인
        byte = ser.read(1)
        if byte and byte[0] == 0xFA:
            break

    # 시작 바이트 확인 후 나머지 데이터 읽기 (10바이트)
    data = ser.read(10)
    return data

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

        # 평균 값 출력
        print(f"{avg_hr}")  # 예: 86.8
        print(f"{avg_spo2}")  # 예: 96.5

        
        # 평균값을 Spring Boot API로 전송
        payload = {
            "hr": avg_hr,
            "spo2": avg_spo2
        }
        response = requests.post("http://localhost:8080/sensor-data", json=payload)

        # 응답 확인
        if response.status_code == 200:
            print("Average values sent successfully.")
        else:
            print(f"Failed to send average values: {response.status_code}")

    except KeyboardInterrupt:
        # 프로그램 종료 시 시리얼 포트 닫기
        close_serial(ser)

if __name__ == '__main__':
    main()
