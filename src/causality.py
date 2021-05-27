from utils import Geo
import pandas as pd
import numpy as np
import scipy.stats as stats
import glob
import datetime as dt
import os
import statsmodels.api as sm
from utils import parse_cl_args, parse_config_file, Geo
from scipy import signal

def detrend_by_county(df):
    new_dfs = []
    for ix, d in df.groupby("FIPS"):
        d_copy = d.copy()
        d_copy["val"] = signal.detrend(d_copy["val"])
        new_dfs.append(d_copy)
    new_dfs = pd.concat(new_dfs)
    return new_dfs

def get_t_val_string(t_val):
    if t_val < 0:
        return 'm'+str(abs(t_val))
    else:
        return str(abs(t_val))

def get_err (merged_data, glm_model, glm_reduced_model):

    tr_fit = sm.OLS.from_formula(glm_model, data=merged_data).fit() 
    treatment_err = sum(tr_fit.resid**2)
    
    null_fit = sm.OLS.from_formula(glm_reduced_model, data=merged_data).fit() 
    null_err = sum(null_fit.resid**2)

    return null_err-treatment_err

def remove_time_trend(df):
    df = df.copy()
    glm_model = 'val ~ t_val'
    fit = sm.OLS.from_formula(glm_model, data=df).fit()
    df.val = fit.resid
    return df

def standardise_variable(d_series):
    mn = np.mean(d_series)
    std = np.std(d_series)
    d_series = (d_series-mn)/std
    return d_series

# Standardise variables, check frac_info which is percent_info.

def run_granger_causality (df_x, df_y, start_t_val, num_vals, verbose=False):
    """ This function takes two dataframes with columns ['FIPS','t_val','val'].
    It returns the mean squared error.
    """

    glm_model = 'x_val ~ 0 + '
    glm_reduced_model = 'x_val ~ 0 + '

    df_x.val = standardise_variable(df_x.val).values
    df_y.val = standardise_variable(df_y.val).values
    
    df_x = df_x.rename(columns={'val':'x_val'})
    df_y = df_y.rename(columns={'val':'y_val'})

    null_columns = []
    treatment_columns = []
    merged_data = df_x

    for lag in range (start_t_val,start_t_val+num_vals):
        
        df_x_var = df_x.rename(columns={'x_val':'x_val_t_minus_'+str(lag)}).copy()

        df_y_var = df_y.rename(columns={'y_val':'y_val_t_minus_'+str(lag)}).copy()
        
        df_x_var.t_val += lag
        df_y_var.t_val += lag

        merged_data = pd.merge(merged_data, df_x_var,on=['FIPS','t_val'])
        merged_data = pd.merge(merged_data, df_y_var,on=['FIPS','t_val'])

        if lag != start_t_val:
            glm_model += ' + '
            glm_reduced_model += ' + '
            
        glm_model += 'x_val_t_minus_'+str(lag)
        glm_model += ' + y_val_t_minus_'+str(lag)
        glm_reduced_model += 'x_val_t_minus_'+str(lag)

    if verbose:
        print ()
        print ("Merged data, to",len(merged_data),"rows")
        print ("With",len(merged_data.FIPS.unique()),"regions")
        print ()

    if verbose:
        print (glm_model)
    treatment_fit = sm.OLS.from_formula(glm_model, data=merged_data).fit() 

    if verbose:
        print (treatment_fit.summary())

    treatment_err = sum(treatment_fit.resid**2)
        
    null_fit = sm.OLS.from_formula(glm_reduced_model, data=merged_data).fit()
    

    if verbose:
        print (null_fit.summary())
        print ('Mean frac param =',np.mean(treatment_fit.params [[i for i in range(1,len(treatment_fit.params),2)]]))
        
    null_err = sum(null_fit.resid**2)
    
    #    subplot (2,1,1)
    #    hist(null_fit.resid_response)
    #    subplot (2,1,2)
    #    hist(treatment_fit.resid_response)

    final_diff = null_err-treatment_err

    if verbose:
        print ("ERR difference",final_diff)  
        print ("AIC difference according to OLS",treatment_fit.aic-null_fit.aic)
        print ("Treatment AIC",treatment_fit.aic)

    return [final_diff,treatment_fit,null_fit]

def test_granger_causality (df_x, df_y, start_t_val, num_vals, n_trials, verbose=False):
    df_x = detrend_by_county(df_x)
    df_y = detrend_by_county(df_y)

    err_diff_val, treatment_fit, null_fit = run_granger_causality(df_x, df_y, start_t_val, num_vals, verbose)

    df_y = df_y.sort_values('FIPS')
    hits = 0
    for i in range (0,n_trials):
        # shuffle the y data variable to remove any time signature
        shuffled = df_y.copy()
        shuffled.val = shuffled.groupby('FIPS').apply(lambda x: x.sample(frac=1)).val.values
        err_diff_test, treatment_fit_test, null_fit_test = run_granger_causality(df_x,shuffled, start_t_val, num_vals, verbose=False)
        if err_diff_test > err_diff_val:
            hits += 1
        if i % 100 == 0 and verbose:
            print (i, hits)

    return err_diff_val,hits/float(n_trials),treatment_fit,null_fit

def run_code(config,order = 6, n_trials = 1000, backward=False, verbose=True, state_level = False, output_csv=""):
    
    start_t_val = 1
    time_window = 1


    misinfo_path = os.path.join(config["PATHS"]["TABLES_TEMPORAL_FOLDER"],str(time_window)+'day')
    aggregate_misinfo_name = 'aggregate_misinfo_'+str(time_window)+'.csv'
    if state_level:
        aggregate_misinfo_name = 'state_level_'+aggregate_misinfo_name
    
    df_misinfo = pd.read_csv(os.path.join(misinfo_path,aggregate_misinfo_name))

    if state_level:
        survey_path = config["PATHS"]["STATE_DATA_DIR"]
    else:
        survey_path = config["PATHS"]["COUNTY_DATA_DIR"]
        
    aggregate_survey_name = 'aggregate_survey_data_days_'+str(time_window)+'.csv'
    
    df_acceptance = pd.read_csv(os.path.join(survey_path,aggregate_survey_name))
    df_acceptance['hesitancy'] = 1.0-df_acceptance.mean_smoothed_covid_vaccinated_or_accept
    
    df_acceptance_outcome = df_acceptance[['FIPS','t_val','hesitancy']].copy().rename (columns={'hesitancy':'val'})
    df_misinfo_outcome = df_misinfo[['FIPS','t_val','Frac low-credibility']].copy().rename(columns={'Frac low-credibility':'val'})


#    print (df_misinfo_outcome)
#    print (df_acceptance_outcome)
    if not backward:
        print ('x=acceptance, y=misinfo')
        err_diff_val,p_val,treatment_fit,null_fit = test_granger_causality(df_acceptance_outcome,df_misinfo_outcome,start_t_val,order,n_trials,verbose=verbose)
        print (err_diff_val,p_val)

    else:
        print ('x=misinfo, y=acceptance')
        err_diff_val,p_val,treatment_fit,null_fit = test_granger_causality(df_misinfo_outcome,df_acceptance_outcome,start_t_val,order,n_trials,verbose=verbose)
        print (err_diff_val,p_val)

    print ()

    if output_csv != "":
        fout = open(output_csv,'w')
        fout.write(treatment_fit.summary().as_csv())
        fout.write ('\n\n')
        fout.write(null_fit.summary().as_csv())
        fout.close()
    
    return treatment_fit,null_fit

# MAIN CODE

if __name__ == '__main__':
    # Load config_file_path from commandline input
    args = parse_cl_args()
    config_file_path = args.config_file
    state_level = args.state_level
    
    # Get config file object
    config = parse_config_file(config_file_path)

    for i in range(2,20):
        print ('Testing with order =',i)
        run_code(config,i,1,backward=False, verbose=False,state_level=state_level)

    run_code(config,6,100,verbose=True,state_level=state_level)

        
