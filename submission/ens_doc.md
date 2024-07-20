# Additional documentation (2023-24)

The goal of these notes are to clearly document for future reference and development:
- the dates and time windows of files to consider for the flu contest prediction
- how to interpret and match datetimes from data files to the relevant CDC horizon

## Datetime definitions

The prediction week *t* is the Saturday following the submission Wednesday. For clarity, we call this Saturday "prediction" or "reference" day. Originally official CDC data would be available for the week ending two weeks before (*t - 2wk*). Thus the horizons are:
- Horizon -1: *t - 1wk*
- Horizon 0: *t*
- Horizon 1: *t + 1wk*
- Horizon 2: *t + 2wk*
- Horizon 3: *t + 3wk*

These horizons are CDC format. In our prediction files these are labeled horizons 1-5. The model prediction files are labeled with the *last available CDC target*. So the file for week *t* is labeled as *t - 2wk*.

**However**, for this season the CDC is able to release ground truth for horizon -1. So for prediction week *t*, we could submit horizon -1 using the CDC ground truth. But this wouldn't be interesting modeling, so we keep using prediction file *t - 2wk* for horizon -1. Then we re-run predictions using the new data, giving prediction files *t - 1wk*. We take horizons 1, 2, 3, 4 from these, which would be horizons 2, 3, 4, 5 from file *t - 2wk*.

| CDC horizon | pred file | pred horizon | original pred horizon (file t-2wk) | pred file weeks ago |
|-------------|-----------|--------------|------------------------------------|---------------------|
| -1          | t-2wk     | 1            | 1                                  | 1                   |
| 0           | t-1wk     | 1            | 2                                  | 1                   |
| 1           | t-1wk     | 2            | 3                                  | 2                   |
| 2           | t-1wk     | 3            | 4                                  | 3                   |
| 3           | t-1wk     | 4            | 5                                  | 4                   |


"pred file" and "pred horizon" are prospective -- when making submission we use those files and horizons. "pred file weeks ago" is retrospective -- when finding the prediction for target in week *t* we look at the prediction from file in that offset week. 

The prediction file is processed into a submission file (which adds uncertainty intervals, formatting, etc), and this gets labeled as time *t*.

### Relevance for ensembling and backtesting
We pass in the prediction week as a parameter to the backtester. If horizon is 1 the file from *t - 2wk* is loaded and pred horizon -1 taken. Otherwise the file from *t - 1wk* is loaded.

The complication with horizons -1 and 0 utilizing the updated data means that the horizon -1 predictions are used twice prospectively: a two-week-ahead prediction for horizon -1 and a one-week-ahead prediction the following week for horizon 0. This means that retrospectively for a given target week, the horizon -1 and horizon 0 predictions are the same source.
