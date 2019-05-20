import os

os.system("pip3 install hyperopt")
os.system("pip3 install lightgbm")
os.system("pip3 install pandas==0.24.2")
os.system("pip3 install deap")

import copy
import numpy as np
import pandas as pd

from automl import predict, train, validate
from CONSTANT import MAIN_TABLE_NAME, REDUCTION_SWITCH
from merge import merge_table
from preprocess import clean_df, clean_tables, feature_engineer, data_reduction_train, data_reduction_test
from util import Config, log, show_dataframe, timeit
from deap import base, creator


class Model:
    def __init__(self, info):
        self.config = Config(info)
        self.tables = None
        # for NSGA-II selection
        creator.create("FitnessMin", base.Fitness, weights=(-1, -1))
        creator.create("Individual", dict, fitness=creator.FitnessMin)
        self.pca = None
        self.scaler = None

    @timeit
    def fit(self, Xs, y, time_ramain):
        self.tables = copy.deepcopy(Xs)

        clean_tables(Xs)
        X = merge_table(Xs, self.config)
        clean_df(X)
        feature_engineer(X, self.config)
        if REDUCTION_SWITCH:
            X, self.scaler, self.pca = data_reduction_train(X)
        train(X, y, self.config)

    @timeit
    def predict(self, X_test, time_remain):

        Xs = self.tables
        main_table = Xs[MAIN_TABLE_NAME]
        main_table = pd.concat([main_table, X_test], keys=['train', 'test'])
        main_table.index = main_table.index.map(lambda x: f"{x[0]}_{x[1]}")
        Xs[MAIN_TABLE_NAME] = main_table

        clean_tables(Xs)
        X = merge_table(Xs, self.config)
        clean_df(X)
        feature_engineer(X, self.config)
        X = X[X.index.str.startswith("test")]
        X.index = X.index.map(lambda x: int(x.split('_')[1]))
        X.sort_index(inplace=True)
        if REDUCTION_SWITCH:
            X = data_reduction_test(X, self.scaler, self.pca)
        result = predict(X, self.config)

        return pd.Series(result)