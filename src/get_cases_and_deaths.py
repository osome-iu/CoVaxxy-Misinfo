"""
PURPOSE:
    - A script for downloading USAFacts covid-19 cases and deaths data.
        - This data is downloaded using the CMU CovidCast API
    - Ref: https://cmu-delphi.github.io/delphi-epidata/api/covidcast-signals/usa-facts.html

INPUT:
    - A standard Python config.ini file called, "config.ini"
    - From that file the following variables are read into this script:
        - CASES_SOURCE - data source. In this case, usa-facts
        - CASES_SIGNALS - a comma-separated (no spaces) list of signals to download
        - START_DAY - first day to pull data (%Y-%m-%d format)
        - END_DAY - last day to pull data (%Y-%m-%d format)
        - GEO_TYPE - level of detail at which to return the data ("county" or "state")
            - Default = 'county'. Include `-s` or `--state_level` to retrieve data from
                only the states.
        - LOG_DIR - directory to save log
        - LOG_FILE - name for log file
        - COVID_DATA_DIR - directory to save output file
        - CASES_DATA_FILE - name for the output file

OUTPUT:
    - A file saved to the filename and directory indicated in the config file
    - The following signals will be included. See above reference for details on each signal
        - 'confirmed_incidence_num' - Number of new confirmed COVID-19 cases, daily
        - 'deaths_incidence_num' - Number of new confirmed deaths due to COVID-19, daily
        - 'confirmed_cumulative_num' - Cumulative number of confirmed COVID-19 cases
        - 'deaths_cumulative_num' - Cumulative number of confirmed deaths due to COVID-19

Author: Matthew DeVerna
"""
import argparse
import datetime
import configparser
import logging
import os

import pandas as pd

# API for pulling the data
import covidcast

# utils.py package within this repo
from utils import get_logger, parse_cl_args, parse_config_file, convert_date_str_to_datetime


### Create Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_covid_cast_signal(
    data_source = str,
    signal = str,
    start_day = datetime.date,
    end_day = datetime.date,
    geo_type = "county"
    ):
    """
    Get data from covid cast.

    Parameters:
    - data_source: String identifying the data source to query, such 
        as ``"fb-survey"``.
    - signal: String identifying the signal from that source to query,
        such as ``"smoothed_cli"``.
    - start_day: Query data beginning on this date. Provided as as
        ``datetime.date`` object. If ``start_day`` is ``None``, defaults
        to the first day data is available for this signal.
    - end_day: Query data up to this date, inclusive. Provided as a
        ``datetime.date`` object. If ``end_day`` is ``None``, defaults
        to the most recent day data is available for this signal.
    - geo_type: The geography type for which to request this data, such as
        ``"county"`` or ``"state"``. Available types are described in the
        COVIDcast signal documentation. Defaults to ``"county"``.

    """
    try:
        data = covidcast.signal(data_source, signal, start_day, end_day, geo_type)
        logger.info(f"~~ Downloaded Successfully: SOURCE={data_source}, SIGNAL={signal} ~~")
        return data

    except:
        logger.error(f"Problem downloading: SOURCE={data_source}, SIGNAL={signal}", exc_info = True)

def get_all_covid_cast_data(
    signals = list,
    data_source = str,
    start_day = datetime.date,
    end_day = datetime.date,
    geo_type = "county"
    ):
    """
    Loop over a list of provided signals. Download each signal's data 
    with `get_covid_cast_signal()` and return them as one dataframe.
    """
    logger.info(f"Attemping to downloaded {len(signals)} signals...")
    try:

        # Initialize empty dataframe to fill with all signal data
        combined_data = pd.DataFrame()

        for signal in signals:
            data = get_covid_cast_signal(
                data_source = data_source,
                signal = signal,
                start_day = start_day,
                end_day = end_day,
                geo_type = geo_type
                )

            combined_data = pd.concat([combined_data,data])

        logger.info("~~ All signals downloaded successfully. ~~")
        return combined_data

    except:
        logger.error(f"Problem during download loop.", exc_info = True)

### Execute main script ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
    # Since we are using relative paths, we should ensure that the
    #    script is being run in the proper directory
    cwd = os.getcwd()

    if os.path.basename(cwd) != "src":
        raise Exception("CHANGE CURRENT WORKING DIRECTORY TO THE `src` PATH BEFORE RUNNING!!")

    # Load commandline args
    args = parse_cl_args()
    config_file_path = args.config_file
    state_level = args.state_level

    # Parse config file
    config = parse_config_file(config_file_path)

    # Start logger
    logger = get_logger(
        LOG_DIR = config["PATHS"]["LOG_DIR"],
        LOG_FILE = config["FILES"]["CASES_LOG_FILE"]
        )

    # Handle config input not yet ready for the script
    try:
        logger.info("Trying to parse config input not ready for script...")
        SIGNALS = config["DATA"]["CASES_SIGNALS"].split(",")
        START_DAY = convert_date_str_to_datetime(config["DATA"]["START_DAY"])
        END_DAY = convert_date_str_to_datetime(config["DATA"]["END_DAY"])
        logger.info("~~ Success ~~")

    except:
        logger.error("Problem parse config input not ready for",
            "script (signals, start_day, or end_day).",
            exc_info = True)

    # Log the signals we're attemping to download.
    try:
        logger.info(f"Signals to Download from Source: {config['DATA']['CASES_SOURCE']} \n")
        [logger.info(f"\t|- {signal}") for signal in SIGNALS]
        logger.info("")
    except:
        logger.error("Problem logging signal info", exc_info = True)

    # Set geo_type based on state_level flag
    if state_level:
        geo_type = "state"
    else:
        geo_type = config["DATA"]["GEO_TYPE"]

    # Try and download all signals
    data = get_all_covid_cast_data(
        signals = SIGNALS,
        data_source = config["DATA"]["CASES_SOURCE"],
        start_day = START_DAY,
        end_day = END_DAY,
        geo_type = geo_type
        )

    try:
        # Make the output data dir location if it doesn't exist
        if not os.path.exists(config["PATHS"]["COVID_DATA_DIR"]):
            os.makedirs(config["PATHS"]["COVID_DATA_DIR"])

        logger.info("Writing data to disk...")

        # Write data file to indicated location
        fname = config["FILES"]["CASES_DATA_FILE"]

        # Insert state to mark state-level only, if necessary
        if state_level:
            fname = "--STATE.".join(fname.split("."))

        data.to_csv(os.path.join(config["PATHS"]["COVID_DATA_DIR"],fname), index = False)
        logger.info("~~ Success ~~")

    except:
        logger.info("Problem writing data to disk.", exc_info = True)

    logger.info("~*~*~*~*~*~*~*~*~*~*~*~* Script complete. ~*~*~*~*~*~*~*~*~*~*~*~*")
    logger.info("~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*")
