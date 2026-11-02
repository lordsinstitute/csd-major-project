import tkinter as tk
from tkinter import simpledialog, messagebox, Text, END
import cv2
import os
import time
import numpy as np
from PIL import Image, ImageTk
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical


# ==========================================
# Video Capture
# ==========================================
class MyVideoCapture:
    def __init__(self, video_source=0):
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open camera")

        self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame(self):
        ret, frame = self.vid.read()
        if ret:
            return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return ret, None

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


# ==========================================
# Main App
# ==========================================
class App:

    def __init__(self, window, title):

        self.window = window
        self.window.title(title)
        self.window.geometry("1300x800")

        self.labels = []
        self.prices = {}
        self.cart = []
        self.model_path = "Model/product_model.h5"
        self.classifier = None

        self.vid = MyVideoCapture(0)

        self.canvas = tk.Canvas(window, width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        # Buttons
        tk.Button(window, text="Add Category", command=self.add_category).place(x=10, y=50)
        tk.Button(window, text="Add Images", command=self.add_images).place(x=10, y=100)
        tk.Button(window, text="Train Model", command=self.train_model).place(x=10, y=150)
        tk.Button(window, text="Predict Product", command=self.predict).place(x=10, y=200)

        self.text = Text(window, height=30, width=40)
        self.text.place(x=1000, y=50)

        self.delay = 15
        self.update()
        self.window.mainloop()

    # ==========================================
    # Add Category
    # ==========================================
    def add_category(self):

        category = simpledialog.askstring("Category", "Enter Product Category Name")
        price = simpledialog.askfloat("Price", "Enter Product Price")

        if not category or not price:
            return

        folder = os.path.join("Product", category)
        os.makedirs(folder, exist_ok=True)

        self.prices[category] = price

        messagebox.showinfo("Success", f"Category '{category}' created")

    # ==========================================
    # Add Images to Category
    # ==========================================
    def add_images(self):

        if not os.path.exists("Product"):
            messagebox.showerror("Error", "Create category first")
            return

        categories = next(os.walk("Product"))[1]

        if len(categories) == 0:
            messagebox.showerror("Error", "No categories found")
            return

        category = simpledialog.askstring("Category",
                                          f"Available: {categories}\nEnter category name")

        if category not in categories:
            messagebox.showerror("Error", "Invalid category")
            return

        count = simpledialog.askinteger("Images",
                                        "How many images to capture?",
                                        minvalue=1, maxvalue=100)

        if not count:
            return

        folder = os.path.join("Product", category)

        for i in range(count):
            ret, frame = self.vid.get_frame()
            if not ret:
                continue

            img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            img_name = time.strftime("%d-%m-%Y-%H-%M-%S") + f"_{i}.jpg"
            cv2.imwrite(os.path.join(folder, img_name), img)

            cv2.waitKey(300)  # small delay

        messagebox.showinfo("Success", f"{count} images added to {category}")

    # ==========================================
    # Train Model
    # ==========================================
    def train_model(self):

        if not os.path.exists("Product"):
            messagebox.showerror("Error", "No Product folder")
            return

        self.labels = next(os.walk("Product"))[1]

        if len(self.labels) < 2:
            messagebox.showerror("Error", "Need at least 2 categories")
            return

        X_train = []
        Y_train = []

        for idx, label in enumerate(self.labels):
            folder = os.path.join("Product", label)
            for img_name in os.listdir(folder):
                path = os.path.join(folder, img_name)
                img = cv2.imread(path)
                if img is None:
                    continue
                img = cv2.resize(img, (128, 128))
                X_train.append(img)
                Y_train.append(idx)

        X_train = np.array(X_train)
        Y_train = np.array(Y_train)

        print("Dataset shape:", X_train.shape)
        print("Class distribution:", np.bincount(Y_train))

        # Shuffle
        indices = np.arange(len(X_train))
        np.random.shuffle(indices)
        X_train = X_train[indices]
        Y_train = Y_train[indices]

        X_train = X_train.astype("float32") / 255
        Y_train = to_categorical(Y_train)

        os.makedirs("Model", exist_ok=True)

        self.classifier = Sequential([
            Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
            MaxPooling2D(2,2),

            Conv2D(64, (3,3), activation='relu'),
            MaxPooling2D(2,2),

            Conv2D(128, (3,3), activation='relu'),
            MaxPooling2D(2,2),

            Flatten(),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(len(self.labels), activation='softmax')
        ])

        self.classifier.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        history = self.classifier.fit(
            X_train,
            Y_train,
            epochs=20,
            batch_size=16,
            validation_split=0.2,
            verbose=1
        )

        self.classifier.save(self.model_path)

        train_acc = history.history['accuracy'][-1] * 100
        val_acc = history.history['val_accuracy'][-1] * 100

        messagebox.showinfo("Training Complete",
                            f"Train Accuracy: {train_acc:.2f}%\n"
                            f"Validation Accuracy: {val_acc:.2f}%")

    # ==========================================
    # Predict
    # ==========================================
    def predict(self):

        if not os.path.exists(self.model_path):
            messagebox.showerror("Error", "Train model first")
            return

        if self.classifier is None:
            self.classifier = load_model(self.model_path)

        ret, frame = self.vid.get_frame()
        if not ret:
            return

        img = cv2.resize(frame, (128, 128))
        img = np.array(img).reshape(1, 128, 128, 3).astype("float32") / 255

        preds = self.classifier.predict(img)
        confidence = float(np.max(preds))
        index = np.argmax(preds)

        print("Prediction:", preds)
        print("Confidence:", confidence)

        if confidence < 0.60:
            messagebox.showinfo("Not Recognized", "Low confidence")
            return

        product = self.labels[index]
        messagebox.showinfo("Prediction",
                            f"Product: {product}\nConfidence: {confidence:.2f}")

    # ==========================================
    # Camera Loop
    # ==========================================
    def update(self):
        ret, frame = self.vid.get_frame()
        if ret:
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)


# ==========================================
# Run App
# ==========================================
App(tk.Tk(), "Smart Vision Supermarket System")