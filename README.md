# flu-hosp-augment

This repository contains supporting code for the submitted manuscript *A prospective real-time transfer learning approach to estimate Influenza hospitalizations with limited data*, with preprint [here](https://www.medrxiv.org/content/10.1101/2024.07.17.24310565v1).

## Modeling scripts

In `./scripts`, we provide scripts demonstrating how we implemented all the models used (e.g. VAR, ARIMA, LGBM), as well as how we performed the transfer learning stage necessary to use ILI to augment hospitalization data (i.e. `stitch.Rmd`). These are the main files of interest in terms of the paper.

For space reasons we include representative examples of the data used. The full data can be readily obtained from the CDC's [FluView portal](https://www.cdc.gov/flu/weekly/fluviewinteractive.htm). We include some demonstrative CSV files to indicate how the intermediate steps in our pipeline look.

In practice, this code was adapted to run weekly to append the CDC new week's data release, with new prediction files generated into the `./predictions` folder.

## CDC contest submission

A simple version of our CDC contest codebase and tooling are provided in `./submission`. Some of the stages go beyond the scope of our paper so we briefly document them. Essentially, in this stage of our method, we use our code to:
- pre-process prediction files to match revised CDC horizon definitions
- ensemble prediction files
- develop confidence intervals for probabilistic prediction
- post-process and write the final submission file
