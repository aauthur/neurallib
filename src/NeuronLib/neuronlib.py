from linalgebralib import LinAlgebraLib as la
import math
import random
import csv
import string
import statistics
import matplotlib.pyplot as plt

class Network():
    def __init__(self, layers):
        """Initialized a neural network with random weights and biases. Layers paramater is meant to be a list of integers representing the number of neurons in each layer."""
        self.layers = len(layers)
        self.weights = [la.Matrix(content=[[random.normalvariate(0,1) for j in range(layers[i])] for k in range(layers[i+1])]) for i in range(self.layers-1)]
        self.biases = [la.Matrix(content=[[random.normalvariate(0,1)] for j in range(layers[i])]) for i in range(1,self.layers)]

    def result(self, input):
        """Takes data in list format corresponding to the first layer of neurons, and outputs the result of the neural network."""
        try:
            if len(input) != self.weights[0].columns:
                raise TypeError
            else:
                v = la.Matrix(content=[[i] for i in input])
                for w,b in zip(self.weights, self.biases):
                    v = w*v + b
                    v = la.Matrix(content=[[activation(i[0])] for i in v.contents])
                return v
                """
                for w,b in zip(self.weights[:-1], self.biases[:-1]):
                    v = w*v + b
                    v = la.Matrix(content=[[activation(i[0])] for i in v.contents])
                return self.weights[-1]*v + self.biases[-1]
                """
                
        except TypeError:
            raise TypeError("Invalid input. Must pass data to the network as a list corresponding to the number of neurons in the input layer.")
        
    def save(self):
        save_file = open('networkdata.txt', 'w')
        save_file.write("Weights:\n\n")
        for weight in self.weights:
            save_file.write(str(weight) + "\n\n")
        save_file.write("Biases:\n\n")
        for bias in self.biases:
            save_file.write(str(bias) + "\n\n")
        
    def backprop(self, input, output, last_layer_activation=True):
        try:
            if len(input) != self.weights[0].columns or self.weights[-1].rows != len(output):
                raise TypeError
            else:
                change_weights = [la.Matrix(size=(i.rows, i.columns)) for i in self.weights]
                change_biases = [la.Matrix(size=(i.rows, i.columns)) for i in self.biases]
                zs = []
                neural_outputs = []
                inp = la.Matrix(content=[[i] for i in input])
                #Keeping track of inputs and outputs of each layer in the network given input data.
                zs.append(inp)
                neural_outputs.append(inp)
                if last_layer_activation:
                    for w,b in zip(self.weights, self.biases):
                        inp = w*inp + b
                        zs.append(inp)
                        inp = la.Matrix(content=[[activation(l[0])] for l in inp.contents])
                        neural_outputs.append(inp)
                else:
                    for w,b in zip(self.weights[:-1], self.biases[:-1]):
                        inp = w*inp + b
                        zs.append(inp)
                        inp = la.Matrix(content=[[activation(l[0])] for l in inp.contents])
                        neural_outputs.append(inp)
                    inp = self.weights[-1]*inp + self.biases[-1]
                    zs.append(inp)
                    neural_outputs.append(inp)
                #Actual backpropogation process
                y = la.Matrix(content=[[i] for i in output])
                delta = neural_outputs[-1] - y
                if last_layer_activation:
                    delta = la.Matrix(content=[[delta.contents[i][0]*activation_prime(zs[-1].contents[i][0])] for i in range(len(output))])
                change_weights[-1] = delta*zs[-2].transpose()
                change_biases[-1] = delta
                delta = self.weights[-1].transpose()*delta
                for l in range(2,self.layers):
                    change_biases[-l] = delta
                    change_weights[-l] = delta*zs[-l-1].transpose()
                    delta = self.weights[-l].transpose()*delta
                return (change_weights,change_biases)
        except TypeError:
            raise TypeError("Invalid input: Network expects input data to match number of input neurons and output data to match number of output neurons.")
        
    def batch(self, data):
        """Takes as argument a list of several inputs and expected ouputs. Way of computing updates to the network based on an average of a sample of data, rather than updating per data point."""
        n = len(data)
        proposed_changes = []
        for i in data:
            proposed_changes.append(self.backprop(i[0],i[1]))
        change_weights = proposed_changes[0][0]
        change_biases = proposed_changes[0][1]
        proposed_changes.pop(0)
        for change in proposed_changes:
            for i in range(len(change_weights)):
                change_weights[i] = change_weights[i] + change[0][i]
                change_biases[i] = change_biases[i] + change[1][i]
        for i in range(self.layers-1):
            change_weights[i] = change_weights[i]*(1/n)
            change_biases[i] = change_biases[i]*(1/n)
        return (change_weights, change_biases)

    def update_wb(self, change_weights, change_biases, eta, reg_rate=0.001):
        """Takes a learning rate and changes to the network from backpropogation as argument, and updates weights and biases in the network according to the direction of most rapid descent for the cost function."""
        for i in range(self.layers-1):
            self.weights[i] = self.weights[i]*(1 - eta * reg_rate)  - change_weights[i]*eta
            self.biases[i] = self.biases[i] - change_biases[i]*eta
    
    def train(self, data, threshold=5, batch_size=1, learning_rate=0.1):
        """Takes training data (list of inputs and expected outputs), batch size, and a learning rate as arguments, and trains the network based on stochastic gradient descent."""
        batches = []
        data = data
        random.shuffle(data)
        while data != []:
            batch = []
            for i in range(batch_size):
                try:
                    batch.append(data.pop(random.randint(0,len(data)-1)))
                except ValueError:
                    break
            batches.append(batch)
        for i in range(len(batches)):
            dw, db = self.batch(batches[i])
            #Gradient clipping
            for j in range(len(dw)):
                if (dw[j].transpose()*dw[j]).rows == 1:
                    norm =  math.sqrt((dw[j].transpose()*dw[j]).contents[0][0])
                else:
                    norm =  math.sqrt((dw[j]*dw[j].transpose()).contents[0][0])
                if norm > threshold:
                    dw[j] = dw[j]*(threshold/norm)
            for j in range(len(db)):
                norm =  math.sqrt((db[j].transpose()*db[j]).contents[0][0])
                if norm > threshold:
                    db[j] = db[j]*(threshold/norm)
            self.update_wb(dw, db, learning_rate)
            print(f"Progress: Training Batch {i+1}/{len(batches)}")
        

#Function for mapping neuron inputs to values between 0 and 1.
def activation(n):
    if n < -500:
        return 0
    elif n > 500:
        return 1
    else:
        return 1 / (1 + math.e**(-n))
    
def activation_prime(n):
    return activation(n)*(1-activation(n))

def import_spanish_songs(path):
    db = []
    chars = list(string.ascii_lowercase + 'ñáéíóúü ')
    possible_chars = {chars[i]:i for i in range(len(chars))}
    with open(path, newline='', encoding='latin1') as f:
        reader = csv.DictReader(f)
        n = len(chars)
        for row in reader:
            song = row["Title"].lower()
            encoded_song = la.Matrix(size=(20,n))
            if len(song) > 20:
                song = song[:20]
            for i in range(len(song)):
                if song[i] in possible_chars:
                    encoded_song.contents[i][possible_chars[song[i]]] = 1
            real_encoded_song = []
            for l in encoded_song.contents:
                for j in l:
                    real_encoded_song.append(j)
            db.append([real_encoded_song, [1,0]])
    f.close()
    return db

def import_english_songs(path):
    db = []
    chars = list(string.ascii_lowercase + 'ñáéíóúü ')
    possible_chars = {chars[i]:i for i in range(len(chars))}
    with open(path, newline='', encoding="latin1") as f:
        reader = csv.DictReader(f)
        n = len(chars)
        for row in reader:
            song = row["title"].lower()
            encoded_song = la.Matrix(size=(20,n))
            if len(song) > 20:
                song = song[:20]
            for i in range(len(song)):
                if song[i] in possible_chars:
                    encoded_song.contents[i][possible_chars[song[i]]] = 1
            real_encoded_song = []
            for l in encoded_song.contents:
                for j in l:
                    real_encoded_song.append(j)
            db.append([real_encoded_song, [0,1]])
    f.close()
    return db

def encode_input_song(song):
    song = song.lower()
    chars = list(string.ascii_lowercase + 'ñáéíóúü ')
    n = len(chars)
    possible_chars = {chars[i]:i for i in range(len(chars))}
    encoded_song = la.Matrix(size=(20,n))
    if len(song) > 20:
        song = song[:20]
    for i in range(len(song)):
        if song[i] in possible_chars:
            encoded_song.contents[i][possible_chars[song[i]]] = 1
    real_encoded_song = []
    for l in encoded_song.contents:
        for j in l:
            real_encoded_song.append(j)
    return real_encoded_song

def test_single_output(input, expected_output):
    tmp = net.result(input)
    if tmp.contents[0][0] > tmp.contents[1][0]:
        prediction = [1,0]
    else:
        prediction = [0,1]
    return prediction == expected_output

def test_accuracy(data):
    results = []
    for i in data:
        if test_single_output(i[0], i[1]):
            results.append(1)
        else:
            results.append(0)
    return(statistics.fmean(results)*100)


spanish_data = import_spanish_songs("spanishsongs.csv")
english_data = import_english_songs("englishsongs.csv")

net = Network([680, 30, 2])
net.save()

training_data = spanish_data[0:1000] + english_data[0:1000]
test_data = spanish_data[1000:1100] + english_data[1000:1100]

print(f"Initial network has {test_accuracy(test_data)}% accuracy!")

net.train(data=training_data,threshold=10, batch_size=5, learning_rate=0.05)

net.save()

print(f"Resultant network has {test_accuracy(test_data)}% accuracy!")

print("------Trained Neural Net-------")
print("Neural net should output something close to the input.")
while True:
    n = input("Song title to pass to neural net: ")
    m = net.result(encode_input_song(n))
    if m.contents[0][0] > m.contents[1][0]:
        result = "Spanish"
    else:
        result = "English"
    print(f"Neural net output: {result}")









#4/18/2024 Implemented neural network object, instantiation method, and method for computing its output. Also implemented a basic activation function (sigmoid).

#TODO: Need to implement training of the neural network through back-propagation and gradient descent.
#Next need to scrape for some sort of test (Spanish vs. English song titles?) data to test the efficacy of the network. 

"""
x = [(i/10) for i in range(100)]
y = [net.result([i/10]).contents[0][0] for i in range(100)]

plt.scatter(x, y)
plt.show()

print("------Untrained Neural Net------")
while True:
    try:
        n = input("Number to pass to neural net: ")
        n = float(n)
        print(f"Neural net output: {net.result([n])}")
    except ValueError:
        if n == "q":
            break
        else:
            print("Invalid input!")

data = []
for i in range(40000):
    n = random.uniform(0,100)
    data.append([[n],[7*n-3.1]])

------

x = [(i/10) for i in range(100)]
y = [net.result([i/10]).contents[0][0] for i in range(100)]

plt.scatter(x, y)
plt.title("7x-3.1", loc="center")
plt.show()

"""