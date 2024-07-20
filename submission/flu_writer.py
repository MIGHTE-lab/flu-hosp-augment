''' Implementation of our Python API for generating CDC submission file
'''
import pandas as pd
import numpy as np


class FlusightForecastWriter:
    def __init__(self, forecast_date, team_name='MIGHTE', model_name='Nsemble'):
        self.forecast_date = forecast_date
        self.team_name = team_name
        self.model_name = model_name

        wk1 = pd.to_datetime(forecast_date) - pd.Timedelta(days=7)
        wk2 = pd.to_datetime(forecast_date)
        wk3 = wk2 + pd.Timedelta(days=7)
        wk4 = wk2 + pd.Timedelta(days=14)
        wk5 = wk2 + pd.Timedelta(days=21)
        wk1 = wk1.strftime('%Y-%m-%d')
        wk2 = wk2.strftime('%Y-%m-%d')
        wk3 = wk3.strftime('%Y-%m-%d')
        wk4 = wk4.strftime('%Y-%m-%d')
        wk5 = wk5.strftime('%Y-%m-%d')
        
        self.valid_date_horizons = (
            (wk1, -1), (wk2, 0), (wk3, 1), (wk4, 2), (wk5, 3)
        )
        
        self.quantiles = np.append(
            np.append([0.01,0.025], np.arange(0.05,0.95+0.05,0.050)),
            [0.975,0.99])
        
        self.categories = ['large_increase', 'increase', 'stable',
                           'decrease', 'large_decrease']
        
        self.entries = {
            'reference_date': [],
            'target': [],
            'horizon': [],
            'target_end_date': [],
            'location': [],
            'output_type': [],
            'output_type_id': [],
            'value': []
        }
    
    def is_valid_time(self, target_end_date, horizon):
        return (target_end_date, horizon) in self.valid_date_horizons

    def _validator(self, target, horizon,
                  target_end_date, location,
                  output_type, output_type_id):
        assert target in ('wk inc flu hosp', 'wk flu hosp rate change')
        assert horizon in (-1, 0, 1, 2, 3)
        assert output_type in ('quantile', 'pmf')
        
        if target == 'wk inc flu hosp':
            assert output_type == 'quantile'
        if target == 'wk flu hosp rate change':
            assert output_type == 'pmf'
        
        if output_type == 'quantile':
            if output_type_id is None:
                raise ValueError('float quantile must be specified')
            if float(output_type_id) not in self.quantiles:
                raise ValueError(f'quantile must be among {self.quantiles}')
        if output_type == 'pmf':
            if output_type_id is None:
                raise ValueError('rate category must be specified')
            if output_type_id not in self.categories:
                raise ValueError(f'rate category must be among {self.categories}')
                
        # ensure target dates and horizons are specified correctly
        if (target_end_date, horizon) in self.valid_date_horizons:
            valid_entry = True
        else:
            valid_entry = False
        return valid_entry
    
    def add_quantile(self, horizon, target_end_date, location, quantile, value):
        if not isinstance(target_end_date, str):
            target_end_date = target_end_date.strftime('%Y-%m-%d')
        if isinstance(horizon, str):
            horizon = int(horizon)
        
        target = 'wk inc flu hosp'
        output_type = 'quantile'
        proceed = self._validator(target, horizon,
                                  target_end_date, location,
                                  output_type, quantile)
        
        # format quantile as str
        quantile = str(np.round(quantile, 3))

        if proceed:
            if np.isnan(value) or value < 0:
                print('NaN value detected in')
                print(horizon, target_end_date, location, quantile)
                value = 0.0

            self.entries['reference_date'].append(self.forecast_date)
            self.entries['target'].append(target)
            self.entries['horizon'].append(horizon)
            self.entries['target_end_date'].append(target_end_date)
            self.entries['location'].append(location)
            self.entries['output_type'].append(output_type)
            self.entries['output_type_id'].append(quantile)
            self.entries['value'].append(value)

    def add_pmf(self, horizon, target_end_date, location, category, value):
        if not isinstance(target_end_date, str):
            target_end_date = target_end_date.strftime('%Y-%m-%d')
        if isinstance(horizon, str):
            horizon = int(horizon)

        target = 'wk flu hosp rate change'
        output_type = 'pmf'
        proceed = self._validator(target, horizon,
                                  target_end_date, location,
                                  output_type, category)

        if proceed:
            if np.isnan(value) or value < 0:
                print('NaN value detected in')
                print(horizon, target_end_date, location, category)
                value = 0.0

            self.entries['reference_date'].append(self.forecast_date)
            self.entries['target'].append(target)
            self.entries['horizon'].append(horizon)
            self.entries['target_end_date'].append(target_end_date)
            self.entries['location'].append(location)
            self.entries['output_type'].append(output_type)
            self.entries['output_type_id'].append(category)
            self.entries['value'].append(value)

    def write(self, save_dir='./final'):
        out_file = f'{self.forecast_date}-{self.team_name}-{self.model_name}.csv'

        df = pd.DataFrame(self.entries)
        df = df.sort_values(['target', 'location', 'output_type', 'horizon', 'output_type_id'])
        df.to_csv(f'{save_dir}/{out_file}', index=False)
        return df
