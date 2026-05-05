from sympy import Symbol, solve
import json
import math
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

def rfid_positioning(rfid_tag_df, right_rfid_dict, left_rfid_dict):

    left_rfid_dict = {key: val for key, val in left_rfid_dict.items() if val > -76}
    right_rfid_dict = {key: val for key, val in right_rfid_dict.items() if val > -76}
    
    left_rfid_list = list(left_rfid_dict.keys())
    right_rfid_list = list(right_rfid_dict.keys())
    
    left_xy_df = find_xy_by_rfid_tag(rfid_tag_df, left_rfid_dict)
    right_xy_df = find_xy_by_rfid_tag(rfid_tag_df, right_rfid_dict)
    
    left_xy_df['dBm'] = list(left_rfid_dict.values())
    right_xy_df['dBm'] = list(right_rfid_dict.values())
    
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
                    print("left_position:", list(left_position)[-1])
                    distance = math.dist([1], [list(left_position)[-1]])
                    if min_distance>distance:
                        result_left_position = list(left_position)
                        min_distance = distance

                left_positions = [result_left_position]

            min_distance = float('inf')

            for left_position in left_positions:
                distance = math.dist(right_xy_df.mean(axis=0).values, list(left_position)[:2])
                if min_distance>distance:
                    print(left_position)
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
            
            print("3-3 left_positions:", left_positions)
            print("3-3 right_positions:", right_positions)

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

    rfid_train_df = pd.read_csv(RFID_TRAIN_FILE_PATH)
    rfid_test_df = pd.read_csv(RFID_TEST_FILE_PATH, index_col='sn')
    rfid_test_df
    imu_df.iloc[0]['datetime']

# RFID preprocessing
rfid_test_df['right_rfid'] = rfid_test_df['right_rfid'].apply(string_to_json)
rfid_test_df['left_rfid'] = rfid_test_df['left_rfid'].apply(string_to_json)
rfid_test_df['datetime']= pd.to_datetime(rfid_test_df['datetime'])
rfid_test_df = rfid_test_df.sort_values("datetime")

rfid_test_df = rfid_test_df[(rfid_test_df['datetime'] > imu_df.iloc[0]['datetime']) & (rfid_test_df['datetime'] < imu_df.iloc[-1]['datetime'])]
rfid_test_df

for index, row in rfid_test_df.iterrows():
    if len(row['left_rfid']) == 0 or len(row['right_rfid']) == 0:
        continue

    x, y = rfid_positioning(rfid_train_df, row['left_rfid'], row['right_rfid'])
    
    rfid_test_df.at[index, 'rfid_loc_x'] = x
    rfid_test_df.at[index, 'rfid_loc_y'] = y
    
rfid_test_df = rfid_test_df.dropna()
rfid_test_df

result_df = pd.merge(result_df, rfid_test_df, how='outer', on='datetime')
result_df = result_df.sort_values("datetime")
result_df

rfid_test_df.to_csv('../rfid_data.csv')

rfid_test_df = pd.read_csv('../rfid_data.csv')

rfid_df = rfid_test_df.copy()

rfid_df['rfid_loc_x'] = rfid_df['rfid_loc_x'].astype(float)
rfid_df['rfid_loc_y'] = rfid_df['rfid_loc_y'].astype(float)

ax = rfid_df.plot(x='rfid_loc_x', y='rfid_loc_y', legend=False, figsize = (10, 10))
plt.plot(rfid_df.iat[0,3],rfid_df.iat[0,4], marker= '^', color = 'green') #start mark
plt.plot(rfid_df.iat[-1,3],rfid_df.iat[-1,4], marker = 'x', color = 'red') #end mark

ax.set_xlim(0, 26)
ax.set_ylim(0, 23)

plt.show() 