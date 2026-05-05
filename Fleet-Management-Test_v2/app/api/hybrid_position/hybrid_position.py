import os
import sys
import time
import smbus
import numpy as np
import pymysql.cursors
import redis
import json
from imusensor.MPU9250 import MPU9250
from typing import Optional
import pandas as pd
import math
import scipy.linalg
from scipy.stats import ks_2samp
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist, squareform
from copy import deepcopy
from threading import Lock
from scipy import linalg as lin
from sympy import Symbol
from sympy.solvers import solve
from sqlalchemy import create_engine
import time

REDIS = redis.Redis(host='127.0.0.1', port=6379, db=1)
ReaderHashKey = "User"
READER_ANTENNA_1 = ReaderHashKey + "_RFID1"
READER_ANTENNA_2 = ReaderHashKey + "_RFID2"
IMUHashKey ="imu_data"
coordinate_HashKey ="coordinate"

MAG_TRAIN_FILE_PATH = "mag_collect_data.csv"

RFID_TRAIN_FILE_PATH ="rfid_field.csv"
rfid_tag_df = pd.read_csv(RFID_TRAIN_FILE_PATH)
rfid_list = list(rfid_tag_df['rfid_id'])

###設定卡爾曼濾波的參數
np.set_printoptions(precision=3)

# Process Noise 
q = np.eye(4)
q[0][0] = 1   #X軸位置的誤差
q[1][1] = 1   #y軸位置的誤差
q[2][2] = 0.0001   #heading的誤差
q[3][3] = 0.0001   #velocity的誤差

# create measurement noise covariance matrices
r_rfid = np.zeros([2, 2])
r_rfid[0][0] = 0.1     #X軸位置的誤差
r_rfid[1][1] = 0.1     #y軸位置的誤差

r_mag = np.zeros([2, 2])
r_mag[0][0] = 4      #X軸位置的誤差
r_mag[1][1] = 4      #y軸位置的誤差

# initializing list 
lst = [3,1, 0, 0]
# converting list to array
init_arr = np.array(lst)

hybrid_list = []

d_time = 0.02 # 時間間隔
###設定卡爾曼濾波的參數

#從redis資料庫取出hash的key與value
def redis_get_imu_data(sensor_data):
    key_dict = REDIS.hgetall(sensor_data)

    key_dict = {k.decode('utf-8'): float(v.decode('utf-8')) for k, v in key_dict.items()}
    # print("key_dict:", key_dict)

    return key_dict
    
def redis_get_rfid_data(sensor_data):
    key_dict = REDIS.hgetall(sensor_data)

    key_dict = {k.decode('utf-8'): int(v.decode('utf-8')) for k, v in key_dict.items()}

    # print("key_dict:", key_dict)

    return key_dict

def redis_truncate(rfid_reader):
    REDIS.delete(rfid_reader)

def main():
    global lst
    global heading
    global velocity
    accel_x_list = []
    accel_y_list = [] 
    accel_z_list = []
    gyro_x_list = []
    gyro_y_list = []
    gyro_z_list = []
    imu_times_old = 0
    initialization = False
    hybrid_position_count = 0
    try:
        state_estimator = UKF(4, q, init_arr, 0.1*np.eye(4), 0.04, 0.0, 2.0, iterate_x)#建立卡爾曼律波模型，處理RFID定位、與航位推測法的混合定位
        mag_model = MagneticModel() 
        while(True):
            hybrid_start = time.process_time()
            hybrid_position_count = hybrid_position_count + 1  # 計算混合定位的次數

            left_rfid_dict = redis_get_rfid_data(READER_ANTENNA_1) # 取出左側讀取到的RFID Tag訊號
            right_rfid_dict = redis_get_rfid_data(READER_ANTENNA_2) # 取出右側讀取到的RFID Tag訊號
            # redis_truncate(READER_ANTENNA_1)
            # redis_truncate(READER_ANTENNA_2)

            imu_data_times = REDIS.hget('imu_data_times', 'imu_data_times') #取得最新存到Redis資料庫的imu數據是第幾筆數據
            if imu_data_times  is not None: 
                imu_times_new = int(imu_data_times.decode())
            
            if bool(left_rfid_dict) and bool(left_rfid_dict): #若左右rfid天線皆有讀取到 rfid tag
                # rfid_start = time.process_time()
                left_xy_df,right_xy_df,left_rfid_list,right_rfid_list = rfid_tag_processing(left_rfid_dict,right_rfid_dict)
                redis_truncate(READER_ANTENNA_1)
                redis_truncate(READER_ANTENNA_2)
                if len(left_rfid_list) != 0 and len(right_rfid_list) != 0 : 
                    rfid_x_position, rfid_y_position = rfid_positioning(left_xy_df,right_xy_df,left_rfid_list,right_rfid_list)
                    #計算rfid定位 
                    if  rfid_x_position != None and rfid_y_position != None:
                        rfid_x_position = float(rfid_x_position)
                        rfid_y_position = float(rfid_y_position)
                        rfid_data = np.array([rfid_x_position,rfid_y_position])
                        
                        # rfid_end = time.process_time()
                        # rfid_time = rfid_end - rfid_start
                        # print("rfid定位執行時間：%f 秒" % (rfid_time))
                        state_estimator.update([0, 1], rfid_data, r_rfid)
                        hybrid_x_position = state_estimator.get_state(0)
                        hybrid_y_position = state_estimator.get_state(1)
                        print("hybrid_x_position",hybrid_x_position)
                        print("hybrid_y_position",hybrid_y_position)
                        # hybrid_position_count_str = str(hybrid_position_count)
                        # REDIS.hset('hybrid_count', 'hybrid_count', hybrid_position_count)
                        # REDIS.hset('coordinate_x',hybrid_position_count_str, hybrid_x_position)
                        # REDIS.hset('coordinate_y',hybrid_position_count_str, hybrid_y_position)
                        localtime = time.localtime()
                        current_time = time.strftime("%Y-%m-%d %I:%M:%S %p", localtime)
                        sql = "INSERT INTO `app_vehicle_state` (" \
                                "`update_time`,`coordinate_x`,`coordinate_y`" \
                                ") VALUES (" \
                                "{0}, {1}, {2}" \
                                ")".format(
                                current_time,hybrid_x_position,hybrid_y_position
                                )
                        dbh = MySQL()
                        result = dbh.execute(sql)
                        dbh.close()
                        

            imu_times_new =  imu_times_new//10
            if initialization:
                if imu_times_new > imu_times_old:
                    #航位推測法
                    # dr_start = time.process_time()
                    # 10,判斷式(老師的solution：缺幾個算幾個)
                    for i in range(imu_times_old,imu_times_new,1):
                        r = (10*i)+1
                        m = r + 10 
                        for j in range(r,m,1):
                            accel_x_r = REDIS.hget('accel_x', str(j))
                            accel_y_r = REDIS.hget('accel_y', str(j))
                            accel_z_r = REDIS.hget('accel_z', str(j))
                            gyro_x_r = REDIS.hget('gyro_x', str(j))
                            gyro_y_r = REDIS.hget('gyro_y', str(j))
                            gyro_z_r = REDIS.hget('gyro_z', str(j))
                            
                            # 不要用平均值
                            if accel_x_r is not None:                      
                                accel_x = float(accel_x_r.decode())
                            if accel_y_r is not None: 
                                accel_y = float(accel_y_r.decode())
                            if accel_z_r is not None:
                                accel_z = float(accel_z_r.decode())
                            if gyro_x_r is not None: 
                                gyro_x = float(gyro_x_r.decode())
                            if gyro_y_r is not None: 
                                gyro_y = float(gyro_y_r.decode())
                            if gyro_z_r is not None: 
                                gyro_z = float(gyro_z_r.decode())
                            

                            if len(accel_x_list) < 1000:
                                # 數據太多，會影響即時性                    
                                accel_x_list.append(accel_x)
                                accel_y_list.append(accel_y)
                                accel_z_list.append(accel_z)
                                gyro_x_list.append(gyro_x)
                                gyro_y_list.append(gyro_y)
                                gyro_z_list.append(gyro_z)
                        
                        
                            acc_list = [accel_x_list,accel_y_list,accel_z_list]
                            gyro_list = [gyro_x_list ,gyro_y_list ,gyro_z_list]
                            acc_total = np.array(acc_list)
                            gyro_total = np.array(gyro_list)                    
                            acc_s = np.array([[accel_x],[accel_y],[accel_z]])
                            gyro_s = np.array([[gyro_x],[gyro_y],[gyro_z]])

                            
                            velocity,heading = dead_rocking(acc_s,gyro_s,acc_mean,gyro_bias,acc_total,gyro_total,d_time)
                            #執行航位推測法        
                            
                            imu_x_position = state_estimator.get_state(0)
                            imu_y_position = state_estimator.get_state(1)
                            #取得X、Y位置
                            real_state = np.array([imu_x_position,imu_y_position,heading,velocity])
                            state_estimator.predict(d_time,real_state)
                            #執行卡爾曼濾波數據預測

                            hybrid_x_position = state_estimator.get_state(0)
                            hybrid_y_position = state_estimator.get_state(1)
                            
                            print("hybrid_x_position",hybrid_x_position)
                            print("hybrid_y_position",hybrid_y_position)
                            # hybrid_position_count_str = str(hybrid_position_count)
                            # REDIS.hset('hybrid_count', 'hybrid_count', hybrid_position_count)
                            # REDIS.hset('coordinate_x',hybrid_position_count_str, hybrid_x_position)
                            # REDIS.hset('coordinate_y',hybrid_position_count_str, hybrid_y_position)

                            ###將定位結果傳入資料庫
                            localtime = time.localtime()
                            current_time = time.strftime("%Y-%m-%d %I:%M:%S %p", localtime)
                            sql = "INSERT INTO `app_vehicle_state` (" \
                                    "`update_time`,`coordinate_x`,`coordinate_y`" \
                                    ") VALUES (" \
                                    "{0}, {1}, {2}" \
                                    ")".format(
                                    current_time,hybrid_x_position,hybrid_y_position
                                    )
                            dbh = MySQL()
                            result = dbh.execute(sql)
                            dbh.close()
                            ###將定位結果傳入資料庫
                            ##航位推測法
                          
            else:
                #　測試初始化條件：20筆,30筆
                if imu_times_new > 50:
                    imu_times_init = imu_times_new - 50
                    for i in range(imu_times_init,imu_times_new,1):
                        accel_x = REDIS.hget('accel_x', str(i))
                        accel_y = REDIS.hget('accel_y', str(i))
                        accel_z = REDIS.hget('accel_z', str(i))
                        gyro_x = REDIS.hget('gyro_x', str(i))
                        gyro_y = REDIS.hget('gyro_y', str(i))
                        gyro_z = REDIS.hget('gyro_z', str(i))
                        if accel_x is not None:                      
                            accel_x_list.append(float(accel_x.decode()))
                        if accel_y is not None: 
                            accel_y_list.append(float(accel_y.decode()))
                        if accel_z is not None:
                            accel_z_list.append(float(accel_z.decode()))
                        if gyro_x is not None: 
                            gyro_x_list.append(float(gyro_x.decode()))
                        if gyro_y is not None: 
                            gyro_y_list.append(float(gyro_y.decode()))
                        if gyro_z is not None: 
                            gyro_z_list.append(float(gyro_z.decode()))

                        
                    acc_list = [accel_x_list,accel_y_list,accel_z_list]
                    gyro_list = [gyro_x_list ,gyro_y_list ,gyro_z_list]
                    acc_total = np.array(acc_list)
                    gyro_total = np.array(gyro_list)
                    acc_mean = np.mean(acc_total[:,0:50], 1)
                    gyro_mean = np.mean(gyro_total[:,0:50], 1) #gyro_mean計算前50筆加速度'gyro_x', 'gyro_y', 'gyro_z'的平均值
                    gyro_bias = np.matrix([gyro_mean[0], gyro_mean[1], gyro_mean[2]]).T  #以加速度'gyro_x', 'gyro_y', 'gyro_z'的平均值建立3X1的矩陣
                    initialization = True
                    imu_data_times = REDIS.hget('imu_data_times', 'imu_data_times') #取得最新存到Redis資料庫的imu數據是第幾筆數據
                    if imu_data_times  is not None: 
                        imu_times_new_r = int(imu_data_times.decode())
                        imu_times_new =  imu_times_new_r // 10
                    print("initialization")
            
            imu_times_old = imu_times_new #更新次數                
            
            hybrid_end = time.process_time()
            dt = hybrid_end - hybrid_start
            print("hybrid_time",dt)
            if dt < 0.2:
                timestamp = 0.2 - dt
                time.sleep(timestamp)
                dt = 0.2

        
    except KeyboardInterrupt:
        print("Exiting...")


            


### MySQL資料庫存取
class MySQL:
    def __init__(self):
        super(MySQL, self).__init__()

        self.connection = pymysql.connect(
            host="127.0.0.1",
            user="root",
            password="eS414o6kdd",
            db="indoor_position",
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def connect(self, host, user, password, db):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def reconnect(self, DB_CONFIG):
        self.connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        result = cursor.execute(sql)
        connection.commit()
        response = {
            'result': result,
            'sn': cursor.lastrowid
        }

        return response

    def query(self, state):
        connection = self.connection
        with connection.cursor() as cursor:
            cursor.execute(state)
            result = cursor.fetchall()

        return result

    def ping(self):
        self.connection.ping(reconnect=True)

    def close(self):
        self.connection.close()

###地磁定位使用函數
def init_start_point(point_df):
    # 使用 scipy 的 pdist 函式來計算所有點之間的歐氏距離
    distances = pdist(point_df.values, metric='euclidean')

    # pdist 回傳的是一個 condensed distance matrix，
    # 我們可以使用 squareform 函式將其轉換為一個對稱的矩陣
    dist_matrix = squareform(distances)
    index = pd.DataFrame(dist_matrix).sum().idxmin()
    return point_df.iloc[index]['x'], point_df.iloc[index]['y']

    
def init_start_yaw(point_df):
    # 使用 scipy 的 pdist 函式來計算所有點之間的歐氏距離
    distances = pdist(point_df.values, metric='euclidean')
    # pdist 回傳的是一個 condensed distance matrix，
    # 我們可以使用 squareform 函式將其轉換為一個對稱的矩陣
    dist_matrix = squareform(distances)
    index = pd.DataFrame(dist_matrix).sum().idxmin()
    return point_df.iloc[index]['yaw']

class MagneticModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MagneticModel, cls).__new__(cls)
            cls._instance._is_started = False
        return cls._instance

    def __init__(self):
        if (self._is_started): return
        self.magnetic_field_raw_df = None
        self.magnetic_field_df = None
        self.fingerprint_df = None
        self.scaler = None
        self._instance = True

    def read_fingerprint_DB_to_df(self):
        try:
            column_names = [
                "axis_x", "axis_y",
                "mag_x", "mag_y", "mag_z", "datetime"
            ]
            
            # engine = create_engine('mysql://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format("root","eS414o6kdd","127.0.0.1",3306,"indoor_position"))
            
            # sql = (
            #  "SELECT `axis_x`,`axis_y`,`mag_x`,`mag_y`,`mag_z` FROM `magnetic_field`"      
            #  )
            # fingerprint_df = pd.read_sql(sql, engine)
            fingerprint_df = pd.read_csv( "mag_collect_data.csv", names=column_names, header=0)
            
            fingerprint_df['intensity'] = (
                fingerprint_df['mag_x'].pow(2)+
                fingerprint_df['mag_y'].pow(2)+
                fingerprint_df['mag_z'].pow(2)
            ).pow(0.5)
            

            self.magnetic_field_raw_df = fingerprint_df.copy()
            self.fingerprint_df = fingerprint_df
            return True
        except BaseException as e:
            print("ERROR: read_fingerprint_DB_to_df:", e)
            return False
    
    def remove_test_noise(self, df):
        
        scaler = StandardScaler().fit(df[['mag_z']])
        X_scaled = scaler.transform(df[['mag_z']])
        df[['std_mag_z']] = X_scaled
        
        df = df.loc[
            ((df['std_mag_z'] < 2) & (df['std_mag_z'] > -2))
        ]
        
        return df
    
    def remove_train_noise(self, df):
        df[['std_mag_z']] = df[[
           'axis_x', 'axis_y', 'mag_z'
        ]].groupby(['axis_x', 'axis_y']).transform(
            lambda x: StandardScaler().fit_transform(x.values[:,np.newaxis]).ravel()
        )

        df = df.loc[((df['std_mag_z'] < 2) & (df['std_mag_z'] > -2))]

        return df
        
    def data_processing(self):
        # print(type(self.fingerprint_df))
        mag_df = self.fingerprint_df
        # print("mag_df",mag_df)
        mag_df = self.remove_train_noise(mag_df)

        self.scaler = StandardScaler().fit(mag_df[['mag_z']])
        X_scaled = self.scaler.transform(mag_df[['mag_z']])
        
        pd.options.mode.chained_assignment = None
        mag_df[['mag_z']] = X_scaled
        
        self.magnetic_field_df = mag_df
        self.fingerprint_df = mag_df.groupby(['axis_x', 'axis_y'])[['mag_z']].mean().reset_index()

    def fingerprint_KNN(self, mag_list, k=1, t=0):
        # Read data in database
        if self.magnetic_field_df is None:
            self.read_fingerprint_DB_to_df()
            self.data_processing()
        
        mag_list = self.remove_test_noise(mag_list)

        pd.options.mode.chained_assignment = None
        mag_list[['mag_z']] = self.scaler.transform(mag_list[['mag_z']])
        #　mag_list[['mag_z']] = self.scaler.transform(mag_list[['mag_z']])

        pvalue_list = []
        for num, row in self.magnetic_field_df.groupby(['axis_x', 'axis_y']):
            pvalue = ks_2samp(row['mag_z'].values, mag_list['mag_z'].values).pvalue
            pvalue_list.append({
                'x':num[0],
                'y':num[1],
                'pvalue':pvalue,
            })
        
        pvalue_df = pd.DataFrame(pvalue_list)
        top_k_pvalue_df = pvalue_df.nlargest(k, 'pvalue')
        # print("top_k_pvalue_df:", top_k_pvalue_df)
        
        sum_pvalue = top_k_pvalue_df['pvalue'].sum()
        
        top_k_pvalue_df['cal_x'] = top_k_pvalue_df['x'] * (top_k_pvalue_df['pvalue']/sum_pvalue)
        top_k_pvalue_df['cal_y'] = top_k_pvalue_df['y'] * (top_k_pvalue_df['pvalue']/sum_pvalue)

        x = top_k_pvalue_df['cal_x'].sum()
        y = top_k_pvalue_df['cal_y'].sum()
        # print("============")
        
        return x, y
        # Init model
        #建立地磁模型

def dead_rocking(acc_s,gyro_s,acc_mean,gyro_bias,acc_total,gyro_total,dt): #航位推測法
    # Error covariance matrix.建立矩陣
    P = np.zeros((9,9))

    # Process noise parameter, gyroscope and accelerometer noise.
    sigma_omega = 0.0006
    sigma_a = 0.003

    # ZUPT measurement matrix.
    H = np.block([
        [np.zeros((3,3)), np.zeros((3,3)), np.eye((3))],
    ])
    #np.block 用于按照给定的块配置将多个 NumPy 数组或矩阵连接在一起，以创建一个新的数组或矩阵
    G = 9.7 #Gravity
    g_array = np.array([[0, 0, G]]).T

    # acc_s = np.array([[accel_x],[accel_y],[accel_z]])
    # gyro_s = np.array([[gyro_x],[gyro_y],[gyro_z]])

    acc_len = len(acc_s)#3
    gyro_len = len(gyro_s)#3



   
    init_a = acc_mean
    pitch = -np.arcsin(init_a[0]/G)
    roll = np.arctan(init_a[1]/init_a[2])
    yaw = -0.3

    # Orientation Matrix (this is already C.T) 方向矩陣
    C = np.array([
        [np.cos(pitch)*np.cos(yaw), (np.sin(roll)*np.sin(pitch)*np.cos(yaw))-(np.cos(roll)*np.sin(yaw)), (np.cos(roll)*np.sin(pitch)*np.cos(yaw))+(np.sin(roll)*np.sin(yaw))],
        [np.cos(pitch)*np.sin(yaw), (np.sin(roll)*np.sin(pitch)*np.sin(yaw))+(np.cos(roll)*np.cos(yaw)), (np.cos(roll)*np.sin(pitch)*np.sin(yaw))-(np.sin(roll)*np.cos(yaw))],
        [-np.sin(pitch), np.sin(roll)*np.cos(pitch), np.cos(roll)*np.cos(pitch)]
        ])

    C_prev = C

    imd_datasize = 1
    
    # Create arrays to storage some data
    heading = np.zeros((1, imd_datasize))
    heading[0,0] = 0.0

    # Preallocate storage for accelerations in navigation frame.
    acc_n = np.zeros((3, imd_datasize))
    acc_n[:,0] = C@acc_s[:,0]
    # print("acc_n",acc_n)


    # Preallocate storage for velocity (in navigation frame).
    # Initial velocity assumed to be zero.
    vel_n = np.zeros((3, imd_datasize)) 

    # Preallocate storage for position (in navigation frame).
    # Initial position arbitrarily set to the origin.
    pos_n = np.zeros((3, imd_datasize))

    # Preallocate storage for distance travelled used for altitude plots.
    distance = np.zeros((1, imd_datasize))

    # ZUPT measurement noise covariance matrix.
    sigma_v = 0.01
    R = np.diag([sigma_v, sigma_v, sigma_v])**2

    # Stance detection starts here
    # Compute accelerometer magnitude
    acc_mag =np.around(np.sqrt(acc_s[0]**2 + acc_s[1]**2 + acc_s[2]**2), decimals=4)
    # Compute gyroscope magnitude
    gyro_mag = np.around(np.sqrt((gyro_s[0])**2 + (gyro_s[1])**2 + (gyro_s[2])**2), decimals=4)
    
    # Compute accelerometer magnitude
    acc_total_mag = np.around(np.sqrt(acc_total[0]**2 + acc_total[1]**2 + acc_total[2]**2), decimals=4)
    # Compute gyroscope magnitude
    gyro_total_mag = np.around(np.sqrt((gyro_total[0])**2 + (gyro_total[1])**2 + (gyro_total[2])**2), decimals=4)
    # #建立判斷式
    acc_stationary_threshold_H = np.quantile(acc_total_mag, 0.75)
    acc_stationary_threshold_L = np.quantile(acc_total_mag, 0.25)
    gyro_stationary_threshold = np.quantile(gyro_total_mag, 0.5)
  
    
    stationary_acc_H = (acc_mag < acc_stationary_threshold_H)
    stationary_acc_L = (acc_mag > acc_stationary_threshold_L)
    stationary_acc = np.logical_and(stationary_acc_H, stationary_acc_L) #C1
    stationary_gyro = (gyro_mag < gyro_stationary_threshold) #C2

    # print(stationary_acc_H)
    # print(stationary_acc_L)
    # print(stationary_acc)
    # print(stationary_gyro)
    stationary = np.logical_and(stationary_acc, stationary_gyro)

    # # print(stationary)
    # # this window is necessary to clean stationary array from false stance detection
    # print(stationary) 
    # W = 10
    # for k in range(imd_datasize-W+1):
    #     if (stationary[k] == True) and (stationary[k+W-1] == True):
    #         stationary[k:k+W] = np.ones((W))
    # print(stationary)   
    # for k in range(imd_datasize-W+1):
    #     if (stationary[k] == False) and (stationary[k+W-1] == False):
    #         stationary[k:k+W] = np.zeros((W))

    # print(stationary)
    # #建立判斷式
    # dt = 0.02

    # Remove bias from gyro measurements.
    gyro_s1 = gyro_s - gyro_bias
    ang_rate_matrix = np.array([[0,            -gyro_s1[2,0], gyro_s1[1,0]],
                                [gyro_s1[2,0],   0,           -gyro_s1[0,0]],
                                [-gyro_s1[1,0],  gyro_s1[0,0],   0]])
    # print(gyro_s1) 

    # Update the orientation estimation (4)
    C = C_prev@(2*np.eye(3)+(ang_rate_matrix*dt))@lin.inv((2*np.eye(3)-(ang_rate_matrix*dt)))
    # print("C",C)
    # Transforming the acceleration from sensor frame to navigation frame.
    acc_n = 0.5*(C + C_prev)@acc_s
    # print("acc_n",acc_n)
    # Skew-symmetric cross-product operator matrix formed from the n-frame accelerations.
    S = np.array([[0,           -acc_n[2,0],   acc_n[1,0]],
                [acc_n[2,0],  0,            -acc_n[0,0]],
                [-acc_n[1,0],  acc_n[0,0],   0]])
    # print("S",S)
    # Velocity and position estimation using trapeze integration. (6-7)
    vel_n = (vel_n + ((acc_n - g_array)+(acc_n - g_array))*dt/2)
    pos_n = (pos_n + (vel_n + vel_n)*dt/2)
    # print("vel_n",vel_n)
    # print("pos_n",pos_n)

    # State transition matrix (or fundamental matrix). (9)
    F = np.block([
            [np.eye((3)),     np.zeros((3,3)),    np.zeros((3,3))], # attitude
            [np.zeros((3,3)), np.eye((3)),        dt*np.eye((3))],  # position
            [-dt*S,           np.zeros((3,3)),    np.eye((3))]      # velocity
            ])
    # print("F:",F)
    Q = (np.diag([sigma_omega, sigma_omega, sigma_omega, 0, 0, 0, sigma_a, sigma_a, sigma_a])*dt)**2
    # print("Q:",Q)
    # Propagate the error covariance matrix.
    P = F@P@F.T + Q
    # print("P:",P)
    ### End INS ###
    # Zero-velocity updates.
    if (stationary):
        ### Start Kalman filter zero-velocity update %%%
        # Compute Kalman gain.
        K = P@H.T@lin.inv(H@P@H.T + R)
        # print("K:",K)
        # Compute the state errors state.
        # Update the filter state.
        delta_x = K@vel_n
        # print("delta_x:",delta_x)
        # Update the error covariance matrix
        P = (np.eye((9)) - K@H)@P
        # print("P:",P)
        # Extract errors from the KF state.
        attitude_error = delta_x[0:3]#[:,np.newaxis]
        pos_error = delta_x[3:6]#[:,np.newaxis]
        vel_error = delta_x[6:9]#[:,np.newaxis]
        ### End Kalman filter zero-velocity update ###
        # print(" attitude_error:", attitude_error)
        # print("pos_error:",pos_error)
        # print("vel_error:",vel_error)
        ### Apply corrections to INS estimates. ###
        # Skew-symmetric matrix for small angles to correct orientation.
        ang_matrix = -np.array([
                    [0,                   -attitude_error[2,0],   attitude_error[1,0]],
                    [attitude_error[2,0],  0,                      -attitude_error[0,0]],
                    [-attitude_error[1,0],  attitude_error[0,0],    0]
                    ])
        # print("ang_matrix:",ang_matrix)
        # Correct orientation estimation. (17)
        C = (2*np.eye(3)+(ang_matrix))@lin.inv((2*np.eye(3)-(ang_matrix)))@C
        # print("C:",C)
        # Correct position and velocity based on Kalman error estimates.
        vel_n =vel_n - vel_error
        pos_n =pos_n - pos_error
        # print("vel_n",vel_n)
        # print("pos_n",pos_n)
        
    heading[0,0] = np.arctan2(C[1,0], C[0,0]) # Estimate and save the yaw of the sensor (different from the direction of travel). Unused here but potentially useful for orienting a GUI correctly.
    C_prev = C # Save orientation estimate, required at start of main loop.

    # print("heading",heading)
    velocity = np.sqrt(np.square(vel_n[0]) + np.square(vel_n[1]) + np.square(vel_n[2]))

    # print("velocity",velocity)
    # 将数组的数据类型转换为整数
    velocity = velocity.astype(float)
    heading = heading.astype(float)
    heading = heading[0][0]
    velocity = velocity[0]
    #將串列的值取出，轉為變數

    angle = np.deg2rad(0)
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle), np.cos(angle)]
        ])
    pos_r = np.zeros((2,imd_datasize))
    pos_r= rotation_matrix@np.array([pos_n[0,0], pos_n[1,0]])
    # print(pos_r)

    return velocity,heading



###卡爾曼濾波
class UKF:
    def __init__(self, num_states, process_noise, initial_state, initial_covar, alpha, k, beta, iterate_function):
        """
        Initializes the unscented kalman filter
        :param num_states: int, the size of the state
        :param process_noise: the process noise covariance per unit time, should be num_states x num_states
        :param initial_state: initial values for the states, should be num_states x 1
        :param initial_covar: initial covariance matrix, should be num_states x num_states, typically large and diagonal
        :param alpha: UKF tuning parameter, determines spread of sigma points, typically a small positive value
        :param k: UKF tuning parameter, typically 0 or 3 - num_states
        :param beta: UKF tuning parameter, beta = 2 is ideal for gaussian distributions
        :param iterate_function: function that predicts the next state
                    takes in a num_states x 1 state and a float timestep
                    returns a num_states x 1 state
        """
        self.n_dim = int(num_states)                 # dim為維度
        self.n_sig = 1 + num_states * 2              # sigma的數量為2L+1
        self.q = process_noise                       # 預測過程誤差 
        self.x = initial_state                       # 初始狀態
        self.p = initial_covar                       # 初始誤差
        self.beta = beta                             # UKF中beta參數
        self.alpha = alpha                           # UKF中alpha參數
        self.k = k                                   # UKF中K參數
        self.iterate = iterate_function

        self.lambd = pow(self.alpha, 2) * (self.n_dim + self.k) - self.n_dim  # UKF中的scaling parameter

        self.covar_weights = np.zeros(self.n_sig)
        #建立變異數的權重之零矩陣
        self.mean_weights = np.zeros(self.n_sig)
        #建立平均值的權重之零矩陣

        self.covar_weights[0] = (self.lambd / (self.n_dim + self.lambd)) + (1 - pow(self.alpha, 2) + self.beta)
        #設定變異數的權重

        self.mean_weights[0] = (self.lambd / (self.n_dim + self.lambd))
        #設定找出平均值所需的權重

        for i in range(1, self.n_sig):
            self.covar_weights[i] = 1 / (2*(self.n_dim + self.lambd))
            self.mean_weights[i] = 1 / (2*(self.n_dim + self.lambd))

        self.sigmas = self.__get_sigmas()

        self.lock = Lock()

    def __get_sigmas(self):
        """generates sigma points"""
        ret = np.zeros((self.n_sig, self.n_dim))

        tmp_mat = (self.n_dim + self.lambd)*self.p

        # print spr_mat
        spr_mat = scipy.linalg.sqrtm(tmp_mat)

        ret[0] = self.x
        for i in range(self.n_dim):
            ret[i+1] = self.x + spr_mat[i]
            ret[i+1+self.n_dim] = self.x - spr_mat[i]

        return ret.T
        
    def update(self, states, data, r_matrix):
        """
        performs a measurement update
        :param states: list of indices (zero-indexed) of which states were measured, that is, which are being updated
        :param data: list of the data corresponding to the values in states
        :param r_matrix: error matrix for the data, again corresponding to the values in states
        """

        self.lock.acquire()

        num_states = len(states)

        # create y, sigmas of just the states that are being updated
        sigmas_split = np.split(self.sigmas, self.n_dim)
        y = np.concatenate([sigmas_split[i] for i in states])

        # create y_mean, the mean of just the states that are being updated
        x_split = np.split(self.x, self.n_dim)
        y_mean = np.concatenate([x_split[i] for i in states])

        # differences in y from y mean
        y_diff = deepcopy(y)
        x_diff = deepcopy(self.sigmas)
        for i in range(self.n_sig):
            for j in range(num_states):
                y_diff[j][i] -= y_mean[j]
            for j in range(self.n_dim):
                x_diff[j][i] -= self.x[j]
        

        # covariance of measurement
        p_yy = np.zeros((num_states, num_states))
        for i, val in enumerate(np.array_split(y_diff, self.n_sig, 1)):
            p_yy += self.covar_weights[i] * val.dot(val.T)

        # add measurement noise
        p_yy += r_matrix

        # covariance of measurement with states
        p_xy = np.zeros((self.n_dim, num_states))
        for i, val in enumerate(zip(np.array_split(y_diff, self.n_sig, 1), np.array_split(x_diff, self.n_sig, 1))):
            p_xy += self.covar_weights[i] * val[1].dot(val[0].T)

        k = np.dot(p_xy, np.linalg.inv(p_yy))

        y_actual = data

        # self.x += np.dot(k, (y_actual - y_mean))
        self.x = self.x + np.dot(k, (y_actual - y_mean))
        self.p -= np.dot(k, np.dot(p_yy, k.T))
        self.sigmas = self.__get_sigmas()

        self.lock.release()

    def predict(self, timestep, inputs=[]):
        """
        performs a prediction step
        :param timestep: float, amount of time since last prediction
        """

        self.lock.acquire()
        # print("predict start")
        sigmas_out = np.array([self.iterate(x, timestep, inputs) for x in self.sigmas.T]).T

        x_out = np.zeros(self.n_dim)

        # for each variable in X
        for i in range(self.n_dim):
            # the mean of that variable is the sum of
            # the weighted values of that variable for each iterated sigma point
            x_out[i] = sum((self.mean_weights[j] * sigmas_out[i][j] for j in range(self.n_sig)))

        p_out = np.zeros((self.n_dim, self.n_dim))
        # for each sigma point

        for i in range(self.n_sig):
            # take the distance from the mean
            # make it a covariance by multiplying by the transpose
            # weight it using the calculated weighting factor
            # and sum
            diff = sigmas_out.T[i] - x_out
            diff = np.atleast_2d(diff)
            p_out += self.covar_weights[i] * np.dot(diff.T, diff)

        # add process noise
        p_out += timestep * self.q

        self.sigmas = sigmas_out
        self.x = x_out
        self.p = p_out
        # print("predict end")

        self.lock.release()


    def get_state(self, index=-1):
        """
        returns the current state (n_dim x 1), or a particular state variable (float)
        :param index: optional, if provided, the index of the returned variable
        :return:
        """
        if index >= 0:
            return self.x[index]
        else:
            return self.x

    def get_covar(self):
        """
        :return: current state covariance (n_dim x n_dim)
        """
        return self.p
    
    def set_state(self, value, index=-1):
        """
        Overrides the filter by setting one variable of the state or the whole state
        :param value: the value to put into the state (1 x 1 or n_dim x 1)
        :param index: the index at which to override the state (-1 for whole state)
        """
        with self.lock:
            if index != -1:
                self.x[index] = value
            else:
                self.x = value

    def reset(self, state, covar):
        """
        Restarts the UKF at the given state and covariance
        :param state: n_dim x 1
        :param covar: n_dim x n_dim
        """

        with self.lock:
            self.x = state
            self.p = covar

        """
        x_in[0]為DR預測X_Position
        x_in[1]為DR預測Y_Position
        x_in[2]為DR預測方向角heading
        x_in[3]為DR預測速度velocity
        """

def iterate_x(x_in, timestep, inputs):
    '''this function is based on the x_dot and can be nonlinear as needed'''
    ret = np.zeros(len(x_in))
    ret[0] = x_in[0] + timestep * x_in[3] * math.cos(x_in[2])
    ret[1] = x_in[1] + timestep * x_in[3] * math.sin(x_in[2])
    ret[2] = x_in[2] 
    ret[3] = x_in[3] 
    return ret

def Measure_fusion(AX, A_std, BX, B_std):
    A_weight = B_std/(A_std+B_std)
    B_weight = A_std/(A_std+B_std)
    return AX*A_weight+BX*B_weight
###卡爾曼濾波

###RFID定位函數
def string_to_json(s):
    s = s.replace("'", '"').replace('u"', '"')
    return json.loads(s)

class Point:
    x: float
    y: float

    def __init__(self, x_init: float, y_init: float):
        self.x = x_init
        self.y = y_init

    def __repr__(self):
        return "".join(["Point(", str(self.x), ",", str(self.y), ")"])

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Point):
            return (self.x == other.x) & (self.y == other.y)
        return False

    def __hash__(self):
        return hash(str(self))
    
class Circle:
    center: Point
    radius: float

    def __init__(self, x: float, y: float, r: float):
        self.center = Point(x, y)
        self.radius = r

    def __repr__(self):
        return "".join(["Circle(", str(self.center.x), ", ", str(self.center.y), ", ", str(self.radius), ")"])

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Circle):
            return (self.center.x == other.center.x) & (self.center.y == other.center.y) & (self.radius == other.radius)
        return False

def rssi_to_distance(rssi, C=35.5510920, N=29.0735592, B=11.8099735):
    return B ** (-1*(rssi + C) / N)

def trilateration(crls: [Circle]):
    x = Symbol('x')
    y = Symbol('y')
    a = Symbol('a')
    
    # 2 point
    if len(crls) == 2:
        arr = []
        for crl in crls:
            arr.append((x-crl.center.x)**2+(y-crl.center.y)**2-(crl.radius)**2)
           
        
        return solve(
            arr,
            [x, y]
        )
    
    # n point
    else:
        arr = []
        for crl in crls:
            arr.append((x-crl.center.x)**2+(y-crl.center.y)**2-(crl.radius*a)**2)
            
        
        return solve(
            arr,
            [x, y, a]
        )

def find_xy_by_rfid_tag(rfid_tag_df, rfid_tag_dict):
    rfid_list = list(rfid_tag_dict.keys())
    return rfid_tag_df[rfid_tag_df['rfid_id'].isin(rfid_list)][['axis_x', 'axis_y']]

def rfid_tag_processing(left_rfid_dict,right_rfid_dict):
    left_rfid_dict = {key: val for key, val in left_rfid_dict.items() if val > -76 }
    right_rfid_dict = {key: val for key, val in right_rfid_dict.items() if val > -76}
    
    # print("type_rfid_list",type(rfid_list))
    left_rfid_dict = {key: val for key, val in left_rfid_dict.items() if key in rfid_list}
    right_rfid_dict = {key: val for key, val in right_rfid_dict.items() if key in rfid_list}
    
    left_rfid_list = list(left_rfid_dict.keys())
    right_rfid_list = list(right_rfid_dict.keys())
    # print("left_rfid_list",left_rfid_list)
    # print("right_rfid_list",right_rfid_list)
    
    left_xy_df = find_xy_by_rfid_tag(rfid_tag_df, left_rfid_dict)
    right_xy_df = find_xy_by_rfid_tag(rfid_tag_df, right_rfid_dict)
    
    # print("left_xy_df",left_xy_df)
    # print("right_xy_df",right_xy_df)
    
    left_xy_df['dBm'] = list(left_rfid_dict.values())
    right_xy_df['dBm'] = list(right_rfid_dict.values())
    # print("left_xy_df['dBm']",left_xy_df['dBm'])
    return  left_xy_df,right_xy_df,left_rfid_list,right_rfid_list

def rfid_positioning(left_xy_df,right_xy_df,left_rfid_list,right_rfid_list):

    # left_rfid_dict = {key: val for key, val in left_rfid_dict.items() if val > -76}
    # right_rfid_dict = {key: val for key, val in right_rfid_dict.items() if val > -76}
    
    # left_rfid_list = list(left_rfid_dict.keys())
    # right_rfid_list = list(right_rfid_dict.keys())
    # print("left_rfid_list",left_rfid_list)
    # print("right_rfid_list",right_rfid_list)
    
    # left_xy_df = find_xy_by_rfid_tag(rfid_tag_df, left_rfid_dict)
    # right_xy_df = find_xy_by_rfid_tag(rfid_tag_df, right_rfid_dict)
    
    # print("left_xy_df",left_xy_df)
    # print("right_xy_df",right_xy_df)
    
    # left_xy_df['dBm'] = list(left_rfid_dict.values())
    # right_xy_df['dBm'] = list(right_rfid_dict.values())
    # print("left_xy_df['dBm']",left_xy_df['dBm'])
    
    left_crls = []
    right_crls = []
    
    for index, row in left_xy_df.iterrows():
        redius = rssi_to_distance(row['dBm'], C=60, N=29.0735592, B=11.8099735)
        left_crls.append(Circle(row['axis_x'], row['axis_y'], redius))
        
    for index, row in right_xy_df.iterrows():
        redius = rssi_to_distance(row['dBm'], C=60, N=29.0735592, B=11.8099735)
        right_crls.append(Circle(row['axis_x'], row['axis_y'], redius))
        
    left_xy_df = left_xy_df[['axis_x', 'axis_y']]
    right_xy_df = right_xy_df[['axis_x', 'axis_y']]
    
    
    x = None
    y = None
    
    try:
        # 1-1
        if (len(left_rfid_list)==1 and len(right_rfid_list)==1):
            # calculate the center of the two rfid
            left_rfid_center_position = left_xy_df.mean(axis=0)
            right_rfid_center_position = right_xy_df.mean(axis=0)

            # calculate the distance between the two rfid centers
            x = (left_rfid_center_position['axis_x'] + right_rfid_center_position['axis_x']) / 2
            y = (left_rfid_center_position['axis_y'] + right_rfid_center_position['axis_y']) / 2
            return x, y

        # 2-1, 3-1
        elif (len(left_rfid_list)==2 and len(right_rfid_list)==1) or (len(left_rfid_list)>=3 and len(right_rfid_list)==1):
            left_positions = trilateration(left_crls)

            if len(left_rfid_list)>=3:
                min_distance = float('inf')
                result_left_position = None
                for left_position in left_positions:
                    # print("left_position:", list(left_position)[-1])
                    distance = math.dist([1], [list(left_position)[-1]])
                    if min_distance>distance:
                        result_left_position = list(left_position)
                        min_distance = distance

                left_positions = [result_left_position]

            min_distance = float('inf')

            for left_position in left_positions:
                distance = math.dist(right_xy_df.mean(axis=0).values, list(left_position)[:2])
                if min_distance>distance:
                    # print(left_position)
                    x = left_position[0]
                    y = left_position[1]
                    min_distance = distance
                    
            right_rfid_center_position = right_xy_df.mean(axis=0)
            
            x = (x + right_rfid_center_position['axis_x']) / 2
            y = (y + right_rfid_center_position['axis_y']) / 2
            return x, y

        # 1-2, 1-3 
        elif (len(left_rfid_list)==1 and len(right_rfid_list)==2) or (len(left_rfid_list)==1 and len(right_rfid_list)>=3):
            right_positions = trilateration(right_crls)

            if len(right_rfid_list)>=3:
                min_distance = float('inf')
                result_right_position = None
                for right_position in right_positions:
                    distance = math.dist([1], [list(right_position)[-1]])
                    if min_distance>distance:
                        result_right_position = list(right_position)
                        min_distance = distance

                right_positions = [result_right_position]

            min_distance = float('inf')

            for right_position in right_positions:
                distance = math.dist(left_xy_df.mean(axis=0).values, list(right_position[:2]))
                if min_distance>distance:
                    x = right_position[0]
                    y = right_position[1]
                    min_distance = distance
                    
            left_rfid_center_position = left_xy_df.mean(axis=0)
            
            x = (x + left_rfid_center_position['axis_x']) / 2
            y = (y + left_rfid_center_position['axis_y']) / 2
            return x, y

        # 2-2, 3-2, 2-3, 3-3
        else:
            left_positions = trilateration(left_crls)
            right_positions = trilateration(right_crls)
            
            # print("3-3 left_positions:", left_positions)
            # print("3-3 right_positions:", right_positions)

            if len(left_rfid_list)>=3:
                min_distance = float('inf')
                result_left_position = None
                for left_position in left_positions:
                    distance = math.dist([1], [list(left_position)[-1]])
                    if min_distance>distance:
                        result_left_position = left_position
                        min_distance = distance

                left_positions = [result_left_position]
                        
            if len(right_rfid_list)>=3:
                min_distance = float('inf')
                result_right_position = None
                for right_position in right_positions:
                    distance = math.dist([1], [list(right_position)[-1]])
                    if min_distance>distance:
                        result_right_position = right_position
                        min_distance = distance

                right_positions = [result_right_position]
            
            min_distance = float('inf')

            for left_position in left_positions:
                for right_position in right_positions:

                    distance = math.dist(list(left_position[:2]), list(right_position[:2]))
                    if min_distance>distance:
                        x = (left_position[0]+right_position[0])/2
                        y = (left_position[1]+right_position[1])/2
                        min_distance = distance
            return x, y
    except Exception as e:
        print("Error:", e)
        return x, y





if __name__ == "__main__":
    redis_truncate(READER_ANTENNA_1)
    redis_truncate(READER_ANTENNA_2)
    main()

