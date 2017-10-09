
'''
@author: Sebastian Lapuschkin
@maintainer: Sebastian Lapuschkin
@contact: sebastian.lapuschkin@hhi.fraunhofer.de, wojciech.samek@hhi.fraunhofer.de
@date: 08.09.2017
@version: 1.0
@copyright: Copyright (c)  2015-2017, Sebastian Lapuschkin, Alexander Binder, Gregoire Montavon, Klaus-Robert Mueller, Wojciech Samek
@license : BSD-2-Clause
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                '''


import datetime
import os
import numpy as np # the de facto numerics package for python
import scipy.io as scio # scientific python package, which supports mat-file IO within python
import helpers
import training
import eval_score_logs
import sys

SKIPTHISMANY=0
ROOTFOLDER='.'

for param in sys.argv:
    if not '=' in param:
        continue
    else:
        k,v = param.split('=')
        if 'skip' in k:
            print 'setting skip param to', v
            SKIPTHISMANY = int(v)
        elif 'root' in k:
            print 'setting root folder param to', v
            ROOTFOLDER = v


################################
#           "Main"
################################

gaitdata = scio.loadmat('{}/Gait_GRF_JA_Label.mat'.format(ROOTFOLDER)) #load matlab data as dictionary using scipy

# Bodenreaktionskraft mit zwei verschiedenen Datennormalisierungen
X_GRF_AV = gaitdata['Feature_GRF_AV']                       # 1142 x 101 x 6
Label_GRF_AV = gaitdata['Feature_GRF_AV_Label']             # 1 x 1 x 6 channel label

X_GRF_JV = gaitdata['Feature_GRF_JV']                       # 1142 x 101 x 6
Label_GRF_JV = gaitdata['Feature_GRF_JV_Label']             # 1 x 1 x 6 channel label

# Gelenkwinkel in drei Drehachsen fuer den gesamten Koerper
X_JA_Full = gaitdata['Feature_JA_Full']                     # 1142 x 101 x 33
Label_JA_Full = gaitdata['Feature_JA_Full_Label']           # 1 x 1 x 33 channel label

# ... fuer den Unterkoerper
X_JA_Lower = gaitdata['Feature_JA_Lower']                   # 1142 x 101 x 18
Label_JA_Lower = gaitdata['Feature_JA_Lower_Label']         # 1 x 1 x 18 channel label

# Gelenkwinkel lediglich in der Hauptdrehachse fuer den gesamten Koerper
X_JA_X_Full = gaitdata['Feature_JA_X_Full']                 # 1142 x 101 x 10
Label_JA_X_Full = gaitdata['Feature_JA_X_Full_Label']       # 1 x 1 x 10 channel label

# ... und den Unterkoerper
X_JA_X_Lower = gaitdata['Feature_JA_X_Lower']               # 1142 x 101 x 6
Label_JA_X_Lower = gaitdata['Feature_JA_X_Lower_Label']     # 1 x 1 x 10 channel label

#Target subject labels und gender labels
Y_Subject = gaitdata['Target_SubjectID']                    # 1142 x 57, binary labels
Y_Gender = gaitdata['Target_Gender']                        # 1142 x 1 , binary labels
#-> create uniform label structure for gender
Y_Gender = np.repeat(Y_Gender, 2, axis=1)
Y_Gender[:, 1] = 1-Y_Gender[:, 0]                           # 1142 x 2, binary labels  (562 vs 580)

#split data for experiments.
#Subject identification: create 10 splits with the samples of each subject spread over all splits.
#Gender identification: create 10 splits with the genders split evenly over all partitions, but pool
#the samples per subject in only one bin: avoid prediction based on personal characteristics
#use a random seed to make partitioning deterministic
RANDOMSEED = 1234
SubjectIndexSplits, GenderIndexSplits, Permutation = helpers.create_index_splits(Y_Subject, Y_Gender, splits=10, seed=RANDOMSEED)

#apply the permutation to the given data for the inputs and labels to match the splits again
X_GRF_AV = X_GRF_AV[Permutation, ...]
X_GRF_JV = X_GRF_JV[Permutation, ...]
X_JA_Full = X_JA_Full[Permutation, ...]
X_JA_Lower = X_JA_Lower[Permutation, ...]
X_JA_X_Full = X_JA_X_Full[Permutation, ...]
X_JA_X_Lower = X_JA_X_Lower[Permutation, ...]
Y_Gender = Y_Gender[Permutation, ...]
Y_Subject = Y_Subject[Permutation, ...]

#create dictionaries for easier batch access for training and testing.
X = {'GRF_AV': X_GRF_AV,
     'GRF_JV': X_GRF_JV,
     'JA_Full': X_JA_Full,
     'JA_Lower': X_JA_Lower,
     'JA_X_Full': X_JA_X_Full,
     'JA_X_Lower': X_JA_X_Lower}

Y = {'Gender': Y_Gender,
     'Subject': Y_Subject}

L = {'GRF_AV': Label_GRF_AV,
     'GRF_JV': Label_GRF_JV,
     'JA_Full': Label_JA_Full,
     'JA_Lower': Label_JA_Lower,
     'JA_X_Full': Label_JA_X_Full,
     'JA_X_Lower': Label_JA_X_Lower}

S = {'Gender':GenderIndexSplits,
     'Subject':SubjectIndexSplits}

# skip to just do nothing and leave the results as is
# load to load the model and reevaluate, recompute heatmaps
# retrain to overwrite the old model and results
DOTHISIFMODELEXISTS = 'skip'


"""
DAYFOLDER = './BASELINE-LINEAR-S{}'.format(RANDOMSEED)
training.run_linear(X, Y, L, S, DAYFOLDER, ifModelExists=DOTHISIFMODELEXISTS)
eval_score_logs.run(DAYFOLDER)

#prepare experiment configuration for this (not necessarily the current, e.g. for result completion) day
DAYFOLDER = './2017-09-14'.format(RANDOMSEED)
#run some experiments
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=64, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=128, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=256, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=512, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=1024, ifModelExists=DOTHISIFMODELEXISTS)
eval_score_logs.run(DAYFOLDER)


#create folder for today's experiments.
DAYFOLDER = './2017-09-15'.format(RANDOMSEED)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=64, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=128,ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=256, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=512, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=1024,ifModelExists=DOTHISIFMODELEXISTS)

training.run_pca(X,Y,S)
"""


"""
#some runs with another random seed for sanity checking.
DAYFOLDER = './' + str(datetime.datetime.now()).split()[0] + '-S{}'.format(RANDOMSEED)
training.run_linear(X, Y, L, S, DAYFOLDER, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=64, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=128, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=256, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=512, ifModelExists=DOTHISIFMODELEXISTS)
training.run_2layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=1024, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=64, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=128, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=256, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=512, ifModelExists=DOTHISIFMODELEXISTS)
training.run_3layer_fcnn(X, Y, L, S, DAYFOLDER, n_hidden=1024, ifModelExists=DOTHISIFMODELEXISTS)
"""


#DAYFOLDER = './' + str(datetime.datetime.now()).split()[0] + '-S{}'.format(RANDOMSEED)
DAYFOLDER = '{}/2017-10-05-S1234'.format(ROOTFOLDER)
SKIPTHISMANY = training.run_cnn_A(X, Y, L, S, DAYFOLDER, ifModelExists=DOTHISIFMODELEXISTS, SKIPTHISMANY=SKIPTHISMANY) # A - mode uses ALL features in each convolution and slides over time. filters are square in shape
print SKIPTHISMANY
if SKIPTHISMANY >= 0:
    training.run_cnn_C3(X, Y, L, S, DAYFOLDER, ifModelExists=DOTHISIFMODELEXISTS, SKIPTHISMANY=SKIPTHISMANY) # C3 - mode. classical 1-stride convolutions in either direction with filter size 3 in time and channel direction
#TODO: Classical C6
#TODO: Stride 3 C3 for the full angle data sets to compare to the C3 classical

training.run_cnn_C6(X, Y, L, S, DAYFOLDER, ifModelExists=DOTHISIFMODELEXISTS, SKIPTHISMANY=SKIPTHISMANY)

eval_score_logs.run(DAYFOLDER)
