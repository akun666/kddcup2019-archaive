import os
<<<<<<< HEAD

# os.system("apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 04EE7237B7D453EC")
# os.system("apt-get --assume-yes update")
# os.system("apt-get --assume-yes install swig libdpkg-perl")

os.system("pip3 install hyperopt")
os.system("pip3 install lightgbm")
os.system("pip3 install pandas==0.24.2")
os.system("pip3 install deap")
os.system("pip3 install eli5")
os.system("pip3 install sklearn")
os.system("pip3 install category_encoders")
os.system("pip3 install bayesian-optimization")
# os.system("pip3 install smac")
# os.system("pip3 install numbers")
# os.system("pip3 install psutil")
# os.system("pip3 install featuretools")
=======
>>>>>>> merge

os.system("pip3 install --default-timeout=1000 scikit-learn==0.21.2")
os.system("pip3 install --default-timeout=1000 hyperopt")
os.system("pip3 install --default-timeout=1000 lightgbm")
os.system("pip3 install -U --default-timeout=1000 pandas==0.24.2")
os.system("pip3 install --default-timeout=1000 deap")

import copy
import numpy as np
import pandas as pd

from CONSTANT import (MAIN_TABLE_NAME,
                      REDUCTION_SWITCH,
                      FEATURE_SELECTION_SWITCH,
                      DATA_BALANCE_SWITCH,
                      BAYESIAN_OPT,
                      ENSEMBLE,
                      ENSEMBLE_OBJ,
                      DATA_DOWNSAMPLING_SWITCH,
                      TIME_PREFIX,
                      MULTI_CAT_PREFIX,
                      DROP_OUTLIER,
                      NUMERICAL_PREFIX,
                      FEATURE_RATIO_1,
                      FEATURE_RATIO_2)
from merge import merge_table
from preprocess import (clean_df,
                        clean_tables,
                        feature_selection,
                        feature_engineer_rewrite,
                        drop_outlier,
                        test_data_feature_selection)
from util import Config, log, show_dataframe, timeit, TimeManager
from deap import base, creator
<<<<<<< HEAD
# import featuretools as ft
=======
import datetime, time
>>>>>>> merge

import gc
gc.enable()

# if BAYESIAN_OPT:
#     from bayesml import predict, train, validate
# else:
#     from automl import predict, train, validate
from automl import predict, train, validate


class Model:
    def __init__(self, info):
        info.pop("start_time")
        self.config = Config(info)
        self.tables = None
        if ENSEMBLE:
            # for NSGA-II selection
            if ENSEMBLE_OBJ == 3:
                creator.create("FitnessMin", base.Fitness, weights=(-1, -1, -1))
            else:
                creator.create("FitnessMin", base.Fitness, weights=(-1, -1))
            creator.create("Individual", dict, fitness=creator.FitnessMin)
        self.pca = None
        self.scaler = None
        self.selected_features_0 = None
        self.selected_features_1 = None

    @timeit
    def fit(self, Xs, y, time_remain):
        print('', flush=True)
        time_manager = TimeManager(self.config, time_remain)
        duration = 0
        # self.tables = copy.deepcopy(Xs)
        self.tables = Xs
        clean_tables(self.tables)
        duration += 2*time_manager.check("clean tables")

        if DROP_OUTLIER:
            # the percentage of outliers dropped is around 15% to 20%
            inlier_lable = drop_outlier(self.tables[MAIN_TABLE_NAME])
            self.tables[MAIN_TABLE_NAME] = self.tables[MAIN_TABLE_NAME][inlier_lable == 1].reset_index(drop=True)
            y = y[inlier_lable == 1].reset_index(drop=True)
            duration += time_manager.check("drop outlier")

        X = merge_table(self.tables, self.config)
        duration += 2*time_manager.check("merge table")

        clean_df(X)
        duration += 2*time_manager.check("clean data before learning")

        self.time_feature_list = [c for c in X if c.startswith(TIME_PREFIX)]
        self.mul_feature_list = [c for c in X if c.startswith(MULTI_CAT_PREFIX)]
        self.num_feature_list = [c for c in X if c.startswith(NUMERICAL_PREFIX)]

        print('', flush=True)

        if FEATURE_SELECTION_SWITCH:
            _, self.selected_features_0 = feature_selection(X.drop(columns=self.time_feature_list+self.mul_feature_list+self.num_feature_list)
                                                            , y, self.config, FEATURE_RATIO_1)
            time_manager.check("first feature selection")
            selected_features = list(self.selected_features_0) + self.time_feature_list + self.mul_feature_list + self.num_feature_list
        else:
            selected_features = self.time_feature_list + self.mul_feature_list + self.num_feature_list

        st = time.time()
        X = feature_engineer_rewrite(X.filter(selected_features), self.config, time_manager)
        duration += 2*(time.time() - st)
        time_manager.check("exit feature engineering")

        if FEATURE_SELECTION_SWITCH:
            X, self.selected_features_1 = feature_selection(X, y , self.config, FEATURE_RATIO_2)
            duration += time_manager.check("second feature selection")
        print('', flush=True)

        self.config["prediction_estimated"] = 1.57 * duration
        print(f"estimated prediction time: {self.config['prediction_estimated']}")
        train(X, y, self.config, time_manager)
        time_manager.check("model training")
        print('', flush=True)

    @timeit
    def predict(self, X_test, time_remain):

        time_manager = TimeManager(self.config, time_remain)
        print(f"prediction remaining time: {time_remain}")
        print('', flush=True)
        Xs = self.tables
        # main_table, len_X_train = Xs[MAIN_TABLE_NAME], len(Xs[MAIN_TABLE_NAME])
        # main_table = pd.concat([main_table, X_test], keys=['train', 'test'], sort=True)
        # time_manager.check("concat X_train and X_test")
        # main_table.index = main_table.index.map(lambda x: f"{x[0]}_{x[1]}")
        # Xs[MAIN_TABLE_NAME] = main_table
        Xs[MAIN_TABLE_NAME] = X_test
        clean_df(Xs[MAIN_TABLE_NAME])
        time_manager.check("clean main table")

        X = merge_table(Xs, self.config)
        time_manager.check("merge table")

        clean_df(X)
        time_manager.check("clean data before learning")
        print('', flush=True)

        if FEATURE_SELECTION_SWITCH:
            selected_features = list(self.selected_features_0) + self.time_feature_list + self.mul_feature_list + self.num_feature_list
        else:
            selected_features = self.time_feature_list + self.mul_feature_list + self.num_feature_list
        X = feature_engineer_rewrite(X.filter(selected_features), self.config, time_manager)
        time_manager.check("exit feature engineering")
        print('', flush=True)

        # X = X[X.index.str.startswith("test")]
        # X = X.iloc[len_X_train:, ]
        X.sort_index(inplace=True)
        time_manager.check("X sorting")
        if FEATURE_SELECTION_SWITCH:
            test_data_feature_selection(X, self.selected_features_1)
            X = X[self.selected_features_1]
            time_manager.check("test data feature selection")

        print('', flush=True)
        result = predict(X, self.config)
        time_manager.check("prediction")
        print('', flush=True)

        return pd.Series(result)
