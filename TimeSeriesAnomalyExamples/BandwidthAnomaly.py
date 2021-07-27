'''
    Anomoly Algorithm for Bandwidth

Algorithm that takes in the user's api key and device id, 
and finds anomolies for Uploads and Download Bandwidth within the past 30 day.

Parameters: required -a API_KEY 
            required -d DEVICE_ID

Downloads .docx report file, anomaly footage, and csv of 30 days to current directory. 
 
'''
from Anomaly import *
import pandas as pd
import datetime
import argparse

data_type = "Bandwidth"

def clean_data_2(df):
    '''
    Cleans Data; Converts B->MB; Drops duplicates; 
    Returns updated DataFrame, Reformated Dates, data used for outlier test
    '''
    df["Upload (BYTES)"] = df["Upload (BYTES)"]/1000000 # change from bytes to MB
    df["Download (BYTES)"] = df["Download (BYTES)"]/1000000 # change from bytes to MB
    df = df.rename(columns={"Upload (BYTES)": "Upload (MB)","Download (BYTES)": "Download (MB)"})

    df = df.drop_duplicates()
    df['Upload (MB)'].fillna((df['Upload (MB)'].mean()), inplace=True)
    df['Download (MB)'].fillna((df['Download (MB)'].mean()), inplace=True)

    clean_dates = [datetime.datetime.strptime(elem, '%Y-%m-%dT%H:%M:%S %Z') for elem in df["Date"]]
    return df, clean_dates, df[['Upload (MB)','Download (MB)']]

def band_grab(api_key,device_id,):
    '''
    Grabs data from given parameters via API and writes to a CSV file
    Returns filename.
    '''
    
    current_milli, thirty_days_ago, current_milli_date, thirty_days_ago_date = get_time()

    url = "https://api2.rhombussystems.com/api/export/countReports"

    payload = {
        "uuidList": [device_id],
        "type": "BANDWIDTH",
        "scope": "DEVICE",
        "interval": "QUARTERHOURLY",
        "endDate": current_milli_date,
        "startDate": thirty_days_ago_date
    }
    
    headers = {
        "Accept": "text/csv; charset=UTF-8",
        "x-auth-scheme": "api-token",
        "Content-Type": "application/json",
        "x-auth-apikey": api_key
    }

    return get_data(url,payload, headers,data_type)


def main():

    # Parser. Gets arguements for test.
    parser = argparse.ArgumentParser(
        description='Creates a report and downloads footage of anomalies found in Environmental data for the past 30 days.')
    
    parser.add_argument('--api_key', '-a', type=str, required=True,
    help='Rhombus API key')
    
    parser.add_argument('--device_id', '-d', type=str, required=True,
    help='Device Id to pull frame from')

    parser.add_argument('--perc_anomalies', '-p', type=int, required=False,
    help='Perecent of anomalies you would like downloaded footage of; 1-100; default = 5')
    
    
    args = parser.parse_args()

    if args.perc_anomalies:
        perc_anomalies = args.perc_anomalies
    else:
        perc_anomalies = 5

    args.duration = 30
    
    # Grabs Data and assigns filename
    file_name = band_grab(args.api_key,args.device_id)
    
    # DataFrame use for outlier test
    df = pd.read_csv(file_name)
    
    # Cleans Data 
    df, clean_dates, data = clean_data_2(df)

    # Outlier Test
    upload_a, upload_date_a, up_graph, download_a, download_date_a,down_graph = isolation_forest_test(df, data, clean_dates,"Upload (MB)",'Download (MB)')

    # Get amount of anomalies for video footage via percent of anomalies user wants
    upload_footage_anomalies,upload_footage_dates, download_footage_anomalies, download_footage_dates = wanted_anomaly_footage(perc_anomalies,upload_a,download_a, "Upload (MB)",'Download (MB)')
    
    # Grab footage from wanted % of anomalies
    up_start = footage_call(upload_footage_dates, args.api_key, args.device_id, args.duration,"Upload")
    down_start = footage_call(download_footage_dates, args.api_key, args.device_id, args.duration,"Download")
    
    # Create Report
    create_report_2var(up_graph,down_graph,data_type,upload_footage_anomalies,download_footage_anomalies)


if __name__ == "__main__":
    main()
