from utils import Geo
import pandas as pd
import numpy as np
import scipy.stats as stats
import glob
import datetime as dt
import os
import statsmodels.api as sm
# utils.py from this repo
from utils import parse_cl_args, parse_config_file, Geo

def get_summary_stats(county_df):
    no_accounts = len(county_df)
    no_tweets = sum(county_df.no_tweets)
    mean_misinfo = np.mean(county_df.fraction_misinfo)
    sem_misinfo = stats.sem(county_df.fraction_misinfo)
    min_misinfo = min(county_df.fraction_misinfo)
    max_misinfo = max(county_df.fraction_misinfo)
    return pd.Series (
        [
            no_accounts,
            no_tweets,
            mean_misinfo,
            sem_misinfo,
        ],
        [
            'No. accounts',
            'No. tweets',
            'Frac low-credibility',
            'Stderr low-credibility',
        ]
    )

def threshold_accounts(df, accounts_per_county, tweets_per_account):
    filtered_accounts = df[df["no_tweets"]>=tweets_per_account].groupby(["state","county"]).filter(lambda x : x.__len__()>=accounts_per_county).copy()
    results = filtered_accounts.groupby(["state","county"]).apply(lambda x: get_summary_stats(x))
    results = results.reset_index()
    return (results)
    
def clean_Twitter_csv(data_path, t_val):

    twitter_data = pd.read_csv(data_path)

    twitter_data = twitter_data.replace('St. Tammany Parish','St Tammany Parish')
    twitter_data = twitter_data.replace('St. Joseph County','St Joseph County')
    
    results_data_list = []
    thresholded_accounts = threshold_accounts(twitter_data,1,1)
    thresholded_accounts = thresholded_accounts.rename(columns={'county':'County','state':'State'})

    fips_map = Geo().get_county_state_to_fips_map(unique_fips=False)
    twitter_data_with_fips = pd.merge(thresholded_accounts,fips_map,on=['County','State'],how='left')
    data = twitter_data_with_fips[twitter_data_with_fips.fips_code.notna()].copy()
    data['t_val'] = t_val
    data = data.rename(columns={'fips_code':'FIPS'})
    dates = os.path.basename(data_path).split('_')
    data['start_day'] = dates[0]
    data['end_day'] = dates[1]
    return data


def clean_Twitter_csv(data_path, t_val):

    twitter_data = pd.read_csv(data_path)

    twitter_data = twitter_data.replace('St. Tammany Parish','St Tammany Parish')
    twitter_data = twitter_data.replace('St. Joseph County','St Joseph County')
    
    results_data_list = []
    thresholded_accounts = threshold_accounts(twitter_data,1,1)
    thresholded_accounts = thresholded_accounts.rename(columns={'county':'County','state':'State'})

    fips_map = Geo().get_county_state_to_fips_map(unique_fips=False)
    twitter_data_with_fips = pd.merge(thresholded_accounts,fips_map,on=['County','State'],how='left')
    data = twitter_data_with_fips[twitter_data_with_fips.fips_code.notna()].copy()
    data['t_val'] = t_val
    data = data.rename(columns={'fips_code':'FIPS'})
    dates = os.path.basename(data_path).split('_')
    data['start_day'] = dates[0]
    data['end_day'] = dates[1]
    return data


def clean_Twitter_csv_state(data_path, t_val):

    twitter_data = pd.read_csv(data_path)
    
    state_data = twitter_data.groupby('state').apply(lambda x: get_summary_stats(x))

    state_data = state_data.reset_index()
    state_data = state_data.rename(columns={'county':'County','state':'State'})
    
    fips_map = Geo().get_state_to_fips_map()
    data = pd.merge(state_data,fips_map,on='State')
    data['County'] = ''

    data['t_val'] = t_val
    dates = os.path.basename(data_path).split('_')
    data['start_day'] = dates[0]
    data['end_day'] = dates[1]
    return data


def generate_aggregate_misinformation (data_path, state_level):

    files = sorted(glob.glob(os.path.join(data_path,'*aggregated_table.csv')))

    data = None

    t_val = 0
    
    for fname in files:
        # ignore the last file
        if fname.find('2021-03-25_US_accounts_aggregated_table.csv') == -1:
            if state_level:
                df = clean_Twitter_csv_state(fname,t_val)
            else:
                df = clean_Twitter_csv(fname,t_val)
            t_val += 1
            if data is None:
                data = df
            else:
                data = pd.concat([data,df])
    return data

def get_stderr(num_accept,sample_size):
    return stats.sem(np.concatenate( [
        np.ones(int(num_accept)),
        np.zeros(int(sample_size-num_accept))
    ]))

def get_summary_stats_FB_survey (geo_loc_df):
    sum_accept = sum (geo_loc_df.num_accept)
    sum_sample_size = sum (geo_loc_df.sample_size)
    stderr = get_stderr(sum_accept,sum_sample_size)
    start_day = min(geo_loc_df.DateTime)
    end_day = max(geo_loc_df.DateTime)
    return pd.Series (
        [
            sum_accept,
            sum_sample_size,
            sum_accept/sum_sample_size,
            stderr,
            start_day,
            end_day
        ],
        [
            'num_smoothed_covid_vaccinated_or_accept',
            'sample_size_for_covid_vaccinated_or_accept_question',
            'mean_smoothed_covid_vaccinated_or_accept',
            'stderr_smoothed_covid_vaccinated_or_accept',
            'start_day',
            'end_day'
        ]
    )

def process_survey_data (data_path,config = None, time_window = 7,state_level=False):

    data = pd.read_csv(
        data_path,
        usecols= ["geo_value","time_value","value","stderr","sample_size"],
        dtype={
            "geo_value":str,
            "time_value":str,
            "value":float,
            "stderr":float,
            "sample_size":float # This needs to be set as a float or the data doesn't load
        }
    )
    data['DateTime'] = pd.to_datetime(data['time_value'])

    if config:
        t_val_start = pd.to_datetime(config["DATES"]["t_val_start"])
        num_t_vals = config["DATES"]["num_t_vals"]
    else:
        t_val_start = dt.datetime(2021,1,4)
        t_val_end = dt.datetime(2021,3,25)
        num_t_vals = (t_val_end-t_val_start).days/time_window

    data['t_val'] = data.DateTime.apply(lambda x: int((x-t_val_start).days/time_window))
    data['num_accept'] = data.sample_size*(data.value/100.0)

    aggregate = data.groupby(['geo_value','t_val']).apply(lambda x: get_summary_stats_FB_survey(x))
    aggregate = aggregate.reset_index()

    if state_level:
        state_abbr = Geo().get_state_to_fips_map()
        data = pd.merge(aggregate,state_abbr,left_on='geo_value',right_on='abbr_lower')
    else:
        data = aggregate.rename(columns={'geo_value':'FIPS'})
    
    return data

def get_t_val_string(t_val):
    if t_val < 0:
        return 'm'+str(abs(t_val))
    else:
        return str(abs(t_val))

if __name__ == '__main__':

    time_window = 1

    # Load config_file_path from commandline input
    args = parse_cl_args()
    config_file_path = args.config_file
    state_level = args.state_level

    # Get config file object
    config = parse_config_file(config_file_path)

    misinfo_path = os.path.join(config["PATHS"]["TABLES_TEMPORAL_FOLDER"],str(time_window)+'day')
    aggregate_misinfo_name = 'aggregate_misinfo_'+str(time_window)+'.csv'
    if state_level:
        aggregate_misinfo_name = 'state_level_'+aggregate_misinfo_name

    if not os.path.exists(os.path.join(misinfo_path,aggregate_misinfo_name)):
        df_misinfo = generate_aggregate_misinformation (misinfo_path, state_level)
        df_misinfo.to_csv(os.path.join(misinfo_path,aggregate_misinfo_name))

    county_path = config["PATHS"]["COUNTY_DATA_DIR"]
    state_path = config["PATHS"]["STATE_DATA_DIR"]
    aggregate_survey_name = 'aggregate_survey_data_days_'+str(time_window)+'.csv'
    

    if state_level:
        if not os.path.exists(os.path.join(state_path,aggregate_survey_name)):
            df_hesitancy = process_survey_data(os.path.join(state_path,'state_level_covidcast-fb-survey-smoothed_wcovid_vaccinated_or_accept-2020-12-20-to-2021-05-10.csv'), time_window = time_window, state_level = state_level)
            df_hesitancy.to_csv(os.path.join(state_path,aggregate_survey_name))
    else:
        if not os.path.exists(os.path.join(county_path,aggregate_survey_name)):
            df_hesitancy = process_survey_data(os.path.join(county_path,'county_level_covidcast-fb-survey-smoothed_wcovid_vaccinated_or_accept-2020-12-20-to-2021-05-10.csv'), time_window = time_window, state_level = state_level)
            df_hesitancy.to_csv(os.path.join(county_path,aggregate_survey_name))

