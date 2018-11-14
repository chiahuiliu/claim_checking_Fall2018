#!/usr/bin/env python
import sys
import dill as pickle
import numpy as np
from itertools import chain
from collections import Counter
from sklearn.model_selection import StratifiedKFold, GroupKFold
import xgboost as xgb
from collections import Counter
from CountFeatureGenerator import *
from TfidfFeatureGenerator import *
from SvdFeatureGenerator import *
from Word2VecFeatureGenerator import *
from SentimentFeatureGenerator import *
from score import *
'''
    10-fold cv on 80% of the data (training_ids.txt)
    splitting based on BodyID
    test on remaining 20% (hold_out_ids.txt)
'''
'''
original parameters
params_xgb = {

    'max_depth': 6,
    'colsample_bytree': 0.6,
    'subsample': 1.0,
    'eta': 0.1,
    'silent': 1,
    #'objective': 'multi:softmax',
    'objective': 'multi:softprob',
    'eval_metric':'mlogloss',
    'num_class': 4
}
'''
params_xgb = {

    # change max_depth
    'max_depth': 6,
    'colsample_bytree': 0.6,
    'subsample': 1.0,
    'eta': 0.1,
    'silent': 1,
    #'objective': 'multi:softmax',
    'objective': 'multi:softprob',
    'eval_metric':'mlogloss',
    'num_class': 4
}

num_round = 1000

def build_data(article_stance=True):

    data = pd.read_csv('./data/merged_data_tain.csv', encoding='utf-8')
    used_column = ['claimHeadline', 'articleHeadline', 'claimTruthiness', 'articleStance', 'articleId']

    data = data[used_column].dropna()
    data['Headline'] = data['claimHeadline'].apply(lambda x: x[8:])
    data['articleBody'] = data['articleHeadline']
    data['Body ID'] = data['articleId']

    if article_stance:
        targets = ['observing', 'for', 'against', 'ignoring']
        targets_dict = dict(zip(targets, range(len(targets))))
        data['target'] = list(map(lambda x: targets_dict[x], data['articleStance']))
    else:
        targets = ['unknown', 'false', 'true']
        targets_dict = dict(zip(targets, range(len(targets))))
        data['target'] = list(map(lambda x: targets_dict[x], data['claimTruthiness']))

    train = data.sample(frac=0.6, random_state=2018)
    test = data.loc[~data.index.isin(train.index)]

    data_y = train['target'].values

    # read features
    generators = [
                  CountFeatureGenerator(),
                  TfidfFeatureGenerator(),
                  SvdFeatureGenerator(),
                  Word2VecFeatureGenerator(),
                  SentimentFeatureGenerator()
                  #AlignmentFeatureGenerator()
                 ]
    features = [f for g in generators for f in g.read('train')]

    data_x = (np.hstack(features))
    print(data_x[0,:])
    print('data_x.shape')
    print(data_x.shape)
    print('data_y.shape')
    print(data_y.shape)
    print('body_ids.shape')
    print(data['Body ID'].values.shape)


    return data_x, data_y, data['Body ID'].values, test[['target', 'Headline', 'Body ID']]

def build_test_data(article_stance=True):

    # create target variable
    # replace file names when test data is ready
    data = pd.read_csv('./data/merged_data_tain.csv', encoding='utf-8')
    used_column = ['claimHeadline', 'articleHeadline', 'claimTruthiness', 'articleStance', 'articleId']

    data = data[used_column].dropna()
    data['Headline'] = data['claimHeadline'].apply(lambda x: x[8:])
    data['articleBody'] = data['articleHeadline']
    data['Body ID'] = data['articleId']

    if article_stance:
        targets = ['observing', 'for', 'against', 'ignoring']
        targets_dict = dict(zip(targets, range(len(targets))))
        data['target'] = list(map(lambda x: targets_dict[x], data['articleStance']))
    else:
        targets = ['unknown', 'false', 'true']
        targets_dict = dict(zip(targets, range(len(targets))))
        data['target'] = list(map(lambda x: targets_dict[x], data['claimTruthiness']))

    train = data.sample(frac=0.6, random_state=2018)
    test = data.loc[~data.index.isin(train.index)]

    '''
    body = pd.read_csv("test_bodies.csv")
    stances = pd.read_csv("test_stances_unlabeled.csv") # needs to contain pair id
    data = pd.merge(stances, body, how='left', on='Body ID')
    '''
    # read features
    generators = [
                  CountFeatureGenerator(),
                  TfidfFeatureGenerator(),
                  SvdFeatureGenerator(),
                  Word2VecFeatureGenerator(),
                  SentimentFeatureGenerator()
                 ]

    features = [f for g in generators for f in g.read("test")]
    print(len(features))

    data_x = np.hstack(features)
    print(data_x[0,:])
    print('test data_x.shape')
    print(data_x.shape)
    print('test body_ids.shape')
    print(test['Body ID'].values.shape)
                   # pair id
    return data_x, test['Body ID'].values, test['target']

def train():
    article_stance = True
    data_x, data_y, body_ids, target_stance = build_data(article_stance=article_stance)
    print(data_x, data_y, body_ids, target_stance)
    # read test data
    test_x, body_ids_test, true_y = build_test_data(article_stance=article_stance)

    n_iters = 50

    #dtrain = xgb.DMatrix(data_x, label=data_y, weight=w)
    dtrain = xgb.DMatrix(data_x, label=data_y)
    dtest = xgb.DMatrix(test_x)
    watchlist = [(dtrain, 'train')]
    bst = xgb.train(params_xgb,
                    dtrain,
                    n_iters,
                    watchlist,
                    verbose_eval=10)

    pred_prob_y = bst.predict(dtest).reshape(test_x.shape[0], 4) # predicted probabilities
    pred_y = np.argmax(pred_prob_y, axis=1)
    print('pred_y.shape:')
    print(pred_y.shape)
    predicted = [LABELS[int(a)] for a in pred_y]
    #print predicted

    # add encoding
    df_test = pd.DataFrame()
    df_test['pred_y'] = pred_y
    df_test['true_y'] = true_y

    if article_stance:

        df_test['pred_y'] = df_test['pred_y'].replace([0,1,2,3], ['observing', 'for', 'against', 'ignoring'])
        df_test['true_y'] = df_test['true_y'].replace([0,1,2,3], ['observing', 'for', 'against', 'ignoring'])
        df_test = df_test.dropna()

        print(df_test['pred_y'].value_counts())
        print(df_test['true_y'].value_counts())

        print(score.report_score(df_test['true_y'], df_test['pred_y'], article_stance=article_stance))
        print("F1 Score")
        print("F1 Micro: " + str(f1_score(true_y, pred_y, average='micro')))
        LABELS = ['observing', 'for', 'against', 'ignoring']
        predicted = [LABELS[int(a)] for a in pred_y]
    else:

        df_test['pred_y'] = df_test['pred_y'].replace([0,1,2], ['unknown','false', 'true'])
        df_test['true_y'] = df_test['true_y'].replace([0,1,2], ['unknown','false', 'true'])
        df_test = df_test.dropna()

        print(df_test['pred_y'].value_counts())
        print(df_test['true_y'].value_counts())

        print(score.report_score(df_test['true_y'], df_test['pred_y'], article_stance=article_stance))
        print("F1 Score")
        print("F1 Micro: " + str(f1_score(true_y, pred_y, average='micro')))
        LABELS = ['unknown', 'false', 'true']
        predicted = [LABELS[int(a)] for a in pred_y]


    # save (id, predicted and probabilities) to csv, for model averaging
    #stances = pd.read_csv("test_stances_unlabeled_processed.csv") # same row order as predicted
    stances = target_stance

    df_output = pd.DataFrame()
    df_output['Headline'] = stances['Headline']
    df_output['Body ID'] = stances['Body ID']

    df_output['Stance'] = predicted

    #df_output.to_csv('submission.csv', index=False)
    df_output.to_csv('tree_pred_prob_cor2.csv', index=False)
    df_output[['Headline','Body ID','Stance']].to_csv('tree_pred_cor2.csv', index=False)

    print(df_output)
    print(Counter((df_output['Stance'])))

if __name__ == '__main__':

    train()

 #   Copyright 2017 Cisco Systems, Inc.
 #
 #   Licensed under the Apache License, Version 2.0 (the "License");
 #   you may not use this file except in compliance with the License.
 #   You may obtain a copy of the License at
 #
 #     http://www.apache.org/licenses/LICENSE-2.0
 #
 #   Unless required by applicable law or agreed to in writing, software
 #   distributed under the License is distributed on an "AS IS" BASIS,
 #   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 #   See the License for the specific language governing permissions and
 #   limitations under the License.
