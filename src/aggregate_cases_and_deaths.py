"""
PURPOSE:
    - This file aggregates the data that is downloaded with
        the `get_cases_and_deaths.py` script. See that file for
        more details
    - Essentially, this file takes the most recent CUMULATIVE
        signals listed below (no aggregation) and then aggregates
        the INCIDENCE signals based on the time period for which
        we have data.
    - It also adds the county and state names to each row, 
        using the `covidcast` convenience functions.

INPUT: 
    - A file downloaded with `get_cases_and_deaths.py`
    - The filename will be:
        ---> "cases_deaths--2021-1-1--2021-3-7.csv"
    - If the '-s' flag is passed at the command line it will process the
        state-only version of the above file.
    - The signals included will be:
        - 'confirmed_incidence_num' - Number of new confirmed COVID-19 cases, daily 
        - 'deaths_incidence_num' - Number of new confirmed deaths due to COVID-19, daily 
        - 'confirmed_cumulative_num' - Cumulative number of confirmed COVID-19 cases 
        - 'deaths_cumulative_num' - Cumulative number of confirmed deaths due to COVID-19 
    - Details on signals found via below link:
        - https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/usa-facts.html

OUTPUT:
    - A single aggregate file which looks at the time period
        ---> 2021-01-04 -- 2021-03-07
    - Filename will be: 
        - aggregate-cases_deaths--2021-1-1--2021-3-7.csv
    - Each row will represent a single county for one of the four signals
    - Signal names will be:
        - 'recent_cases_cum' - Cumulative *cases* for the observed time period 
        - 'recent_deaths_cum' - Cumulative *deaths* for the observed time period
        - 'total_cases_cum' - Cumulative *cases* for the ENTIRE time period observed by CovidCast
        - 'total_deaths_cum' - Cumulative *deaths* for the ENTIRE time period observed by CovidCast
        - See update_signal_names() below for how the original signal names are updated

Author: Matthew DeVerna
"""
import argparse
import configparser
import os
import json

import covidcast

import pandas as pd

# utils.py from this repo
from utils import parse_cl_args, parse_config_file


### Create Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def load_data(file_path):
    """Load data based on provided file path"""

    print("Trying to load cases & deaths data...")
    data = pd.read_csv(
        file_path, 
        parse_dates=["time_value", "issue"], 
        dtype = {"geo_value":str,
                 "signal":str,
                 "lag":int,
                 "value":float,
                 "stderr":float,
                 "sample_size":float,
                 "geo_type":str,
                 "data_source":str
            }
        )

    print("\tData loaded successfully...")
    return data

def aggregate_data(data, signals):
    """Create aggregate dataframe"""
    
    print("Trying to aggregate data...")
    # Create empty dataframe to fill with new data
    aggregate = pd.DataFrame()

    # Sum all "incidence" (daily) values and select the columns we need
    recent_cum_for_sig = data[data.signal.str.contains('incidence')].groupby(["geo_value","signal"])['value'].sum().reset_index()

    # Select the most recent "cumulative" rows for the same columns
    cum_sig = data[data.signal.str.contains('cumulative')]
    total_cum_for_sig = cum_sig[cum_sig["time_value"] == cum_sig.time_value.max()][["geo_value", "signal", "value"]]

    # Concatenate these subframes into one larger frame
    aggregate = pd.concat([aggregate,recent_cum_for_sig])
    aggregate = pd.concat([aggregate,total_cum_for_sig])

    print("\tData aggregated successfully.")
    return aggregate

def update_signal_names(aggregate):
    """Update signal names based on the below map"""

    print("Trying to update signal names...")
    signal_map = {
        'confirmed_incidence_num' : 'recent_cases_cum',
        'deaths_incidence_num' : 'recent_deaths_cum',
        'confirmed_cumulative_num' : 'total_cases_cum',
        'deaths_cumulative_num' : 'total_deaths_cum'
        }
    aggregate["signal"] = aggregate.signal.map(signal_map)

    print("\tSignal names updated successfully.")
    return aggregate

def load_fip_state_json(file_path):
    """
    Load fip code to state dictionary
    
    This is a dictionary where:
        - keys = "fip_code"
        - vals = "State_name"
    """
    
    print("Trying to load fip_state.json...")
    with open(file_path, "r") as f:
        for line in f:
            fip_state = json.loads(line)

    print("\tfip_state.json loaded successfully.")
    return fip_state

def add_names_states(aggregate, fip_state, state = False):
    """Add the county and state names for each row"""

    if state:
        print("Trying to add FIPS values and state names...")
        # Use the covidcast convenience function to overwrite the state
        # abbreviations with the fips values
        aggregate["geo_value"] = covidcast.abbr_to_fips(
            list(aggregate["geo_value"].str.upper()),   # it likes lists
            ties_method="first"                         # this returns a single value vs. a dictionary
            )
        # Now get the state names and put them in their own column
        aggregate["geo_name"] = covidcast.fips_to_name(
            list(aggregate["geo_value"]), # it likes lists
            ties_method="first"           # this returns a single value vs. a dictionary
            )

        # At the county-level geo_name = county name. Here it is the state name
        # We add this duplicate column to keep the output consistent
        aggregate["state"] = aggregate["geo_name"]

        print("\t FIPS values and state names added successfully.")
        return aggregate

    print("Trying to add county and state names...")
    # Use the covidcast convenience function to add county names
    aggregate["geo_name"] = covidcast.fips_to_name(
        list(aggregate["geo_value"]), # it likes lists
        ties_method="first"           # this returns a single value vs. a dictionary
        )

    # Use the fip_state dict to add state names
    states = []

    for fip_code in aggregate["geo_value"]:
        """
        The below chunk of code matches the first two numbers from
        the fip score in the dataframe to the first two numbers from
        the fip score in the fip-to-state dictionary, returning the state.

        This works because the first two numbers of a fip code indicate
        the state.
        """
        state_indicator = fip_code[:2]
        state = [state for fip, state in fip_state.items() if state_indicator == fip[:2]][0]
        
        # Now we can store that state value
        states.append(state)

    # Add state values to new column
    aggregate["state"] = states

    print("\tCounty and state names added successfully.")
    return aggregate 


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
    
    # Get config file object
    config = parse_config_file(config_file_path)

    # Load data to aggregate
    if state_level:
        fname = os.path.join(config["PATHS"]["COVID_DATA_DIR"],config["FILES"]["CASES_DATA_FILE_STATE"])
    else:
        fname = os.path.join(config["PATHS"]["COVID_DATA_DIR"],config["FILES"]["CASES_DATA_FILE"])
    data = load_data(fname)

    # Get list of signals
    signals = list(data.signal.unique())

    # Aggregate the data
    aggregate = aggregate_data(data, signals)

    # Update the signal names based on the below map
    aggregate = update_signal_names(aggregate)

    # Get fip code to state dictionary
    fip_dict_path = os.path.join(config["PATHS"]["COVID_DATA_DIR"],config["FILES"]["FIP_DICT"])
    fip_state = load_fip_state_json(fip_dict_path)

    # Add state and country names
    aggregate = add_names_states(aggregate, fip_state, state=state_level)

    # Save file
    if state_level:
        fname = os.path.join(config["PATHS"]["COVID_DATA_DIR"],config["FILES"]["AGGR_CASES_FILE_STATE"])
    else:
        fname = os.path.join(config["PATHS"]["COVID_DATA_DIR"],config["FILES"]["AGGR_CASES_FILE"])
    aggregate.to_csv(fname)

    print("~*~*~*~*~*~*~**~*~*~*|| Script Complete ||~*~*~*~*~*~*~**~*~*~*")
