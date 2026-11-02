import tkinter
import cv2
import PIL.Image, PIL.ImageTk
from tkinter import simpledialog
import time
from tkinter import messagebox
import os
from keras.utils.np_utils import to_categorical
import numpy as np
from keras.layers import  MaxPooling2D
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D
from keras.models import Sequential
from keras.models import model_from_json
import pickle
from tkinter import *
import random

class App:
    global classifier
    global labels
    global X_train
    global Y_train
    global prices
    global cart
    global text
    global person_id
    global img_canvas
    global cascPath
    global faceCascade
    global pid
    
    def __init__(self, window, window_title, video_source=0):
        global cart
        global text
        cart = []
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1300x1200")
        self.video_source = video_source
        self.vid = MyVideoCapture(self.video_source)
        self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.pack()
        self.font1 = ('times', 13, 'bold')
        self.btn_snapshot=tkinter.Button(window, text="Add Product Details", command=self.snapshot)
        self.btn_snapshot.place(x=10,y=50)
        self.btn_snapshot.config(font=self.font1) 
        self.btn_train=tkinter.Button(window, text="Train Model", command=self.trainmodel)
        self.btn_train.place(x=10,y=100)
        self.btn_train.config(font=self.font1) 
        self.btn_predict=tkinter.Button(window, text="Add/Remove Product from Basket", command=self.predict)
        self.btn_predict.place(x=10,y=150)
        self.btn_predict.config(font=self.font1)

        self.btn_person=tkinter.Button(window, text="Capture Person", command=self.capturePerson)
        self.btn_person.place(x=10,y=200)
        self.btn_person.config(font=self.font1)

        self.img_canvas = tkinter.Canvas(window, width = 200, height = 200)
        self.img_canvas.place(x=10,y=250)

        self.text=Text(window,height=35,width=45)
        scroll=Scrollbar(self.text)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.place(x=1000,y=50)
        self.text.config(font=self.font1)

        self.cascPath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(self.cascPath)

        self.delay = 15
        self.update()
        self.window.mainloop()

    def getID(self,name):
        index = 0
        for i in range(len(labels)):
            if labels[i] == name:
                index = i
                break
        return index

    def capturePerson(self):
        option = 0
        ret, frame = self.vid.get_frame()
        img = frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.faceCascade.detectMultiScale(gray,1.3,5)
        print("Found {0} faces!".format(len(faces)))
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            img = frame[y:y + h, x:x + w]
            img = cv2.resize(img,(500,500))
            option = 1
        if option == 1:
            self.pid = random.randint(1000, 100000)
            cv2.imwrite("images/"+str(self.pid)+".jpg",img);
            cv2.imshow("Person ID : "+str(self.pid)+".jpg",img)
            c2.waitKey(0)
        else:
            messagebox.showinfo("Face or person not detected","Face or person not detected")

    def snapshot(self):
        ret, frame = self.vid.get_frame()
        if ret:
            img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            pname = simpledialog.askstring("Enter Product Name", "Enter Product Name",parent=self.window)
            price = simpledialog.askfloat("Enter Product Price", "Enter Product Price", parent=self.window, minvalue=1.0, maxvalue=100000.0)
            if not os.path.exists('Product/'+pname):
                os.makedirs('Product/'+pname)
            img_name = time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg"    
            cv2.imwrite('Product/'+pname+'/'+img_name,img)
            f = open("details.txt", "a+")
            f.write(pname+","+str(price)+","+img_name+"\n")
            f.close()
            messagebox.showinfo("Product details saved","Product details saved")

    def trainmodel(self):
        global labels
        global X_train
        global Y_train
        global classifier
        global prices
        labels = []
        X_train = []
        Y_train = []
        prices = []
        path = 'Product'
        for root, dirs, directory in os.walk(path):
            for j in range(len(directory)):
                name = os.path.basename(root)
                if name not in labels:
                    labels.append(name)

        for i in range(len(labels)):
            cost = '0'
            with open("details.txt", "r") as file:
                for line in file:
                    line = line.strip('\n')
                    line = line.strip()
                    arr = line.split(",")
                    if arr[0] == labels[i] and cost == '0':
                        cost = arr[1]
            file.close()
            prices.append(cost)

        for root, dirs, directory in os.walk(path):
            for j in range(len(directory)):
                name = os.path.basename(root)
                img = cv2.imread(root+"/"+directory[j])
                img = cv2.resize(img, (256,256))
                im2arr = np.array(img)
                im2arr = im2arr.reshape(256,256,3)
                X_train.append(im2arr)
                Y_train.append(self.getID(name))
        X_train = np.asarray(X_train)
        Y_train = np.asarray(Y_train)
        print(Y_train)
        print(labels)
        print(prices)
        X_train = X_train.astype('float32')
        X_train = X_train/255
    
        test = X_train[3]
        cv2.imshow("aa",test)
        cv2.waitKey(0)
        indices = np.arange(X_train.shape[0])
        np.random.shuffle(indices)
        X_train = X_train[indices]
        Y_train = Y_train[indices]
        Y_train = to_categorical(Y_train)

        if os.path.exists('Model/model.json'):
            with open('Model/model.json', "r") as json_file:
                loaded_model_json = json_file.read()
                classifier = model_from_json(loaded_model_json)

            classifier.load_weights("Model/model_weights.h5")
            classifier._make_predict_function()   
            print(classifier.summary())
            f = open('Model/history.pckl', 'rb')
            data = pickle.load(f)
            f.close()
            acc = data['accuracy']
            accuracy = acc[9] * 100
            messagebox.showinfo("Training model accuracy","Training Model Accuracy = "+str(accuracy))
        else:
            classifier = Sequential()
            classifier.add(Convolution2D(32, 3, 3, input_shape = (256, 256, 3), activation = 'relu'))
            classifier.add(MaxPooling2D(pool_size = (2, 2)))
            classifier.add(Convolution2D(32, 3, 3, activation = 'relu'))
            classifier.add(MaxPooling2D(pool_size = (2, 2)))
            classifier.add(Flatten())
            classifier.add(Dense(output_dim = 256, activation = 'relu'))
            classifier.add(Dense(output_dim = 4, activation = 'softmax'))
            print(classifier.summary())
            classifier.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])
            hist = classifier.fit(X_train, Y_train, batch_size=16, epochs=10, shuffle=True, verbose=2)
            classifier.save_weights('Model/model_weights.h5')            
            model_json = classifier.to_json()
            with open("Model/model.json", "w") as json_file:
                json_file.write(model_json)
            f = open('Model/history.pckl', 'wb')
            pickle.dump(hist.history, f)
            f.close()
            f = open('Model/history.pckl', 'rb')
            data = pickle.load(f)
            f.close()
            acc = data['accuracy']
            accuracy = acc[9] * 100
            messagebox.showinfo("Training model accuracy","Training Model Accuracy = "+str(accuracy))

    def predict(self):
        ret, frame = self.vid.get_frame()
        img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, (256,256))
        im2arr = np.array(img)
        im2arr = im2arr.reshape(1,256,256,3)
        image = np.asarray(im2arr)
        image = image.astype('float32')
        image = image/255
        preds = classifier.predict(image)
        predict = np.argmax(preds)
        pname = labels[predict]
        print(str(pname)+" "+str(np.amax(preds)))
        if np.amax(preds) >= 0.85:
            cost = prices[predict]
            if pname in cart:
                cart.remove(pname)
            else:
                cart.append(pname)
            self.text.delete('1.0', END)
            total_amt = 0
            for i in range(len(cart)):
                for k in range(len(labels)):
                    if labels[k] == cart[i]:
                        cost = prices[k]
                        k = len(labels)
                total_amt = total_amt + float(cost)        
                self.text.insert(END,"Product Name : "+cart[i]+"\n")
                self.text.insert(END,"Product Cost : "+cost+"\n\n")
            self.text.insert(END,"Total Amount : "+str(total_amt)+"\n\n")    
        else:
            messagebox.showinfo("Unable to recognized product","Unable to recognized product")


             
    def update(self):
        ret, frame = self.vid.get_frame()
        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
            self.window.after(self.delay, self.update)
 
 
class MyVideoCapture:
    def __init__(self, video_source=0):
        
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.pid = 0
 
    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)
 
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
App(tkinter.Tk(), "Tkinter and OpenCV")
