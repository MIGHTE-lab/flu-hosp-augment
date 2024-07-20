import numpy as np
import pandas as pd
from constants import *


def logit(x):
    return np.log(x / (1 - x))

def expit(x):
    return 1 / (1 + np.exp(-x))


def load_mmwr_map():
    df = pd.read_csv('./submission/CDC_season_lookup.csv',
                     dtype={'Season': str})
    # from pdb import set_trace; set_trace()
    df['Sunday'] = pd.to_datetime(df['Sunday'])
    df['Saturday'] = df['Sunday'] + pd.Timedelta(days=6)
    df = df.drop('is_GFT', axis=1)
    
    # 40-51
    df['Fall'] = 0
    df.loc[(df['WEEK'] >= 40) & (df['WEEK'] < 52), 'Fall'] = 1

    # 52-10
    df['Winter'] = 0
    df.loc[(df['WEEK'] >= 52) | (df['WEEK'] < 11), 'Winter'] = 1

    # 11-20
    df['Spring'] = 0
    df.loc[(df['WEEK'] >= 11) & (df['WEEK'] <= 20), 'Spring'] = 1

    # score 2022-2023 and 2023-present flu seasons
    df['score'] = 0
    df.loc[(df['YEAR'] == 2022) & (df['WEEK'] >= 40), 'score'] = 1
    df.loc[(df['YEAR'] == 2023) & (df['WEEK'] <= 20), 'score'] = 1
    
    df.loc[(df['YEAR'] == 2023) & (df['WEEK'] >= 40), 'score'] = 1
    df.loc[(df['YEAR'] == 2024) & (df['WEEK'] <= 20), 'score'] = 1

    return df


def load_prediction_file(fname):
    df = pd.read_csv(fname)
    df['date_predicted'] = pd.to_datetime(df['date_predicted'])
    
    required_cols = ['date_predicted', 'location_name',
                     'model', 'value', 'target_value',
                     'horizon']
    assert all([x in df.columns for x in required_cols])
    
    mmwr = load_mmwr_map()
    df = pd.merge(
        df, mmwr, left_on='date_predicted',
        right_on='Saturday'
    )
    return df


def load_imputed_target(date='2022-11-06'):
    truth = pd.read_csv(f'./data/imputed_sets/imputed_stitched_hosp_{date}.csv')
    truth['Saturday'] = pd.to_datetime(truth['date'])
    truth = truth.drop('date', axis=1)
    return truth
