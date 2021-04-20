"""
PURPOSE:
    - A script to build the FIPS code data table.

INPUT:
    - all-geocodes-v2018-RAW.xlsx

OUTPUT:
    - fip_code_lookup.csv
"""
import argparse
import datetime
import configparser
import os

import pandas as pd

from utils import parse_cl_args, parse_config_file


def load_raw_data(data_path):
    """Load the raw Census FIPS codes data."""

    print("Loading raw data...")
    fips_source = pd.read_csv(
        data_path, 
        dtype= {
            "State Code (FIPS)":str,
            "County Code (FIPS)":str,
            "County Subdivision Code (FIPS)":str,
            "Place Code (FIPS)":str,
            "Consolidtated City Code (FIPS)":str,
        }
    )

    print("\t~~ Success")
    return fips_source

def get_reduced_table(fips_source):
    """There is a lot of extra information in this df,
    lets reduce it to only the county-level resolution.
    """

    print("Grabbing only the columns we want...")
    # Take only country (10), state (40), and county (50)
    reduced_table = fips_source.loc[fips_source["Summary Level"].isin([10, 40, 50])]

    # Write over those numerical codes with a dict map
    # The Census labels resolution via a "summary level"
    #    this map will make sense of those for humans
    summary_map = {
        10 : "Country",
        40 : "State",
        50 : "County"
    }
    reduced_table.loc[:,"Summary Level"] = reduced_table["Summary Level"].map(summary_map)

    # Remove extra columns
    reduced_table = reduced_table[[
        'Summary Level',
        'State Code (FIPS)',
        'County Code (FIPS)',
        'Area Name (including legal/statistical area description)'
        ]]

    print("\t~~ Success")
    return reduced_table

def rename_columns(reduced_table):
    """Rename columns."""

    print("Attempting to rename columns...")
    reduced_table.rename(
        columns={
            'Summary Level':'geo_level',
            'State Code (FIPS)':'state_code_fips',
            'County Code (FIPS)':'county_code_fips',
            'Area Name (including legal/statistical area description)':'area_name'
        },
        inplace = True
    )

    print("\t~~ Success")
    return reduced_table

def construct_full_fips_code(reduced_table):
    """The raw data separates state and county codes, this
    function creates a new column combining those two columns.
    """

    print("Constructing the full FIPS codes...")
    # Create a list of the full fips codes and set to a new column
    full_fips = [state + county for state,county, in zip(reduced_table["state_code_fips"],reduced_table["county_code_fips"])]
    reduced_table["fips_code"] = full_fips

    # Reset the indices so everything is clean
    reduced_table.reset_index(inplace = True, drop = True)

    print("\t~~ Success")
    return reduced_table

if __name__ == '__main__':

    # Parse config file from CL
    config_file = parse_cl_args()

    # Load config file
    config = parse_config_file(config_file)

    # Load raw data
    data_path = os.path.join(config["PATHS"]["MISC_DIR"], config["FILES"]["FIP_RAW"])
    fips_source = load_raw_data(data_path)

    # Take only the columns we want
    reduced_table = get_reduced_table(fips_source)

    # Rename columns
    reduced_table = rename_columns(reduced_table)

    # Rename columns
    reduced_table = construct_full_fips_code(reduced_table)

    # Write file to disk
    print("Writing file to disk...")
    out_file = os.path.join(config["PATHS"]["MISC_DIR"], config["FILES"]["FIP_LOOKUP"])
    reduced_table.to_csv(out_file, index = False)

    print("~*~*~*~*~ Script complete ~*~*~*~*~")
