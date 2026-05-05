import time

import smbus
import pymysql.cursors
from imusensor.MPU9250 import MPU9250

import redis
REDIS = redis.Redis(host='127.0.0.1', port=6379, db=1)
ReaderHashKey = "imu_data_times"

def caliberate():
    # Initialize the MPU-6050 sensor
    address = 0x68 # 設定 MPU9250 IMU 的 I2C 地址為 0x68。
    bus = smbus.SMBus(1) # 初始化 I2C 通訊，使用的 bus 數字可能會因系統而異，這裡是用 1。
    imu = MPU9250.MPU9250(bus, address) # 通過 MPU9250.MPU9250() 建立 MPU9250 物件，並傳入之前設定的 I2C 地址和初始化的 I2C 通訊 bus。
    imu.begin() # 初始化 IMU。
    imu.caliberateGyro() # 執行陀螺儀的校準。
    imu.caliberateAccelerometer() # 執行加速度計的校準。
    print("Accel Success")
    imu.caliberateMagApprox() # 執行磁力計的校準。
    print("Mag Success")

    imu.saveCalibDataToFile("./calib.json") # 將校準資料保存到一個 JSON 檔案
    print("calib data saved")

    imu.loadCalibDataFromFile("./calib.json") # 從之前保存的 JSON 檔案中載入校準資料。

    dt = 0.02 # 時間間隔，每0.02秒執行一次
    times = 0 # IMU數據存入次數，確認最新存入的數據是第幾筆
    REDIS.delete('accel_x')
    REDIS.delete('accel_y')
    REDIS.delete('accel_z')
    REDIS.delete('gyro_x')
    REDIS.delete('gyro_y')
    REDIS.delete('gyro_z')
    
    while True:
        imu_start = time.process_time() 
        imu.readSensor() # 讀取 IMU 數據
        imu.computeOrientation() #　計算 MPU9250 IMU（Inertial Measurement Unit）的姿態（orientation）

        accel_x, accel_y, accel_z = imu.AccelVals[0], imu.AccelVals[1], imu.AccelVals[2]
        gyro_x, gyro_y, gyro_z = imu.GyroVals[0], imu.GyroVals[1], imu.GyroVals[2]
        mag_x, mag_y, mag_z = imu.MagVals[0], imu.MagVals[1], imu.MagVals[2]
        roll, pitch, yaw = imu.roll, imu.pitch, imu.yaw
        times = times + 1
        time_str = str(times)
        print(time_str)
        REDIS.hset('imu_data_times', 'imu_data_times', times)
        REDIS.hset('accel_x', time_str, accel_x)
        REDIS.hset('accel_y', time_str, accel_y)
        REDIS.hset('accel_z', time_str, accel_z)
        REDIS.hset('gyro_x', time_str, gyro_x)
        REDIS.hset('gyro_y', time_str, gyro_y)
        REDIS.hset('gyro_z', time_str, gyro_z)
        
        imu_end = time.process_time()
        imu_time = imu_end - imu_start
        time.sleep(0.02)


if __name__ == "__main__":
    caliberate()
