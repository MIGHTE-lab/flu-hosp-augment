import numpy as np
import pandas as pd


rate_thresh_dict = {-1: {
      'Stable': 1,
      'Increase': 2,
      'Large increase': 2,
      'Decrease': -2,
      'Large decrease': -2
    },
 0: {
     'Stable': 1,
     'Increase': 3,
     'Large increase': 3,
     'Decrease': -3,
     'Large decrease': -3,
    },
 1: {
     'Stable': 2,
     'Increase': 4,
     'Large increase': 4,
     'Decrease': -4,
     'Large decrease': -4,
    },
 2: {
     'Stable': 2.5,
     'Increase': 5,
     'Large increase': 5,
     'Decrease': -5,
     'Large decrease': -5,
    },
 3: {
     'Stable': 2.5,
     'Increase': 5,
     'Large increase': 5,
     'Decrease': -5,
     'Large decrease': -5,
    }
}


def load_mapping_info(last_cdc_date):
    pop_info = pd.read_csv(
        './submission/locations.csv',
        dtype={'location': str})
    
    pop_dict = dict(zip(pop_info['location_name'], pop_info['population']))
    
    truth = pd.read_csv(
        f'./data/ground_truth/target-hospital-admissions_{last_cdc_date}.csv',
        dtype={'location': str})
    truth = truth[truth['date'] == last_cdc_date].copy()
    return pop_dict, truth, rate_thresh_dict
