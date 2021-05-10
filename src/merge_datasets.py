"""
PURPOSE:
    - This script takes in and cleans all of the data for this project
        and merges into one long/tidy format file with the format
        detailed below. 
    - This script also prints out a brief summary of the file that
        was created to hopefully raise any glaring red flags if the
        data looks strange. For example, if we see there are 300
        states, we know something bad is happening.

INPUT:
    - People.csv
    - Income.csv
    - Gini.csv
    - county_2020_elections.csv
    - 2021-01-04_2021-03-25_US_accounts_aggregated_table.csv
    - state_level_covidcast-fb-survey-smoothed_wcovid_vaccinated_or_accept-2021-01-04-to-2021-03-25.csv
    - county_level_covidcast-fb-survey-smoothed_wcovid_vaccinated_or_accept-2021-01-04-to-2021-03-25.csv

OUTPUT:
    - `master_data--{%Y-%m-%d__%H-%M-%S}.csv`
    - This is a merge of the above listed input files with 
        the following columns:
            - 'FIPS' - FIP state code
            - 'State' - State name
            - 'County' - County name
            - 'variable' - Signal/variable
            - 'value' - value of signal/variable
    - Each row representes a *single observation*

INSTRUCTIONS FOR UPDATING:
    - This file will need to be updated to incorporate different
        new data sets.
    - To do so, simply create a function that reads the dataset
        in and wrangles it into the five columns described above.
        The county name and state name cleaning portion should
        work no matter what is included because it relies on the
        FIPS code to overwrite whatever the original data set
        uses to set these uniformly.
    - **Important**: make sure that you manually set the FIPS
        code (if not all variables) when you read data in.
        pandas WILL read FIPS codes as integers, which causes
        matching issues.

Author: Matthew DeVerna, John Bryden
"""
import os
import datetime
import pandas as pd
import glob
import numpy as np
import scipy.stats as stats

# utils.py from this repo
from utils import parse_cl_args, parse_config_file, Geo

### Create Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def clean_People_csv(data_path,state_level = False):
    """Clean People.csv county-level data."""

    input_vars = ["TotalPop2010","WhiteNonHispanicPct2010","BlackNonHispanicPct2010","AsianNonHispanicPct2010","NativeAmericanNonHispanicPct2010","HispanicPct2010","Under18Pct2010","Age65AndOlderPct2010"]

    dtype={
            "FIPS":str,
            "State":str,
            "County":str
        }
    dtype.update({v:float for v in input_vars})
    
    data = pd.read_csv(
        data_path, 
        usecols= ["FIPS","State","County"]+input_vars,
        dtype=dtype
    )

    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)
    
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars=input_vars)
    
    return data

def clean_Income_csv(data_path,state_level = False):
    """Clean Income.csv county-level data."""
    
    data = pd.read_csv(
        data_path, 
        usecols= ["FIPS","State","County","MedHHInc"],
        dtype={
            "FIPS":str,
            "State":str,
            "County":str,
            "MedHHInc":float # This needs to be set as a float or the data doesn't load
        }
    )

    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)
     
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars="MedHHInc")
    
    return data

def clean_Education_csv(data_path,state_level=False):
    """Clean Education.csv county-level data."""
    
    data = pd.read_csv(
        data_path, 
        usecols= ["FIPS Code","State","Area name","Percent of adults with a bachelor's degree or higher, 2015-19"],
        dtype={
            "FIPS Code":str,
            "State":str,
            "Area name":str,
            "Percent of adults with a bachelor's degree or higher, 2015-19":float # This needs to be set as a float or the data doesn't load
        },
        encoding='Latin-1'
    )

    data = data.rename(columns={'FIPS Code':'FIPS','Area name':'County'})
    
    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)

    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars="Percent of adults with a bachelor's degree or higher, 2015-19")
    
    return data


def clean_Unemployment_csv (data_path, state_level = False):
    """Clean Unemployment.csv county-level data."""
    
    data = pd.read_csv(
        data_path, 
        dtype={
            "fips_txt":str,
            "Stabr":str,
            "area_name":str,
            "Attribute":str,
            "Value":float
        }
    )

    data = data.rename(columns={
        'fips_txt':'FIPS',
        'Stabr':'State',
        'area_name':'County',
        'Attribute':'variable',
        'Value':'value'
    })

    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)

    # Extract only the rows we're interested int
    data = data[data.variable=='Unemployment_rate_2019'].copy()

    return data


def clean_PovertyData_csv (data_path, state_level=False):
    """Clean Poverty county-level data."""
    
    data = pd.read_csv(
        data_path, 
        dtype={
            "FIPStxt":str,
            "Stabr":str,
            "Area_name":str,
            "Attribute":str,
            "Value":float
        }
    )

    data = data.rename(columns={
        'FIPStxt':'FIPS',
        'Stabr':'State',
        'Area_name':'County',
        'Attribute':'variable',
        'Value':'value'
    })
    
    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)
        
     # Extract only the rows we're interested int
    data = data[data.variable=='POVALL_2019'].copy()

    return data


def clean_Rurality_csv(data_path, state_level=False):
    """Clean rurality county-level data."""
    
    data = pd.read_csv(
        data_path,
        sep=';',
        usecols= ["FIPS","State","County_Name","RUCC_2013"],
        dtype={
            "FIPS":str,
            "State":str,
            "County_Name":str,
            "RUCC_2013":float # This needs to be set as a float or the data doesn't load
        }
    )
        
    data = data.rename(columns={'County_Name':'County'})

    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)
    
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars="RUCC_2013")
    
    return data


def clean_Religiosity_csv(data_path):
    """Clean religiosity county-level data."""
    
    data = pd.read_csv(
        data_path,
        usecols= ["FIPS","STNAME","CNTYNAME","TOTRATE"],
        dtype={
            "FIPS":str,
            "STNAME":str,
            "CNTYNAME":str,
            "TOTRATE":float # This needs to be set as a float or the data doesn't load
        }
    )

    
    data = data.rename(columns={
        'STNAME':'State',
        'CNTYNAME':'County'
    })

    data = data[~data.FIPS.isna()]


    
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars="TOTRATE")
    
    return data


def clean_Religiosity_csv_state (data_path):
    """Clean religiosity county-level data."""
    
    data = pd.read_csv(
        data_path,
        usecols= ["STNAME","STCODE","TOTRATE"],
        dtype={
            "STNAME":str,
            "STCODE":int,
            "TOTRATE":float # This needs to be set as a float or the data doesn't load
        }
    )

    
    data = data.rename(columns={
        'STNAME':'State',
    })

    data['FIPS'] = data.STCODE.apply(lambda x: str(x*1000).zfill(5))
    data['County'] = ''
    
    data = data[~data.FIPS.isna()]
    
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars="TOTRATE")
    
    return data


def get_stderr(num_accept,sample_size):
    return stats.sem(np.concatenate( [
        np.ones(int(num_accept)),
        np.zeros(int(sample_size-num_accept))
    ]))

def clean_FB_survey_csv(data_path,state_level = False):
    """Clean facebook survey county-level data."""
    
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

    start_date = "REFUSAL_START"
    end_date = "REFUSAL_END"

    start = pd.to_datetime(config["DATES"][start_date])
    end = pd.to_datetime(config["DATES"][end_date])

    data = data[(data.DateTime>=start) & (data.DateTime<=end)].copy()

    data['num_accept'] = data.sample_size*(data.value/100.0)
    aggregate = data.groupby('geo_value', as_index=False).sum()

    # Calculate the new variables for the aggregates
    aggregate['mean_smoothed_covid_vaccinated_or_accept'] = aggregate.num_accept/aggregate.sample_size 
    aggregate['stderr_smoothed_covid_vaccinated_or_accept'] = aggregate.apply(lambda x: get_stderr(x['num_accept'],x['sample_size']),axis=1)

    if not state_level:
        fips_map = Geo().get_county_state_to_fips_map(unique_fips=True)
        data = pd.merge(aggregate,fips_map,left_on='geo_value',right_on='fips_code')
    else:
        state_abbr = Geo().get_state_to_fips_map()
        data = pd.merge(aggregate,state_abbr,left_on='geo_value',right_on='abbr_lower')
        data['County'] = ''
        
    data = data.rename(columns={'fips_code':'FIPS','num_accept':'num_smoothed_covid_vaccinated_or_accept','sample_size':'sample_size_for_covid_vaccinated_or_accept_question'})
    
    # This will help to create a standard set of columns, which will be:
    #     ["FIPS","State", "County", "variable", "value"]
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars=["mean_smoothed_covid_vaccinated_or_accept","stderr_smoothed_covid_vaccinated_or_accept","num_smoothed_covid_vaccinated_or_accept","sample_size_for_covid_vaccinated_or_accept_question"])
    
    return data

def clean_OWID_vaccine_uptake_csv(config, early=False):
    """Clean vaccine uptake data"""

    data_path = os.path.join(config["PATHS"]["STATE_DATA_DIR"],config["FILES"]["OWID_DATA_FILE"])

    cols = ["daily_vaccinations_per_million","people_vaccinated_per_hundred","people_fully_vaccinated_per_hundred","share_doses_used"]
    
    data = pd.read_csv(
        data_path,
        usecols= ["date","location"]+cols,
        dtype={
            "location":str,
            "date":str,
        }.update({c:float for c in cols})
    )

    data['DateTime'] = pd.to_datetime(data['date'])

    start_date = "UPTAKE_START"
    end_date = "UPTAKE_END"

    if early:
        start_date = "UPTAKE_EARLY_START"
        end_date   = "UPTAKE_EARLY_END"
    
    start = pd.to_datetime(config["DATES"][start_date])
    end = pd.to_datetime(config["DATES"][end_date])

    time_period = data[(data.DateTime>=start) & (data.DateTime<=end)].copy()

    grouped_data=time_period.groupby(time_period.location).mean().reset_index()
    # Fix NY bug in OWID data
    grouped_data.loc[grouped_data.location=='New York State','location']='New York'

    merged_data = pd.merge(grouped_data,Geo().get_state_to_fips_map(),left_on='location',right_on='State')
    merged_data['County'] = ''

    if early:
        old_cols = cols
        merged_data = merged_data.rename(columns = {col:'early_'+col for col in old_cols}).copy()
        cols = ['early_'+col for col in old_cols]
        
    data = merged_data.melt(id_vars=["FIPS","State", "County"], value_vars=cols)
    
    return data

def clean_Gini_csv(data_path, state_level=False):
    """Clean Gini.csv county-level data."""
    
    data = pd.read_csv(
        data_path,
        header = 1,    # There is a weird extra line, so I manually select the header row
        dtype={
            'id':"str",
            'Geographic Area Name':str,
            'Estimate!!Gini Index':float,
            'Margin of Error!!Gini Index':float
        }
    )
    
    # Those are some funky column names, lets change them
    data.rename(
        columns={
            "Estimate!!Gini Index" : "Gini_Est",
            "Margin of Error!!Gini Index" : "Gini_Est_Margin_of_Error"
            },
        inplace = True
    )
    
    # This column is a string which looks like the below...
    #    "Baldwin County, Alabama"
    # ... so we split on the "," creating two new columns
    data[["County", "State"]] = data["Geographic Area Name"].str.split(",", expand = True)
    
    # This column is a string looks like the below...
    #    "0500000US01003"
    # ... so we split on the "US" creating two new columns
    data[["Unknown", "FIPS"]] = data.id.str.split("US", expand = True)

    if state_level:
        data = data[(data['FIPS'].astype(int) % 1000 ==0) & (data.FIPS.astype(int) != 0)].copy()
        data['County'] = ''
        if len(data) == 0:
            print ('Warning, no state level data for',data_path)
    
    # Now we have a DF with the following columns...
    #    ['id', 'Geographic Area Name', 'Gini_Est', 'Gini_Est_Margin_of_Error',
    #   'County', 'State', 'Unknown', 'FIPS']
    # ... so we can melt this into our long, standardized form via
    data = data.melt(
        id_vars=["FIPS","State", "County"], 
        value_vars=["Gini_Est","Gini_Est_Margin_of_Error"]
    )
    return data

def clean_Election_csv(data_path):
    """Clean county_2020_elections.csv county-level data."""
    
    data = pd.read_csv(
        data_path,
        usecols=[
            "state_name","county_fips","county_name",
            "per_gop", "per_dem", "total_votes"
        ],
        dtype = {
            "state_name":str,
            "county_fips":str,
            "county_name":str,
            "per_gop":float,
            "per_dem":float,
            "total_votes":float
        }
    )
    
    # Rename columns to match the standard
    data.rename(
        columns={
            "state_name":"State",
            "county_fips":"FIPS",
            "county_name":"County",
            "per_dem":"prop_dem_vote",
            "per_gop":"prop_gop_vote"
        },
        inplace = True
    )
    
    # Melt into the proper format
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars=["prop_gop_vote","prop_dem_vote","total_votes"])
    
    return data

def clean_Election_csv_state(config):
    """Clean 1976-2020-president.csv state-level data."""

    elections = pd.read_csv(os.path.join (config["PATHS"]["STATE_DATA_DIR"],config["FILES"]["PRESIDENTIAL_STATE_ELECTIONS"]))

    gop_votes = elections[(elections.year==2020) & (elections.party_simplified == 'REPUBLICAN')].copy()
    gop_votes['prop_gop_vote'] = gop_votes.candidatevotes/gop_votes.totalvotes
    gop_votes['FIPS'] = gop_votes.state_fips.astype(int).apply(lambda x: str(x*1000).zfill(5))

    dem_votes = elections[(elections.year==2020) & (elections.party_simplified == 'DEMOCRAT')].copy()
    dem_votes['prop_dem_vote'] = dem_votes.candidatevotes/dem_votes.totalvotes
    dem_votes['FIPS'] = dem_votes.state_fips.astype(int).apply(lambda x: str(x*1000).zfill(5))

    data = pd.merge(gop_votes[['prop_gop_vote','totalvotes','state','FIPS']],dem_votes[['prop_dem_vote','FIPS']],on='FIPS')

    data['County'] = ''
    data=data.rename(columns={'state':'State','totalvotes':'total_votes'})
    
    data.reset_index()
    
    # Melt into the proper format
    data = data.melt(id_vars=["FIPS","State", "County"], value_vars=["prop_gop_vote","prop_dem_vote","total_votes"])
    
    return data

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
            min_misinfo,
            max_misinfo
        ],
        [
            'No. accounts',
            'No. tweets',
            'Mean % low-credibility',
            'Stderr % low-credibility',
            'Min % low-credibility',
            'Max % low-credibility',
        ]
    )

def clean_Twitter_csv_state(data_path,just_state_identified_accounts = False):
    
    twitter_data = pd.read_csv(data_path)
    
    if just_state_identified_accounts:
        state_data = twitter_data[(df.county.isna()) | (df.county == 'None')].groupby('state').apply(lambda x: get_summary_stats(x))
    else:
        state_data = twitter_data.groupby('state').apply(lambda x: get_summary_stats(x))

    state_data = state_data.reset_index()
    state_data = state_data.rename(columns={'county':'County','state':'State'})
    
    fips_map = Geo().get_state_to_fips_map()
    data = pd.merge(state_data,fips_map,on='State')
    data['County'] = ''

    data = data.melt(id_vars=["FIPS","State", "County"], value_vars=[
        'No. accounts',
        'No. tweets',
        'Mean % low-credibility',
        'Stderr % low-credibility',
        'Min % low-credibility',
        'Max % low-credibility',
    ])
    return data
   
    
def threshold_accounts(df, accounts_per_county, tweets_per_account, only_with_county=True):
    # selection only those with a county
    if only_with_county:
        df = df[(~df.county.isna()) & (df.county != 'None')].copy()

    # filter out accounts within the two thresholds
    filtered_accounts = df[df["no_tweets"]>=tweets_per_account].groupby(["state","county"]).filter(lambda x : x.__len__()>=accounts_per_county).copy()

    results = filtered_accounts.groupby(["state","county"]).apply(lambda x: get_summary_stats(x))
    results = results.reset_index()
    
    return results

def clean_Twitter_csv(data_path):

    twitter_data = pd.read_csv(data_path)

    twitter_data = twitter_data.replace('St. Tammany Parish','St Tammany Parish')
    twitter_data = twitter_data.replace('St. Joseph County','St Joseph County')
    
    results_data_list = []
    
    for no_accounts in [1,10,50,100]:
        for no_tweets in [1,10,50,100,200,500]:
            suffix=f'{no_accounts}_accounts_{no_tweets}_tweets '

            thresholded_accounts = threshold_accounts(twitter_data,no_accounts,no_tweets)
            if len(thresholded_accounts)<1:
                continue

            thresholded_accounts = thresholded_accounts.rename(columns={'county':'County','state':'State'})

            fips_map = Geo().get_county_state_to_fips_map(unique_fips=False)
    
            twitter_data_with_fips = pd.merge(thresholded_accounts,fips_map,on=['County','State'],how='left') 
    
            missing = twitter_data_with_fips[twitter_data_with_fips.fips_code.isna()][['County','State']]
            if len(missing)>0:
                print ("For ",suffix)
                print ("Missing the following counties' fips codes")
                print (missing)

            # These are the data columns from the Twitter data file we are going to
            # add suffix at the front of each of these for the output.
            # The filename has the thresholds for the numbers of tweets and accounts
            columns = 'Mean % low-credibility,Stderr % low-credibility,Min % low-credibility,Max % low-credibility,No. accounts,No. tweets'.split(',')
    
            output_columns = {c:suffix+c for c in columns}

            twitter_data_to_output = twitter_data_with_fips.rename(columns=output_columns)

            data = twitter_data_to_output.rename(columns={'fips_code':'FIPS'})

            data = data.melt(id_vars=["FIPS","State", "County"], value_vars=list(output_columns.values()))
            data = data[~data.FIPS.isna()]
            results_data_list += [data,]

    return pd.concat(results_data_list, sort=False)


def clean_AggCasesDeaths_csv(data_path):
    """Clean aggregate-cases_deaths county-level data. """
    
    data = pd.read_csv(
        data_path,
        index_col = 0,
        dtype = {
            "geo_value" : str,
            "signal" : str,
            "value" : float,
            "geo_name" : str,
            "state" : str
        }
    )

    data.rename(
        columns={
            "geo_value" : "FIPS",
            "signal" : "variable",
            "geo_name" : "County",
            "state" : "State"
        },
        inplace = True
    )

    
    return data

def clean_AggCasesDeaths_csv_state(data_path):
    """Clean aggregate-cases_deaths county-level data. """
    
    data = pd.read_csv(
        data_path,
        index_col = 0,
        dtype = {
            "geo_value" : str,
            "signal" : str,
            "value" : float,
        }
    )

    
    data.rename(
        columns={
            "signal" : "variable",
            "geo_value": "FIPS",
            "state": "State"
        },
        inplace = True
    )

    data['County'] = ''

    return data[['FIPS', 'State', 'County', 'variable', 'value']].copy()


### Execute Main Script ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == '__main__':
    # Since we are using relative paths, we should ensure that the
    #    script is being run in the proper directory
    cwd = os.getcwd()

    if os.path.basename(cwd) != "src":
        raise Exception("CHANGE CURRENT WORKING DIRECTORY TO THE `src` PATH BEFORE RUNNING!!")

    # Load config_file_path from commandline input
    args = parse_cl_args()
    config_file_path = args.config_file

    state_level = args.state_level
    keywords_filter = args.keywords_filter

    
    # Get config file object
    config = parse_config_file(config_file_path)

    # Intialize the Geo class and load lookup tables/dicts
    g = Geo()
    fip_lookup = g.load_fip_code_lookup()
    state_lookup = g.load_state_abbrv_lookup(as_dict=True)

    # Get base dir for county-level data and set data file paths
    county_data_dir = config["PATHS"]["COUNTY_DATA_DIR"]
    state_data_dir = config["PATHS"]["STATE_DATA_DIR"]
    covid_data_dir = config["PATHS"]["COVID_DATA_DIR"]
    intermediate_data_dir = config["PATHS"]["INTERMEDIATE_DATA_DIR"]
    
    people_file_path = os.path.join(county_data_dir, config["FILES"]["COUNTY_PEOPLE"])
    income_file_path = os.path.join(county_data_dir, config["FILES"]["COUNTY_INCOME"])
    gini_file_path = os.path.join(county_data_dir, config["FILES"]["COUNTY_GINI"])
    election_file_path = os.path.join(county_data_dir, config["FILES"]["COUNTY_ELECTIONS"])
    education_file_path = os.path.join(county_data_dir, config["FILES"]["EDUCATION"])
    unemployment_file_path = os.path.join(county_data_dir, config["FILES"]["UNEMPLOYMENT"])
    poverty_file_path = os.path.join(county_data_dir, config["FILES"]["POVERTY"])
    rurality_file_path = os.path.join(county_data_dir, config["FILES"]["RURALITY"])
    if state_level:
        religiosity_file_path = os.path.join(state_data_dir, config["FILES"]["RELIGIOSITY_STATE"])
    else:
        religiosity_file_path = os.path.join(county_data_dir, config["FILES"]["RELIGIOSITY_COUNTY"])
    county_vaccine_acceptance_file_path = os.path.join(county_data_dir,config["FILES"]["VACCINE_ACCEPTANCE_COUNTY"])
    state_vaccine_acceptance_file_path = os.path.join(state_data_dir,config["FILES"]["VACCINE_ACCEPTANCE_STATE"])
    if state_level:
        agg_cases_deaths_file = os.path.join(covid_data_dir,config["FILES"]["AGGR_CASES_FILE_STATE"])
    else:
        agg_cases_deaths_file = os.path.join(covid_data_dir,config["FILES"]["AGGR_CASES_FILE"])

    if keywords_filter:
        twitter_data_file = os.path.join(intermediate_data_dir,config["FILES"]["ACCOUNTS_DATA_FILE_KEYWORDS_FILTERED"])
    else:
        twitter_data_file = os.path.join(intermediate_data_dir,config["FILES"]["ACCOUNTS_DATA_FILE"])
    
    # Load and clean data into the standardized columns format
    #    ['FIPS', 'State', 'County', 'variable', 'value']
    people_data = clean_People_csv(people_file_path,state_level = state_level)
    income_data = clean_Income_csv(income_file_path,state_level = state_level)
    gini_data = clean_Gini_csv(gini_file_path,state_level = state_level)
    education_data = clean_Education_csv(education_file_path,state_level = state_level)
    unemployment_data = clean_Unemployment_csv(unemployment_file_path,state_level = state_level)
    poverty_data = clean_PovertyData_csv(poverty_file_path,state_level = state_level)
    rurality_data = clean_Rurality_csv(rurality_file_path,state_level = state_level)
    if state_level:
        religiosity_data = clean_Religiosity_csv_state(religiosity_file_path)
    else:
        religiosity_data = clean_Religiosity_csv(religiosity_file_path)
        
    if state_level:
        agg_cases_deaths_data = clean_AggCasesDeaths_csv_state(agg_cases_deaths_file)
    else:
        agg_cases_deaths_data = clean_AggCasesDeaths_csv(agg_cases_deaths_file)

    if state_level:
        vaccine_acceptance_data = clean_FB_survey_csv(state_vaccine_acceptance_file_path,state_level = state_level)
    else:
        vaccine_acceptance_data = clean_FB_survey_csv(county_vaccine_acceptance_file_path)
        
    if state_level:
        election_data = clean_Election_csv_state(config)
    else:
        election_data = clean_Election_csv(election_file_path)

    if state_level:
        twitter_data = clean_Twitter_csv_state(twitter_data_file,False)
    else:
        twitter_data = clean_Twitter_csv(twitter_data_file)
    
    all_data = [
        people_data,
        income_data,
        gini_data,
        election_data,
        education_data,
        unemployment_data,
        poverty_data,
        rurality_data,
        religiosity_data,
        vaccine_acceptance_data,
        twitter_data,
        agg_cases_deaths_data
        ]

    

    if state_level:
        vaccination_uptake_data=clean_OWID_vaccine_uptake_csv(config)
        early_vaccination_uptake_data=clean_OWID_vaccine_uptake_csv(config,early=True)
        all_data += [vaccination_uptake_data,early_vaccination_uptake_data,]

    
    # Merge data
    tidy_data = pd.concat(all_data,sort=False)

    # Pad the start of all FIPS entries with zeros so they are of length 5
    tidy_data.FIPS=tidy_data.FIPS.apply(lambda x: x.zfill(5))

    if state_level:
        # Remove counties and the country
        state_filter = ((tidy_data.FIPS.astype(int) % 1000)==0) & (tidy_data.FIPS.astype(int) != 0)
        tidy_data = tidy_data[state_filter].copy()
    else:
        # Remove just states or countries
        county_filter = (tidy_data.FIPS.astype(int) % 1000)!=0
        tidy_data = tidy_data[county_filter].copy()
    
    # Create a fip_state_code --to--> proper state name dictionary
    states_only = fip_lookup.loc[fip_lookup["geo_level"] == "State"]
    zipper = zip(states_only["state_code_fips"], states_only["area_name"])
    state_code_dict = {fip_code:name for fip_code,name in zipper}
    
    # Use it to ensure the same state name is in place for all rows
    for state_code in state_code_dict.keys():
        locs = tidy_data["FIPS"].str.startswith(state_code)
        tidy_data.loc[locs, "State"] = state_code_dict[state_code]

    # Create a fip_code --to--> county_name dict to fix county naming differences
    zipper = zip(fip_lookup["fips_code"], fip_lookup["area_name"])
    fip_dict = {fip_code:name for fip_code,name in zipper}

    # Use it to ensure same county name is in place for all rows
    new_names = tidy_data.FIPS.replace(fip_dict)
    tidy_data.loc[:,"County"] = new_names

    # Reset indices, just in case
    tidy_data.reset_index(inplace = True, drop = True)

    # Print some info about the file...
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Aggregation Information:\n")
    print(f"Columns in aggregated file:\n\t- {list(tidy_data.columns)}")
    print(f"Unique FIPS codes:\n\t- {tidy_data.FIPS.nunique()}")
    print(f"Unique States:\n\t- {tidy_data.State.nunique()}")
    print(f"Unique County Names:\n\t- {tidy_data.County.nunique()}")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    if state_level:
        level = 'state_level_'
    else:
        level='county_level_'

    if keywords_filter:
        level += 'keywords_filtered_'
        
    # Write the file to disk with the current date/tome
    now = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d__%H-%M-%S")
    outfile_name = os.path.join(config["PATHS"]["MASTER_DATA_DIR"],level+f"master_data--{now}.csv")
    tidy_data.to_csv(outfile_name, index = False)

    outfile_name_pivoted = os.path.join(config["PATHS"]["MASTER_DATA_DIR"],level+f"wide_data--{now}.csv")

    df_pivot = tidy_data.pivot_table(index="FIPS",columns='variable',values='value').reset_index()
    df_pivot.to_csv(outfile_name_pivoted, index = False)

    print ('Saved to',outfile_name)
    
    print("~~~~~~Script Complete~~~~~~")
