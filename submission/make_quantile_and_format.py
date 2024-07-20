from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy import stats
from scipy import optimize

from constants import LOCATIONS
from loader import load_prediction_file
from quantile import SeasonalNormalQuantiles
from flu_writer import FlusightForecastWriter

from mapping import load_mapping_info

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--date', '-d',
                    help='Reference date of submission (Saturday): YYYY-MM-DD')
parser.add_argument('--name', '-n', default='Nsemble')
parser.add_argument('--pred', '-p', help='Prediction file')
parser.add_argument('--trend', '-m', help='Trend category file')
parser.add_argument('--errors', '-e',
                    help='Historical predictions to estimate quantiles')
parser.add_argument('--backup',
                    help='Pred file to fill missing locations')
parser.add_argument('--quantile', '-q', default='normal', help='Quantile method')
args = parser.parse_args()

LAST_CDC_DATE = (pd.to_datetime(args.date) - pd.Timedelta(days=14)).strftime('%Y-%m-%d')


def load_fips_lookup():
    df = pd.read_csv('./submission/locations.csv', dtype={'location': str})
    lookup = dict(zip(df['location_name'], df['location']))
    return lookup


def make_quantile_estimators(train_df):

    estimators = {}
    for loc in set(LOCATIONS):
        for h in [1, 2, 3, 4, 5]:
            # print(loc, h)
            df = train_df[(train_df.location_name == loc) & (train_df.horizon == h)].copy()

            if df.shape[0] == 0:
                continue
            # print(df.shape)
            def normality_score(x):
                # adding 1 pseudo-count to all cells improves normality
                X = np.clip(df['value'].values + 1, 0, None)
                Y = np.clip(df['target_value'].values + 1, 0, None)
                resid = np.power(X, x) - np.power(Y, x)
                return -stats.shapiro(resid).pvalue

            # raised lower bound to 0.2 to avoid huge intervals on power distributions
            result = optimize.minimize_scalar(normality_score, bounds=[0.2, 0.99], method='bounded')            
            quant = SeasonalNormalQuantiles(transform='power', power=result.x)
            quant.fit(df)

            estimators[(loc, h)] = quant

    return estimators


if __name__ == '__main__':
    SEASON = 'Fall'
    
    fips = load_fips_lookup()
    
    # compute quantiles
    error_df = load_prediction_file(args.errors)
    error_df.loc[error_df['value'] < 0, 'value'] = 0.0
    error_df = error_df[~error_df.target_value.isna()]
    estimators = make_quantile_estimators(error_df)

    # load prediction file
    pred_df = load_prediction_file(args.pred)
    
    # start writing predictions to file
    writer = FlusightForecastWriter(forecast_date=args.date, model_name=args.name)

    # this section computes quantile estimates
    for row in pred_df.iterrows():
        info = row[1]
        try:
            distr = estimators[(info['location_name'], info['horizon'])]
        except KeyError:
            print('Missing quantile estimator: ', info['location_name'], info['horizon'])
        
        pred_date_str = info['date_predicted'].strftime('%Y-%m-%d')
            
        if not writer.is_valid_time(pred_date_str, info['horizon'] - 2):
            continue

        quant_est = distr.quantiles(
            writer.quantiles, pt_estimate=info['value'], season=SEASON)
        
        for i, q in enumerate(writer.quantiles):
            writer.add_quantile(
                info['horizon'] - 2,
                info['date_predicted'],
                fips[info['location_name']],
                q,
                quant_est[i])


    # this section computes rate mapping estimates using the quantile probabilities
    if args.trend is not None: 
        trend_df = load_prediction_file(args.trend)
    else:
        # compute mapping from regression task predictions
        pop_dict, truth, rate_thresh_dict = load_mapping_info(LAST_CDC_DATE)        
        
        for row in pred_df.iterrows():
            info = row[1]
            try:
                distr = estimators[(info['location_name'], info['horizon'])]
            except KeyError:
                print('Missing quantile estimator: ', info['location_name'], info['horizon'])

            loc, horizon, pred = info['location_name'], info['horizon'], info['value']

            pred_date_str = info['date_predicted'].strftime('%Y-%m-%d')
            if not writer.is_valid_time(pred_date_str, horizon - 2):
                continue

            truth_row = truth[truth['location_name'] == loc]
            assert truth_row.shape[0] == 1
            
            last_obs_count = truth_row['value'].iloc[0]
            last_obs_rate = truth_row['weekly_rate'].iloc[0]
            
            pop_rate = pop_dict[loc] / 100000
            
            # either stable rate or 10 counts, whichever is greater, counts as stable
            stable_delta = rate_thresh_dict[horizon - 2]['Stable'] * pop_rate
            stable_delta = max(stable_delta, 10)
            
            increase_delta = rate_thresh_dict[horizon - 2]['Increase'] * pop_rate
            decrease_delta = rate_thresh_dict[horizon - 2]['Decrease'] * pop_rate

            stable_ucp = distr.cdf(last_obs_count + stable_delta, pred, season=SEASON)
            stable_lcp = distr.cdf(last_obs_count - stable_delta, pred, season=SEASON)
            stable_prob = stable_ucp - stable_lcp
            
            inc_cp = distr.cdf(last_obs_count + increase_delta, pred, season=SEASON)
            increase_prob = inc_cp - stable_ucp
            large_inc_prob = 1.0 - inc_cp

            # decrease_delta is already negative so add the delta
            dec_cp = distr.cdf(last_obs_count + decrease_delta, pred, season=SEASON)
            large_dec_prob = dec_cp
            decrease_prob = stable_lcp - large_dec_prob
            
            writer.add_pmf(
                    info['horizon'] - 2,
                    info['date_predicted'],
                    fips[info['location_name']],
                    'stable',
                    stable_prob)

            writer.add_pmf(
                    info['horizon'] - 2,
                    info['date_predicted'],
                    fips[info['location_name']],
                    'increase',
                    increase_prob)

            writer.add_pmf(
                    info['horizon'] - 2,
                    info['date_predicted'],
                    fips[info['location_name']],
                    'large_increase',
                    large_inc_prob)

            writer.add_pmf(
                    info['horizon'] - 2,
                    info['date_predicted'],
                    fips[info['location_name']],
                    'decrease',
                    decrease_prob)

            writer.add_pmf(
                    info['horizon'] - 2,
                    info['date_predicted'],
                    fips[info['location_name']],
                    'large_decrease',
                    large_dec_prob)

    df = writer.write()
