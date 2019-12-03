#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 13:41:12 2019

@author: chayanit
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, cross_val_predict
from sklearn import linear_model, metrics
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score

data = pd.read_csv('ohlcv_with_future.csv')

col = ['trend','RSI','close','Fast_Line','Slow_Line_9','close_c_1min','close_1min','close_10min']

for c in col:
    data = data[pd.notnull(data[c])]

data['trend'] = pd.Categorical(data['trend'])
dfDummies = pd.get_dummies(data['trend'], prefix = 'trend')
data = pd.concat([data, dfDummies], axis=1)
    
x_data = data[['close','Fast_Line','Slow_Line_9','trend_uptrend','trend_downtrend','RSI']].copy()
y_data = data[['close_10min']].copy()

#normalise
for i in x_data.columns:
    x_data[i] = (x_data[i] - x_data[i].mean()) / x_data[i].std()
    
x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=1)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=0.2, random_state=1)

#linear regression
model = linear_model.LinearRegression()
model.fit(x_train,y_train)
predictions = model.predict(x_test)

print(predictions[0:5])

plt.scatter(y_test, predictions, color = 'green')
plt.title('Linear Regression') 
plt.xlabel("True Values")
plt.ylabel("Predictions")
plt.show() 
print("Score:", model.score(x_test, y_test))

validation_scores = cross_val_score(model, x_data, y_data, cv=6)
print("Cross-validated scores:", validation_scores)

#print("accuracy : ", accuracy_score(y_test, predictions))



#polynomial regression

#model2 = linear_model.LinearRegression()
#model2.fit(x_train, y_train)
#predictions2 = model2.predict(x_test)
#plt.plot(y_test, predictions2)
#plt.scatter(y_test, predictions2)
#plt.title("Linear Model, Polynomial Degree = 1")
#plt.show()
#
#poly_features = PolynomialFeatures(degree = 2)  
#X_poly = poly_features.fit_transform(x_train)
#poly_model = LinearRegression()  
#poly_model.fit(X_poly, y_train)
#pred = poly_model.predict(X_poly)
#plt.plot(y_test, predictions2)
#plt.scatter(y_test, predictions2)
#plt.title("Polynomial Degree = 2")
#plt.show()