''' 
    Anomoly Algorithm for Environment Sensors
Algorithm that takes in the user's api key and device id, 
and finds anomolies for Temperature and Humidity within the past 30 day.
Parameters: required -a API_KEY 
            required -d DEVICE_ID
            optional -c converts to CELCIUS (default F)
            optional -p percent of anomalies wanted (default 5 percent)
Downloads .docx report file, anomaly footage, and csv of 30 days to current directory. 
Command Line Input: 
    basic case: python3 environment_anomaly.py -a {API_KEY} -d {DEVICE_ID} 
    celcius case: python3 environment_anomaly.py -a {API_KEY} -d {DEVICE_ID} -c 
    percent_anomaly case: python3 environment_anomaly.py -a {API_KEY} -d {DEVICE_ID} -p {% number of anomalies}
'''

from anomaly_helpers import *
import pandas as pd
import datetime
import argparse

data_type = 'Environment' 

def C_to_F(temp):
    '''
    Converts C -> F.
    Returns C temperature.
    '''
    return (temp*9/5)+32

def clean_data(df,convert):
    '''
    Cleans Data for proper dataframe. Drops Tampered column and duplicates. Reformats Date.
    Returns updated DataFrame, Reformated Dates and data used for outlier test.
    '''
    # Changes data from C->F
    if convert:
        changed_temp = []
        for temp in df["Temperature"]:
            changed_temp.append(C_to_F(temp))
        df["Temperature"] = changed_temp
    
    # Deletes Tampered column
    del df["Tampered"]
    # Drops duplicate rows
    df = df.drop_duplicates()
    # Reformats date
    clean_dates = [datetime.datetime.strptime(elem, '%Y-%m-%dT%H:%M:%S') for elem in get_datetime(df)]
    return df, clean_dates, df[['Temperature','Humidity']]


def EV_grab(api_key,device_id):
    '''
    Grabs data from given parameters via API and writes to CSV file.
    Returns filename.
    '''
    
    current_milli, thirty_days_ago, current_milli_date, thirty_days_ago_date = get_time()

    url = "https://api2.rhombussystems.com/api/export/climateEvents"

    payload = {
        "createdBeforeMs": current_milli,
        "createdAfterMs": thirty_days_ago,
        "sensorUuid": device_id
    }  
    headers = {
        "Accept": "application/json",
        "x-auth-scheme": "api-token",
        "Content-Type": "application/json",
        "x-auth-apikey": api_key
    }

    return get_data(url,payload, headers,data_type)



def main():
    # Defaults to F
    convert = True
    url = "https://api2.rhombussystems.com/api/climate/getMinimalClimateStateList"

    # Parser. Gets arguements for test.
    parser = argparse.ArgumentParser(
        description='Creates a report and downloads footage of anomalies found in Environmental data for the past 30 days.')
    
    parser.add_argument('--api_key', '-a', type=str, required=True,
    help='Rhombus API key')
    
    parser.add_argument('--device_id', '-d', type=str, required=True,
    help='Device Id to pull frame from')
    
    parser.add_argument("--celcius", '-c', help="convert to C; default F",
                    action="store_true")
    
    parser.add_argument('--perc_anomalies', '-p', type=int, required=False,
    help='Perecent of anomalies you would like downloaded footage of; 1-100; default=5',
    default=5)
    
    parser.add_argument('--duration', '-dur', type=int, required=False,
    help='Duration of clip in seconds; default=60',
    default=60)

    args = parser.parse_args()
    
    # Checks for Celcius flag
    if args.celcius: 
        convert = False 

    # Grabs data and assigns filename
    file_name,new_dir_path = EV_grab(args.api_key,args.device_id)

    # DataFrame used for outlier test
    df = pd.read_csv(new_dir_path + '/' + file_name)

    # Clean Data 
    df, clean_dates, data = clean_data(df, convert)
    
    # Outlier Test
    temp_a, temp_date_a, temp_graph, hum_a, hum_date_a, hum_graph = isolation_forest_test(df, data, clean_dates,"Temperature","Humidity",new_dir_path)
   
    # Get amount of anomalies for video footage via percent of anomalies user wants
    temp_footage_anomalies, temp_footage_dates, hum_footage_anomalies, hum_footage_dates = wanted_anomaly_footage(args.perc_anomalies,temp_a,hum_a,"Temperature","Humidity")
    associated_cameras = find_associated_camera(args.api_key, url,"climateStates")

    # Grab footage from wanted % of anomalies and creates seek points
    for camera_id in associated_cameras:
        temp_start = footage_call(temp_footage_dates, args.api_key, camera_id, args.duration,"Temperature",new_dir_path)
        hum_start = footage_call(hum_footage_dates, args.api_key, camera_id, args.duration,"Humidity",new_dir_path)
        
        # Add Seek Points
        for sec_time in temp_start:
            start_time = sec_time * 1000
            seek_points(start_time, camera_id, args.api_key)
        for sec_time in hum_start:
            start_time = sec_time * 1000 
            seek_points(start_time, camera_id, args.api_key)

    # Create Report
    create_report_2var(temp_graph,hum_graph,data_type,temp_footage_anomalies,hum_footage_anomalies,new_dir_path)

if __name__ == "__main__":
    main()