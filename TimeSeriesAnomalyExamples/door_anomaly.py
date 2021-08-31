'''
    Anomaly Algorithm for Door
Algorithm that takes in the user's api key and device id, 
and finds anomolies for door activities within the past 30 day.
Parameters: required -a API_KEY 
            required -d DEVICE_ID
            optional -p percent of anomalies wanted (default 5 percent)
Downloads .docx report file, anomaly footage, and csv of 30 days to current directory. 
 
Command Line Input: 
    basic case: python3 door_anomaly.py -a {API_KEY} -d {DEVICE_ID} 
    percent_anomaly case: python3 door_anomaly.py -a {API_KEY} -d {DEVICE_ID} -p {% number of anomalies}
'''
import warnings 
warnings.filterwarnings("ignore")
from anomaly_helpers import *
import pandas as pd
import datetime
import argparse

data_type = "Door"

def door_grab(api_key,device_id):
    '''
    Grabs data from given parameters via API and writes to a CSV file
    Returns filename.
    ''' 
    current_milli, thirty_days_ago, current_milli_date, thirty_days_ago_date = get_time()

    url = "https://api2.rhombussystems.com/api/export/doorEvents"

    payload = {
        "createdAfterMs": thirty_days_ago,
        "createdBeforeMs": current_milli,
        "sensorUuid": device_id
    }

    headers = {
        "Accept": "application/json",
        "x-auth-scheme": "api-token",
        "Content-Type": "application/json",
        "x-auth-apikey": api_key
    }

    return get_data(url,payload, headers,data_type)

def wanted_door_footage(perc_anomaly, outliers,df):
    '''
    Finds amout of outliers to be downloaded based on percent of anomaly specified by user.
    Returns dataframe of outliers and outliers to download.
    '''
    
    num_outliers_wanted = round((perc_anomaly/100)*len(outliers))
    outliers.sort()
    wanted = outliers[-num_outliers_wanted:]
    outlier_df = df.loc[df["Door opened (sec)"].isin(outliers)]
    
    count = 0
    open_index = []
    for i in df["Door opened (sec)"]:
        if i in wanted:
            open_index.append(count-1)
        count+=1
 
    df_open = df.iloc[open_index]

    return df_open, outlier_df 

def clean_date_door(df):
    '''
    Cleans data and adds column: Door opened (sec)- how long the door was open for.
    Returns clean dataframe with added column.
    '''
    df = df.drop_duplicates()
    date = df["Date"]
    time = df["Time"]

    time = time.str.split('-').str[0]
    df["Date"]= date+"T"+time
    del df["Time"]
    df = df.sort_values(by=['Date'],ascending=True)

    count = 0
    previous = 'CLOSED'
    index = []
    indexNames = df[ df['State'] == "AJAR" ].index
    df.drop(indexNames , inplace=True)
    for state in df['State']:
        if state != previous:
            index.append(count)
        previous = state
        count += 1

    df_clean = df.iloc[index]

    pandas_dates = [datetime.datetime.strptime(elem, '%Y-%m-%dT%H:%M:%S') for elem in df_clean["Date"]]
    clean_dates = []

    for dates in pandas_dates:
        clean = int(dates.timestamp())
        clean_dates.append(clean)

    difference_in_time = []
    count = 0
    for state in df_clean['State']:
        current_time = clean_dates[count]
        if state == 'CLOSED':
            difference = current_time - previous_time
        else: 
            difference = 0
        difference_in_time.append(difference)
        previous_time = current_time
        count+=1
        
    df_clean["Door opened (sec)"] = difference_in_time

    return df_clean

def main():
    
    url = "https://api2.rhombussystems.com/api/door/getMinimalDoorStateList"
    # Parser. Gets arguements for test.
    parser = argparse.ArgumentParser(
        description='Creates a report and downloads footage of anomalies found in Environmental data for the past 30 days.')
    
    parser.add_argument('--api_key', '-a', type=str, required=True,
    help='Rhombus API key')
    
    parser.add_argument('--device_id', '-d', type=str, required=True,
    help='Device Id to pull frame from')
    
    parser.add_argument('--perc_anomalies', '-p', type=int, required=False,
    help='Perecent of anomalies you would like downloaded footage of; 1-100; default=5',
    default=5)

    parser.add_argument('--duration', '-dur', type=int, required=False,
    help='Duration of clip in seconds; default=60',
    default=60)

    args = parser.parse_args()

    # Grabs data and assigns filename
    file_name, new_dir_path = door_grab(args.api_key,args.device_id)

    # DataFrame used for outlier test
    df = pd.read_csv(new_dir_path + '/' + file_name)

    # Clean Data 
    df = clean_date_door(df)
    
    # Outlier Test
    outliers, outlier_dates, door_graph = iqr_test(df,df["Door opened (sec)"],"Door",new_dir_path)
    
    #Get amount of anomalies for video footage via percent of anomalies user wants
    footage_df, outlier_df = wanted_door_footage(args.perc_anomalies, outliers, df)
    anomaly_data = outlier_df.drop(columns=['State'])

    associated_cameras = find_associated_camera(args.api_key,url,"doorStates" )

    pandas_date_footage =  [datetime.datetime.strptime(elem, '%Y-%m-%dT%H:%M:%S') for elem in footage_df["Date"]]
    
    # Grab footage from wanted % of anomalies and creates seek points
    for camera_id in associated_cameras:
        door_start = footage_call(pandas_date_footage, args.api_key, camera_id, args.duration,"Door", new_dir_path)
        
        # Add Seek Points
        for sec_time in door_start:
            start_time = sec_time * 1000
            seek_points(start_time, camera_id, args.api_key)
   
    # Create Report
    create_report_1var(door_graph,data_type,anomaly_data,new_dir_path)
    
if __name__ == "__main__":
    main()