import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam, SGD
import matplotlib.pyplot as plt


def load_data():
    columns = ["input_X", "input_Y", "expected_X", "expected_Y"]
    training_data = pd.DataFrame(columns=columns)
    testing_data = pd.DataFrame(columns=columns)

    static_folders_paths = ["./dane/f8/stat", "./dane/f10/stat"]
    dynamic_folders_paths = ["./dane/f8/dyn", "./dane/f10/dyn"]

    for i in range(2):
        static_folder_path = static_folders_paths[i]
        dynamic_folder_path = dynamic_folders_paths[i]

        # Sorting the files to ensure data is concatenated in alphabetical order.
        static_files = sorted(file for file in os.listdir(static_folder_path) if file.endswith(".csv"))
        dynamic_files = sorted(file for file in os.listdir(dynamic_folder_path) if file.endswith(".csv"))

        for file in static_files:
            file_path = os.path.join(static_folder_path, file)
            temp_data_frame = pd.read_csv(file_path, names=columns)
            training_data = pd.concat([training_data, temp_data_frame], ignore_index=True)

        for file in dynamic_files:
            file_path = os.path.join(dynamic_folder_path, file)
            temp_data_frame = pd.read_csv(file_path, names=columns)
            testing_data = pd.concat([testing_data, temp_data_frame], ignore_index=True)

    # anty_null procedure
    training_data = training_data.dropna()
    testing_data = testing_data.dropna()

    # save to csv (debug purpose)
    training_data.to_csv("training_data.csv", index=False)
    testing_data.to_csv("testing_data.csv", index=False)

    print("Data loaded ✅")
    return training_data, testing_data


class NeuralNetworkModel:
    def __init__(self, hidden_layers, activation_function='tanh', activation_function_out='linear',
                 weight_init_method='glorot_uniform', num_of_inputs_neurons=2, num_of_outputs_neurons=2,
                 epochs=100, learning_rate=0.01, optimizer='adam', momentum=0.9):
        self.hidden_layers = hidden_layers
        self.activation_function = activation_function
        self.activation_function_out = activation_function_out
        self.weight_init_method = weight_init_method
        self.num_of_inputs_neurons = num_of_inputs_neurons
        self.num_of_outputs_neurons = num_of_outputs_neurons
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.optimizer_type = optimizer
        self.momentum = momentum
        self.model = self.create_model()

    def create_model(self):
        model = Sequential()

        # input layer
        il = Input(shape=(self.num_of_inputs_neurons,))
        model.add(il)

        # first hidden layer
        fhl = Dense(self.hidden_layers[0], activation=self.activation_function, kernel_initializer=self.weight_init_method)
        model.add(fhl)

        for layer in self.hidden_layers[1:]:
            # next hidden layer
            nhl = Dense(layer, activation=self.activation_function, kernel_initializer=self.weight_init_method)
            model.add(nhl)

        # output layer
        ol = Dense(self.num_of_outputs_neurons, kernel_initializer=self.weight_init_method, activation=self.activation_function_out)
        model.add(ol)
        print("Model created ✅")
        return model

    def train(self, training_data, testing_data):
        # preparation of training and validation data
        train_data = training_data[["input_X", "input_Y"]].values
        train_labels = training_data[["expected_X", "expected_Y"]].values
        val_data = testing_data[["input_X", "input_Y"]].values
        val_labels = testing_data[["expected_X", "expected_Y"]].values

        # optimizer selection
        if self.optimizer_type == 'adam':
            opt = Adam(learning_rate=self.learning_rate)
        elif self.optimizer_type == 'sgd':
            opt = SGD(learning_rate=self.learning_rate, momentum=self.momentum)
        else:
            raise ValueError('Optimizer must be either "adam" or "sgd"')

        # model compilation
        self.model.compile(optimizer=opt, loss="mean_squared_error", metrics=['mse'])

        history = self.model.fit(train_data, train_labels, epochs=self.epochs, validation_data=(val_data, val_labels), verbose=0)
        print("\tModel trained ✅")
        return history

    def test(self, testing_data):
        # preparation of validation data
        test_data = testing_data[["input_X", "input_Y"]].values
        test_labels = testing_data[["expected_X", "expected_Y"]].values

        # final evaluation of the model
        mse = self.model.evaluate(test_data, test_labels, verbose=0)
        predictions = self.model.predict(test_data)
        print("MSE on test data: {}".format(mse[1]))
        return mse[1], predictions

    def plot(self, history):
        plt.plot(history.history['mse'], label='MSE na zbiorze uczącym')
        plt.plot(history.history['val_mse'], label='MSE na zbiorze walidacyjnym')
        plt.xlabel('Epoki')
        plt.ylabel('MSE')
        plt.legend()
        plt.show()

    def give_train_mse(self, history):
        # static data
        return history.history['mse']
    def give_test_mse(self, history):
        # dynamic data
        return history.history['val_mse']


# plot 3
def calculate_cdf(errors):
    sorted_errors = np.sort(errors)
    cdf = np.cumsum(sorted_errors) / np.sum(sorted_errors)
    return sorted_errors, cdf
def plot_cdf(models, testing_data):
    plt.figure(figsize=(10, 6))
    counter = 1
    for model in models:
        mse, predictions = model.test(testing_data)
        errors = np.abs(testing_data[["expected_X", "expected_Y"]].values - predictions)
        errors = errors.flatten()

        sorted_errors, cdf = calculate_cdf(errors)
        plt.plot(sorted_errors, cdf, label='Model: {}'.format(counter))
        plt.grid(True)
        counter += 1

    # distribution of errors for real dynamic measurements
    real_errors = np.abs(
        testing_data[["expected_X", "expected_Y"]].values - testing_data[["input_X", "input_Y"]].values)
    real_errors = real_errors.flatten()
    sorted_real_errors, real_cdf = calculate_cdf(real_errors)
    plt.plot(sorted_real_errors, real_cdf, label='wszystkie pomiary dynamiczne', linestyle='--')

    plt.xlabel('Błąd')
    plt.ylabel('Skumulowane prawdopodobieństwo')
    plt.title('Dystrybuanta blędów pomiarów dynamicznych dla wybranych wariantów sieci')
    plt.legend()
    plt.show()