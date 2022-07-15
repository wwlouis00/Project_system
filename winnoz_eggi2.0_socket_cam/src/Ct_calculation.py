import pandas as pd
import os
from datetime import datetime, time
#import matplotlib.pyplot as plt

# global variable
raw_file_path = "./result/detection.csv"

default_threshold = 0.4584

colorTab_More4 = ['#e8a5eb', '#facc9e', '#e8e948', '#1bb763',
                       '#25f2f3', '#1db3ea', '#d1aef8', '#c8c92c',
                       '#f32020', '#fd9b09', '#406386', '#24a1a1',
                       '#1515f8', '#959697', '#744a20', '#7b45a5']

def get_accumulation_time():
    df_time = df_normalization['time']
    time_ori = datetime.strptime(df_time[0], "%H:%M:%S")
    time_delta = []
    for time in df_time:
        time_now = datetime.strptime(time, "%H:%M:%S")
        time_delta.append((time_now - time_ori).seconds/60)
    df_normalization.insert(1, column="accumulation", value=time_delta)

def get_StdDev_and_Avg(baseline_begin, baseline_end):
    StdDev = []
    Avg = []
    for i in range(0, 16):
        df_current_well = df_normalization[f'well{i+1}']
        StdDev.append(df_current_well[baseline_begin:baseline_end+2].std()) # the "+2" follow behind makes the array slice correct (1 unit is 0.5 min in raw data)
        Avg.append(df_current_well[baseline_begin:baseline_end+2].mean()) # the "+2" follow behind makes the array slice correct (1 unit is 0.5 min in raw data)
    return StdDev, Avg

def normalize(baseline_begin, baseline_end):
    for i in range(0, 16):
        df_current_well = df_raw[f'well{i+1}']
        baseline = df_current_well[baseline_begin:baseline_end+2].mean() # the "+2" follow behind makes the array slice correct (1 unit is 0.5 min in raw data)
        df_normalization[f'well{i+1}'] = (df_raw[f'well{i+1}']-baseline)/baseline # normalized = (IF(t)-IF(b))/IFc

def get_ct_threshold(baseline_begin, baseline_end):
    threshold_value = []
    StdDev, Avg = get_StdDev_and_Avg(baseline_begin, baseline_end)
    for i in range(0, 16):
        print(f"Well {i+1}: StdDev is {StdDev[i]}, Avg is {Avg[i]}")
        # Because stander deviation = 0 may cause some weird ct output,
        # so when stander deviation = 0, we'll assign them a default threhold value
        if StdDev[i] == 0:
            threshold_value.append(default_threshold)
            print(f"Use default threshold: {default_threshold}\n")
        else:
            threshold_value.append(10*StdDev[i] + Avg[i])
            print(f"Threshold_value: {threshold_value[i]}\n")
    return threshold_value

def get_ct_value(threshold_value, baseline_begin):
    Ct_value = []
    for i in range(0, 16):
        df_current_well = df_normalization[f'well{i+1}']
        df_accumulation = df_normalization['accumulation']
        # print("\n")
        # print(df_current_well)
        # print(f"Threshold value: {threshold_value[i]}")
        try:
            for j, row in enumerate(df_current_well):
                # The comparison only compare the data beyond baseline_begin
                if row >= threshold_value[i] and j > baseline_begin :
                    # print(f"row: {row}")
                    thres_lower = df_current_well[j-1]
                    thres_upper = df_current_well[j]
                    acc_time_lower = df_accumulation[j-1]
                    acc_time_upper = df_accumulation[j]

                    # linear regression
                    x2 = acc_time_upper
                    y2 = thres_upper
                    x1 = acc_time_lower
                    y1 = thres_lower
                    y = threshold_value[i]
                    x = (x2-x1)*(y-y1)/(y2-y1)+x1

                    Ct_value.append(round(x, 2))
                    print(f"Ct of well{i+1} is {round(x, 2)}")
                    break

                # if there is no Ct_value availible
                elif j == len(df_current_well)-1:
                    Ct_value.append(99.99)
                    print("Ct value is not available")

        # some unknow error occur, use default_threshold
        except:
            for j, row in enumerate(df_current_well):
                # The comparison only compare the data beyond baseline_begin
                if row >= default_threshold and j > baseline_begin :
                    # print(f"row: {row}")
                    thres_lower = df_current_well[j-1]
                    thres_upper = df_current_well[j]
                    acc_time_lower = df_accumulation[j-1]
                    acc_time_upper = df_accumulation[j]

                    # linear regression
                    x2 = acc_time_upper
                    y2 = thres_upper
                    x1 = acc_time_lower
                    y1 = thres_lower
                    y = threshold_value[i]
                    x = (x2-x1)*(y-y1)/(y2-y1)+x1

                    Ct_value.append(round(x, 2))
                    print(f"Ct of well{i+1} is {round(x, 2)}")
                    break

                # if there is no Ct_value availible
                elif j == len(df_current_well)-1:
                    Ct_value.append(99.99)
                    print("Ct value is not available")

    return Ct_value

def take_photo():
    '''
    This function do moving average on raw data.
    It can generate a smoother curve on show the chart in UI.
    '''
    all_well = []
    time_array = []

    for i in range(0,16):
        filling_value = df_normalization[f"well{i + 1}"][5]
        all_well.append(df_normalization[f"well{i + 1}"].rolling(window=5).mean().fillna(filling_value).round(2))
    temp_well = pd.DataFrame(all_well)
    Csv_well = temp_well.T

    for j in range(0, len(Csv_well.index), 1):
        time_array.append(j / 2)

    return Csv_well


def ct_calculation(baseline_begin, baseline_end):
    global df_raw, df_normalization, well_move_average, Csv_well
    well_move_average = []
    df_raw = pd.read_csv(raw_file_path)
    df_normalization = df_raw.copy()

    get_accumulation_time()
    normalize(baseline_begin, baseline_end)
    df_normalization.to_csv("./result/normalization.csv", index=False)
    threshold_value = get_ct_threshold(baseline_begin, baseline_end)
    Ct_value = get_ct_value(threshold_value, baseline_begin)
    try:
        if len(df_raw.index) < 7:
            raise
        print("Count of data is greater than 7")
        Csv_well = take_photo()
        save_excel = pd.DataFrame({"well_1":[Ct_value[0]],"well_2":[Ct_value[1]],"well_3":[Ct_value[2]],"well_4":[Ct_value[3]],
                                   "well_5":[Ct_value[4]],"well_6":[Ct_value[5]],"well_7":[Ct_value[6]],"well_8":[Ct_value[7]],
                                   "well_9":[Ct_value[8]],"well_10":[Ct_value[9]],"well_11":[Ct_value[10]],"well_4":[Ct_value[11]],
                                   "well_13":[Ct_value[12]],"well_14":[Ct_value[13]],"well_15":[Ct_value[14]],"well_16":[Ct_value[15]]}
        ,index=["CT_Value"])
        save_excel.to_csv("./result/CT.csv",encoding= "utf_8_sig")
        Csv_well.T.to_csv("./result/detection_T.csv",encoding= "utf_8_sig") # The data after doing moving average.
        return Ct_value
        
    except Exception as e:
        print(e)
        print("Count of data is less than 7")
        save_excel = pd.DataFrame({"well_1":[Ct_value[0]],"well_2":[Ct_value[1]],"well_3":[Ct_value[2]],"well_4":[Ct_value[3]],
                                   "well_5":[Ct_value[4]],"well_6":[Ct_value[5]],"well_7":[Ct_value[6]],"well_8":[Ct_value[7]],
                                   "well_9":[Ct_value[8]],"well_10":[Ct_value[9]],"well_11":[Ct_value[10]],"well_4":[Ct_value[11]],
                                   "well_13":[Ct_value[12]],"well_14":[Ct_value[13]],"well_15":[Ct_value[14]],"well_16":[Ct_value[15]]}
        ,index=["CT_Value"])
        save_excel.to_csv("./result/CT.csv",encoding= "utf_8_sig")
        df_normalization = df_normalization.drop(columns=['time','accumulation','shutter_speed','ISO']) #Drop 'time','accumulation','shutter_speed','ISO'
        df_normalization.T.to_csv("./result/detection_T.csv",encoding= "utf_8_sig")
        return Ct_value
