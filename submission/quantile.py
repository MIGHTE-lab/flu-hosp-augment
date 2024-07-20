''' Code for generating probabilistic intervals and quantiles for submission file
'''
import scipy.stats
import numpy as np
import pandas as pd


def log_transform():
    return lambda x: np.log(x + 1)

def inv_log_transform():
    return lambda x: np.exp(x) - 1

def power_transform(a):
    def fn(x):
        x = np.clip(x + 1, 0, None)
        return np.power(x, a)
    return fn

def inv_power_transform(a):
    return lambda x: np.power(x, 1/a) - 1

def no_transform():
    return lambda x: x


class QuantileEstimator:
    def fit(self, df):
        raise NotImplementedError
    
    def quantiles(self, qs, pt_estimate=0.0):
        raise NotImplementedError


class SeasonalNormalQuantiles(QuantileEstimator):
    def __init__(self, transform='none', power=2):
        if transform == 'log':
            self.transform = log_transform()
            self.inv_transform = inv_log_transform()
        elif transform == 'power':
            self.transform = power_transform(power)
            self.inv_transform = inv_power_transform(power)
        else:
            self.transform = no_transform()
            self.inv_transform = no_transform()

        self.estimators = {}
            
    def fit(self, df):
        df = df[~df['target_value'].isna()].copy()
        
        # from pdb import set_trace; set_trace()
        for season in ['Fall', 'Winter', 'Spring']:
            sdf = df[df[season] == 1]
            pred = self.transform(sdf['value'].values)
            target = self.transform(sdf['target_value'].values)
            resid = target - pred
            sd = np.std(resid)
            self.estimators[season] = sd
         
        pred = self.transform(df['value'].values)
        target = self.transform(df['target_value'].values)
        resid = pred - target
        sd = np.std(resid)
        self.estimators['Overall'] = sd

    def quantiles(self, qs, pt_estimate=0.0, season='Overall'):
        pt_est_tr = self.transform(pt_estimate)
        dist_sd = self.estimators[season]
        est_tr = scipy.stats.norm.ppf(qs, loc=pt_est_tr, scale=dist_sd)
        return self.inv_transform(est_tr)
    
    def cdf(self, val, pt_estimate=0.0, season='Overall'):
        pt_est_tr = self.transform(pt_estimate)
        val_tr = self.transform(val)
        dist_sd = self.estimators[season]
        cprob = scipy.stats.norm.cdf(val_tr, loc=pt_est_tr, scale=dist_sd)
        return cprob
