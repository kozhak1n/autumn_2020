# -*- coding: utf-8 -*-
"""NN Mersedes FINAL

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16LJ7JTVUXurptgYu2aNY-2MbDt9zwWd1

#Серебрянский Александр Сергеевич 18-АС (18-ИВТ-1)
#3 Вариант

##Подготовка, Импорты
"""

!pip install -U keras-tuner
!pip install -U pygal

import pandas as pd
import numpy as np
import random
import pygal
from keras.datasets import boston_housing
from keras.models import Sequential
from keras.layers import Dense, MaxPooling2D, Conv2D, Flatten
from keras.optimizers import SGD
from kerastuner.tuners import RandomSearch, Hyperband, BayesianOptimization
from kerastuner.engine import hyperparameters
from keras.layers import Dropout
from keras import backend as K
from keras.regularizers import L1, L2
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import time
import math
import seaborn as sns
import matplotlib.pyplot as plt
from keras import utils
from sklearn.preprocessing import MinMaxScaler

from google.colab import drive
drive.mount('/content/drive')

"""##Подготовка данных

###Получение и вывод тренировочных данных
"""

train_path = '/content/drive/My Drive/labs/train.csv'
data = pd.read_csv(train_path)
data.head()

"""###Удаление столбика ID"""

del data['ID']
data.head()

"""###Получение истинных значений и удаление стобца Y"""

y_data = data.get('y')
x_data = data.drop('y' , axis=1)

"""###Выделение и удаление странных данных, у которых значение, отличное от нуля только в одной строке"""

strange_data = []
for col in x_data:
    if len(x_data[col].unique()) == 1:
        strange_data.append(col)
x_data[strange_data].describe()
x_data.drop(strange_data, 1, inplace = True)

"""###Кодирование буквенных данных"""

# list of categorical variables
word_vars = [var for var in x_data.columns if x_data[var].dtypes == 'O']
# все буквы и цифры шифруются, чтобы остались только числа
df = pd.DataFrame(x_data[word_vars])
x_data[word_vars] = df.apply(preprocessing.LabelEncoder().fit_transform)

print(x_data[word_vars])

mms = MinMaxScaler()
x_data[word_vars] = mms.fit_transform(x_data[word_vars])

"""###Разделение данных на тренировочные и тестовые"""

x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, random_state=0, test_size = 0.2)

"""##Создание и обучение нейросети

###Создание нейросети
"""

model = Sequential()
model.add(Dense(128, activation="relu", input_shape=(x_train.shape[1],)))
model.add(Dense(128, activation="relu"))
model.add(Dropout(0.2))
model.add(Dense(1))
print("[DEBUG-USER] nn created")

model.compile(optimizer="adam", loss="mse", metrics=["mae"])
print("[DEBUG-USER] nn compiled")

model.summary()

"""###Обучение нейросети"""

history = model.fit(x_train, y_train, epochs=100, batch_size=128, verbose=1, validation_split=0.2)
print(history)
history = history.history
print("[DEBUG-USER] nn finish")

"""###Вывод графика"""

def graphs(history):
    loss = history["loss"]
    val_loss = history["val_loss"]
    epochs = range(1, len(history['loss']) + 1)
    plt.plot(epochs, loss, 'r', label='Training loss')
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

    plt.clf()

    mae = history['mae']
    val_mae = history['val_mae']
    plt.plot(epochs, mae, 'r', label='Training mae')
    plt.plot(epochs, val_mae, 'b', label='Validation mae')
    plt.title('Training and validation mae')
    plt.xlabel('Epochs')
    plt.ylabel('mae')
    plt.legend()
    plt.show()



# рисуем все графики
graphs(history)

"""###Ошибки"""

print("[INFO] RUNNING ON TEST DATA: \n")
# вычисляем ошибки и выводим их на экран
mse, mae = model.evaluate(x_test, y_test, verbose=0, batch_size=128)
print(f"[INFO] Mean squared error is {mse}")
print(f"[INFO] Mean absolute error is {mae}")

"""##Keras Tuner

###Функция создания модели
"""

def build_model(hp):
  hidden_layers = hp.Choice('hidden_layers', values=[1,2,3])
  activation_choice = hp.Choice('activation', values=['relu', 'selu', 'elu'])
  model = Sequential()
  model.add(Dense(units=hp.Int('units',min_value=256,max_value=512,step=32),activation=activation_choice, input_shape=(x_train.shape[1], ), kernel_regularizer=L2(0.001)))
  model.add(Dropout(0.2))
  for i in range(hidden_layers):
    model.add(Dense(units=hp.Int(f'layer_{i}_units_',min_value=32//(i+1), max_value=128//(i+1),step=64//(i+1)),activation=activation_choice, kernel_regularizer=L2(0.001)))
  model.add(Dense(1))  
  model.compile(optimizer='rmsprop', loss="mse", metrics=["mae"])
  return model

"""###Поиск с помощью Hyperband"""

def find_best_NN(x_train_main, y_train_main):
  # создаю тюнер, который сможет подобрать оптимальную архитектуру модели
  tuner = Hyperband(build_model, objective="loss", max_epochs=20, hyperband_iterations=5)
  print("\n\n\n")
  # начинается автоматический подбор гиперпараметров
  print('[INFO] start searching')
  tuner.search(x_train, y_train, batch_size=128, epochs=20, validation_split=0.3)
  # выбираем лучшую модель
  print("\n\n\nRESULTS SUMMARY")
  tuner.results_summary()
  print("\n\n\n")
  # получаем лучшую модель
  print("\n\n\nHERE IS THE BEST MODEL\n\n\n")
  best_params = tuner.get_best_hyperparameters()[0]
  best_model = tuner.hypermodel.build(best_params)
  best_model.summary()
  return best_model
  

best_model = find_best_NN(x_train, y_train)

"""###Удаляем логи"""

! rm -rf untitled_project/

"""###Тренировка лучшей модели"""

best_history = best_model.fit(x_train, y_train, epochs=100, batch_size=128, validation_split=0.2)
best_history = best_history.history
print("[INFO] Training has been finished")

"""###График лучшей модели"""

graphs(best_history)

"""###Проверка на тестовых данных"""

print("[INFO] RUNNING ON TEST DATA: \n")
mse, mae = best_model.evaluate(x_test, y_test, verbose=1)
print(f"[INFO] Mean squared error is {mse}")
print(f"[INFO] Mean absolute error is {mae}")

"""##Предсказания

###Ручная модель
"""

predicted_y = model.predict(x_test)
predicted_y = np.reshape(predicted_y, (predicted_y.shape[0]))

"""###Модель Keras_Tuner"""

best_predicted_y = best_model.predict(x_test)
best_predicted_y = np.reshape(best_predicted_y, (best_predicted_y.shape[0]))

"""###Перевод в векторы"""

predicted_y = np.reshape(predicted_y, (predicted_y.shape[0]))
best_predicted_y = np.reshape(best_predicted_y, (best_predicted_y.shape[0]))
y_test = np.reshape(y_test, (y_test.shape[0]))

"""###Подсчет коэфицента корреляции ручной модели"""

best_cc = np.corrcoef(predicted_y, y_test)
best_cc = best_cc[0][1]
print(f'Correlation Coefficient: {best_cc}')

"""###Подсчет коэфицента корреляции модели Keras_Tuner"""

best_cc_tuner = np.corrcoef(best_predicted_y, y_test)
best_cc_tuner = best_cc_tuner[0][1]
print(f'Correlation Coefficient: {best_cc_tuner}')

"""###Подсчет разницы между Keras_Tuner и ручной моделью"""

cordiff = abs(best_cc - best_cc_tuner)
if best_cc > best_cc_tuner:
  best = "Handmade"
else:
  best = "Keras"
print("Best NN: " + best + 
"\nDifference: """+str(cordiff))