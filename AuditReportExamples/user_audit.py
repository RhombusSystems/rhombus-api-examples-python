'''
    Audit Report on Specific User

Program that takes in the user's api key and a specific user's email from org, 
and finds stats/basic information on specific user.

Parameters: required -a API_KEY 
            required -u Specific user email

Downloads .docx report file and csv of past 30 days to current directory. 

Reports user's locations, actions, and dataframe of all user data. 

Command Line Input: 
    basic case: python3 user_audit_report.py -a {API_KEY} -u {EMAIL}
'''

import argparse
from audit_helpers import *
import pandas as pd

def main():

    # Parser. Gets arguements for test.
    parser = argparse.ArgumentParser(
        description='Creates a report of a specific user\'s data for the past 30 days.')
    
    parser.add_argument('--api_key', '-a', type=str, required=True,
    help='Rhombus API key')

    parser.add_argument('--user', '-u', type=str, required=True,
    help='User\'s email you would like to audit')
    
    args = parser.parse_args()
    
    # Grabs Data and assigns filename
    file_name, new_dir_path = audit_grab(args.api_key)
    
    # DataFrame use for outlier test
    df = pd.read_csv(new_dir_path + '/' + file_name)

    # Clean audit DataFrame
    clean_df = clean_data_audit(df)

    # Get User Dataframe
    user_df = user_action(clean_df,args.user)
    if (len(user_df) == 0):
        return 

    # User Locations
    user_loc = find_unique_values(user_df,"Location")

    # User Actions
    user_actions = user_action_count(df,args.user)

    # User activity plot
    plot_fname = user_activity_plot(user_df,args.user)

    # User Report
    user_report(user_df, user_actions, user_loc, args.user, plot_fname)

if __name__ == "__main__":
    main()
