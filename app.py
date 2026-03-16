from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5.QtWidgets import QFileDialog , QPushButton , QWidget , QMessageBox , QLabel
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
from PyQt5.QtCore import Qt
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import numpy as np
import matplotlib.pyplot as plt
import os 
from PyQt5.QtCore import QTimer
from datetime import datetime
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from PyQt5.QtGui import QIcon

class MyHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.pause_event = threading.Event()
    def on_any_event(self, event):
        if event.is_directory:
            return
        # Restart the application
        restart_application()
    def pause(self):
        self.pause_event.clear()  # Clear the event to pause the thread
        print("MyHandle thread paused")

    def resume(self):
        self.pause_event.set()  # Set the event to resume the thread
        print("MyHandle thread resumed")

def restart_application():
    print("Restarting application...")
    time.sleep(5)
    try:
        # subprocess.Popen(["python", "app.py"])
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        print("Error:", e)

# Function to check if the opening data for the past 30 days is unchanged for a given file
def check_last_30_days(file_path):
    # Read data into DataFrame
    df = pd.read_excel(file_path)

    # Find the latest date available in the 'Date' column
    latest_date = df['Date'].max()
    
    # Calculate the date 30 days ago
    threshold_date = latest_date - pd.Timedelta(days=30)
    
    # Filter the DataFrame to include only rows for the past 30 days
    recent_data = df[df['Date'] >= threshold_date]  # Assuming 'Date' is the column containing the dates
    # Check if there is only one unique opening value within the past 30 days
    unique_openings = recent_data['Closing'].nunique()
    print(unique_openings)
    return unique_openings == 1

class MaterialWidget(QWidget):
    def __init__(self, max_opening_files,latest_opening_files, parent=None):
        super().__init__(parent)
        self.max_opening_files = max_opening_files
        self.latest_opening_files = latest_opening_files
        self.combined_set = self.join_max_and_latest_sets(self.max_opening_files, self.latest_opening_files)

    def join_max_and_latest_sets(self,max_opening_files, latest_opening_files):
        combined_set = set()

            # Iterate over each file name in the maximum opening set
        for max_file_name, max_opening in max_opening_files:
            # Check if the file name exists in the latest opening set
            for latest_file_name, latest_opening in latest_opening_files:
                if max_file_name == latest_file_name:
                    # If the file name matches, create a tuple with file name, max opening, and latest opening
                    combined_set.add((max_file_name, max_opening, latest_opening))
                    break  # Break the inner loop to avoid unnecessary iterations

        return combined_set

    

    def paintEvent(self, event):
        painter = QPainter(self)
        brush = QBrush(Qt.SolidPattern)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        x, y = 50, 50  # Initial position for the shapes

        for file_name, max_opening, latest_opening in self.combined_set:

            # Determine the color based on the latest opening
            if latest_opening >= max_opening * 0.5:
                color = Qt.green
            elif latest_opening >= max_opening * 0.25:
                color = Qt.yellow
            else:
                color = Qt.red

            painter.setBrush(QColor(color))
    
            # Set the maximum capacity of the box to be the maximum opening of the raw material
            capacity = max_opening
    
            width, height = 100, 100  # Fixed size for all boxes
            # Calculate the height of the filled portion based on the material amount
            filled_height = (latest_opening / capacity) * height
            # Draw the filled portion of the box
            painter.drawRect(x, int(y + height - filled_height), width, int(filled_height))
            # Draw the empty portion of the box
            empty_height = height - filled_height
            painter.setBrush(QColor(Qt.lightGray))
            painter.drawRect(x, y, width, int(empty_height))
            # Calculate the position to display the amount text within the box
            text_x = x + width // 2
            text_y = y + height // 2
            painter.drawText(text_x, text_y, str(latest_opening))  # Display the amount
            name_width = painter.fontMetrics().width(file_name)
            name_height = painter.fontMetrics().height()
            name_x = int(x + (width - name_width) / 2)
            name_y = int(y + height + name_height + 15)  # Adjusted to add more space below the text
            painter.drawText(name_x, name_y, file_name)
            x += width + 100  # Adjusted to add more space between the boxes
class Ui_PythonApplication(object):
    def setupUi(self, PythonApplication):
         # Create a timer to periodically check for changes in the 'raw' folder
        self.update_timer = QTimer(PythonApplication)
        self.update_timer.timeout.connect(self.update_combo_box)
        self.update_timer.start(5000)  # Check every 5 seconds (adjust as needed)
        PythonApplication.setObjectName("PythonApplication")
        PythonApplication.resize(1124, 733)
        PythonApplication.setMinimumSize(QtCore.QSize(10, 50))
        self.centralwidget = QtWidgets.QWidget(PythonApplication)
        self.centralwidget.setObjectName("centralwidget")

        self.Container = QtWidgets.QGraphicsView(self.centralwidget)
        self.Container.setGeometry(QtCore.QRect(15, 500, 1350, 471))
        self.Container.setObjectName("Container")

 # Create a QGraphicsView and a QGraphicsSceneW
        self.Container_alert = QtWidgets.QGraphicsView(self.centralwidget)
        self.Container_alert.setGeometry(QtCore.QRect(1400, 500, 500, 471))
        self.Container_alert.setObjectName("Container_alert")
        self.scene = QtWidgets.QGraphicsScene()
        self.Container_alert.setScene(self.scene)
        

        # Create a QVBoxLayout to hold the alerts
        self.alert_layout = QtWidgets.QVBoxLayout()
        self.alert_layout.setContentsMargins(1, 1, 1, 1) 
        
        container_style = "QWidget#Container_alert { border: 2px solid black; }"
        self.Container_alert.setStyleSheet(container_style)
 # Adjust margins for spacing

            # Set the layout for the QGraphicsView
        container_widget = QWidget()
        container_widget.setLayout(self.alert_layout)
        self.scene.addWidget(container_widget)






        # self.Container_alert_head = QtWidgets.QGraphicsView(self.Container_alert)
        # self.Container_alert_head.setGeometry(QtCore.QRect(14010, 490, 200, 30))
        # self.Container_alert_head.setObjectName("Container_alert_head")

        # Calculate maximum opening for each file in 'raw' folder
        folder_path = os.path.join(os.path.dirname(__file__), 'raw')
        
        if os.path.exists(folder_path):
            max_opening_files = self.get_max_opening_per_file(folder_path)
            print("Files with maximum opening:")
            for file_name, max_opening in max_opening_files:
                print(f"{file_name}: {max_opening}")
        else:
            print("Error: 'raw' folder not found.")

        def get_latest_opening_per_file(folder_path):
            latest_opening_files = set()

            # Iterate over each file in the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                # Read data into DataFrame
                    df = pd.read_excel(file_path)  # Assuming the file is an Excel file, adjust if it's a different format
                    
                    df['Date'] = pd.to_datetime(df['Date'])
                    # Get the row with the latest date
                    latest_row = df.loc[df['Date'].idxmax()]
                    print(latest_row)
                    # Get the latest opening
                    latest_opening = latest_row['Closing']
                    print(latest_opening)
                    # Add file name and its latest opening to the set
                    latest_opening_files.add((file_name, latest_opening))
                print("Files with Latest opening:")
                for file_name, latest_opening in latest_opening_files:
                    print(f"{file_name}: {latest_opening}")
            return latest_opening_files
        
        self.latest_opening_files = get_latest_opening_per_file(folder_path)

        self.material_widget =  MaterialWidget(max_opening_files,self.latest_opening_files ,self.Container)
        self.material_widget.setGeometry(QtCore.QRect(0, 0, 1500, 471)) 


        self.Visual1 = QtWidgets.QFrame(self.centralwidget)
        self.Visual1.setGeometry(QtCore.QRect(700, 70, 561, 400))
        self.Visual1.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Visual1.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Visual1.setObjectName("Visual1")
        self.visual2 = QtWidgets.QFrame(self.centralwidget)
        self.visual2.setGeometry(QtCore.QRect(1300, 70, 561, 400))
        self.visual2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.visual2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.visual2.setObjectName("visual2")

        self.Visual1.setLayout(QtWidgets.QVBoxLayout())
        self.visual2.setLayout(QtWidgets.QVBoxLayout())
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)  # Add a combo box
        self.comboBox.setGeometry(QtCore.QRect(250, 350, 194, 35))
        self.comboBox.setObjectName("comboBox")
        self.populate_combo_box()
        self.comboBox.currentIndexChanged.connect(self.on_combo_box_changed)

        self.upload_button = QtWidgets.QPushButton(self.centralwidget)
        self.upload_button.setGeometry(QtCore.QRect(20, 350, 194, 35))
        self.upload_button.setObjectName("upload_button")
        self.upload_button.setText("Upload File")
        self.upload_button.clicked.connect(self.upload_file)
        def add_data(selected_date, data1, data2):
            # Get the selected date and data from the input boxes
            selected_date_str = selected_date.toString("yyyy-MM-dd")
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")

            # Set the time to 00:00:00
            selected_date_with_time = selected_date.replace(hour=0, minute=0, second=0)

            # Format the selected date with time
            selected_date_str = selected_date_with_time.strftime("%m/%d/%Y %H:%M:%S")
            selected_file = self.comboBox.currentText()
            print("Selected Date:", selected_date_str)
            print("Data 1:", data1)
            print("Data 2:", data2)
            print("selected_file 2:", selected_file)
            add_data_to_excel(selected_file,selected_date_str, data1 ,data2)
        def add_data_to_excel(file_name,selected_date_str, data1 ,data2 ):
            print("Came")

            folder_path = os.path.join(os.path.dirname(__file__), 'raw')  # Path to 'raw' folder

            # Construct the full file path
            file_path = os.path.join(folder_path, file_name)
            # Read existing data from the Excel file into a DataFrame
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                print("Came into Existing file")
            else:
                # If the file doesn't exist yet, create an empty DataFrame
                df = pd.DataFrame()
                print("Came into new file")
            # Convert the new data to a DataFrame
            new_opening = df['Closing'].iloc[-1].astype(float)
            print(type(new_opening))
            print(type(data1))
            print(type(data2))
            print(df.dtypes)
            Closing = (float(new_opening) + float(data1)) - float(data2)

            selected_date_str = pd.to_datetime(selected_date_str)
            print(type(selected_date_str))
            print(selected_date_str)
            print(Closing)
            new_data = {
            'Material':[None],
            'Date': [selected_date_str],
            'Opening': [new_opening],
            'Purchase': [data1],
            'Issues': [0],
            'Line_1': [0],
            'Line_2': [0],
            'Total': [data2],
            'moisture': [0],
            'percentage': [0],
            'Closing': [Closing]
            }
            my_handler_instance.pause_event.clear()
            # Convert the new data to a DataFrame

            new_df = pd.DataFrame(new_data)

            # Adjust the new data before appending
            # Here, you might need to modify the 'Opening', 'Closing', and other columns based on your requirements
      

            # Append the new data to the existing DataFrame
            df = pd.concat([df, new_df], ignore_index=True)

            # Write the concatenated DataFrame back to the Excel file
            df.to_excel(file_path, index=False)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText("Data Added Successfully")
            msg_box.setWindowTitle("Alert")
            msg_box.exec_()
            my_handler_instance.pause_event.set()
        def add_data_dialog():
            # Create a dialog window
            dialog = QtWidgets.QDialog()
            dialog.setWindowTitle("Add Data")
    
            # Create layout for the dialog
            layout = QtWidgets.QVBoxLayout(dialog)
    
            # Add calendar widget
            calendar = QtWidgets.QCalendarWidget()
            layout.addWidget(calendar)
    
            # Add input boxes for data
            input1 = QtWidgets.QLineEdit()
            input2 = QtWidgets.QLineEdit()
            layout.addWidget(QLabel("Purchase Quantity:"))
            layout.addWidget(input1)
            layout.addWidget(QLabel("Used Quantity:"))
            layout.addWidget(input2)
    
            # Add a button to confirm data addition
            confirm_button = QPushButton("Add")
            confirm_button.clicked.connect(lambda: add_data(calendar.selectedDate(), input1.text(), input2.text()))
            layout.addWidget(confirm_button)
    
            # Execute the dialog
            dialog.exec_()
        self.add_data_button = QPushButton("Add Data", self.centralwidget)
        self.add_data_button.setGeometry(500, 350, 194, 35) 
        self.add_data_button.clicked.connect(add_data_dialog)
        self.add_data_button.hide() 

        self.title_card = QtWidgets.QLabel(self.centralwidget)
        self.title_card.setGeometry(QtCore.QRect(10, 10, 721, 79))


        font = QtGui.QFont()
        font.setPointSize(24) 
        self.title_card.setFont(font)
        self.title_card.setObjectName("title_card")
        self.title_card.setText("Raw Material Predictive Model") 

        self.Opening = QtWidgets.QLabel(self.centralwidget)
        self.Opening.setGeometry(QtCore.QRect(40, 150, 101, 31))
        font = QtGui.QFont()
        font.setPointSize(10)  # Adjust font size to 18
        self.Opening.setFont(font)
        self.Opening.setObjectName("Opening")
        self.opening = QtWidgets.QLCDNumber(self.centralwidget)
        self.opening.setGeometry(QtCore.QRect(10, 210, 141, 71))
        self.opening.setObjectName("opening")
        self.Total_usuage = QtWidgets.QLabel(self.centralwidget)
        self.Total_usuage.setGeometry(QtCore.QRect(250, 150, 91, 31))
        font = QtGui.QFont()
        font.setPointSize(10) 
        self.Total_usuage.setFont(font)
        self.Total_usuage.setObjectName("Total_usuage")
        self.total = QtWidgets.QLCDNumber(self.centralwidget)
        self.total.setGeometry(QtCore.QRect(230, 210, 131, 71))
        self.total.setObjectName("total")
        self.predicted_days = QtWidgets.QLCDNumber(self.centralwidget)
        self.predicted_days.setGeometry(QtCore.QRect(420, 210, 131, 71))
        self.predicted_days.setObjectName("predicted_days")
        self.Predicted_days = QtWidgets.QLabel(self.centralwidget)
        self.Predicted_days.setGeometry(QtCore.QRect(440, 150, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.Predicted_days.setFont(font)
        self.Predicted_days.setObjectName("Predicted_days")
        self.Opening_2 = QtWidgets.QLabel(self.centralwidget)
        self.Opening_2.setGeometry(QtCore.QRect(110, 220, 371, 31))
        self.Opening_2.setObjectName("Opening_2")
        self.LCD_value_link = QtWidgets.QLabel(self.centralwidget)
        self.LCD_value_link.setGeometry(QtCore.QRect(440, 220, 371, 31))
        self.LCD_value_link.setObjectName("LCD_value_link")
        PythonApplication.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(PythonApplication)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1124, 21))
        self.menubar.setObjectName("menubar")
        self.menuPredictive_Model = QtWidgets.QMenu(self.menubar)
        self.menuPredictive_Model.setObjectName("menuPredictive_Model")
        PythonApplication.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(PythonApplication)
        self.statusbar.setObjectName("statusbar")
        PythonApplication.setStatusBar(self.statusbar)

        # self.update_timer = QTimer(PythonApplication)
        # self.update_timer.timeout.connect(self.update_contents)
        # self.update_timer.start(5000)  # Check every 5 seconds

        self.retranslateUi(PythonApplication)
        QtCore.QMetaObject.connectSlotsByName(PythonApplication)

        PythonApplication.showMaximized()
        self.check_raw_materials()
        low_materials, restock_info = self.check_raw_materials_for_limit()

# Print low materials and restock information
        print("Low Materials:")
        for material in low_materials:
            print(material)

        print("\nRestock Information:")
        for material, info in restock_info.items():
            print(f"Material: {material}")
            print(f"Average Opening: {info['average_opening']}")
            print(f"Lowest Opening: {info['lowest_opening']}")
            print(f"Terminal Level: {info['terminal_level']}")
            print(f"Latest Opening: {info['latest_opening']}")
            print(f"Restock Time: {info['restock_time']}")
            if info['restock_time'] == "Immediate":
                self.add_alert(self.alert_layout, f"Material Name: {material} is low on stock , Please restock soon..")

    def add_alert(self,container,message):
        # Create spacers for top and bottom margins
        top_margin = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        bottom_margin = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # Add the spacers to the layout
        self.alert_layout.addItem(top_margin)

        # Create and style the QLabel
        alert_label = QtWidgets.QLabel(message)
        alert_label.setStyleSheet("color: black; font-weight: bold; padding-top: 50px; text-align: left; word-wrap: break-word;")

        # Add the QLabel to the layout
        self.alert_layout.addWidget(alert_label)

        # Add bottom margin
        self.alert_layout.addItem(bottom_margin)


    def check_raw_materials(self):
        # Path to the folder containing raw materials files
        ####################################################################################IMPORTANT LINE FOR EXE###################################################################
        # folder_path = os.path.join(os.path.dirname(sys.executable),'raw')  # Path to 'raw' folder
        folder_path = os.path.join(os.path.dirname(__file__), 'raw')
        # Iterate over each file in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                # Check if the opening data for the past 30 days is unchanged for the current file
                not_used_recently = check_last_30_days(file_path)
                print("Checking for not used")
                # If the opening data is unchanged, display a notification
                if not_used_recently:
                    # self.show_notification(f"The opening for '{file_name}' has not been used or changed in the past 30 days.")
                    print("Not used Recently "f'{file_name}')
                    self.add_alert(self.alert_layout,f"Material :{file_name} is not used for past 30 Days ")
        
    def populate_combo_box(self):
        folder_path = os.path.join(os.path.dirname(__file__), 'raw')  # Path to 'raw' folder
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)  # Get list of file names in 'raw' folder
            self.comboBox.addItems(files)  # Add file names to combo box
        else:
            print("Error: 'raw' folder not found.")
    def update_contents(self):
         # Calculate maximum opening for each file in 'raw' folder
        folder_path = os.path.join(os.path.dirname(__file__), 'raw')
        if os.path.exists(folder_path):
            max_opening_files = self.get_max_opening_per_file(folder_path)
            self.material_widget.update_data(max_opening_files)
            print("Files with maximum opening:")
            for file_name, max_opening in max_opening_files:
                print(f"{file_name}: {max_opening}")
        else:
            print("Error: 'raw' folder not found.")

    def on_combo_box_changed(self, index):
        selected_file = self.comboBox.currentText()  
        self.add_data_button.show() # Get the selected file name
        self.process_selected_file(selected_file)  # Call function with selected file name
        
    def check_raw_materials_for_limit(self):
        folder_path = os.path.join(os.path.dirname(__file__), 'raw')  # Path to 'raw' folder
        low_materials = []
        restock_info = {}

        # Iterate over each file in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
            # Read data into DataFrame
                df = pd.read_excel(file_path)

            # Calculate average opening and lowest opening
                average_opening = df['Closing'].mean()
                lowest_opening = df['Closing'].min()

            # Calculate terminal level
                terminal_level = average_opening * 0.6

            # Check if the current or latest data is below the terminal level
                latest_opening = df['Closing'].iloc[-1]  # Assuming the last row contains the latest data
                if latest_opening < terminal_level:
                    low_materials.append(file_name)

            # Determine how soon to restock the raw material
                restock_time = "Immediate" if latest_opening < terminal_level else "Normal"

            # Store restock information
                restock_info[file_name] = {
                "average_opening": average_opening,
                "lowest_opening": lowest_opening,
                "terminal_level": terminal_level,
                "latest_opening": latest_opening,
                "restock_time": restock_time
                }  
        return low_materials, restock_info
               
    def process_selected_file(self, file_name):
        folder_path = os.path.join(os.getcwd(), 'raw')  # Get directory of main.py
        file_path = os.path.join(folder_path, file_name)  # Concatenate with file name
        print("Selected file path:", file_path)
        self.predicting_for_selected_material(file_path)
    def get_max_opening_per_file(self, folder_path):
        max_opening_files = set()

        # Iterate over each file in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                print(file_path)
               
                # Read data into DataFrame
                df = pd.read_excel(file_path)  # Assuming the file is an Excel file, adjust if it's a different format

                # Calculate maximum opening
                max_opening = df['Closing'].max()

                # Add file name and its maximum opening to the set
                max_opening_files.add((file_name, max_opening))

        return max_opening_files
    def update_combo_box(self):
        folder_path = os.path.join(os.getcwd(), 'raw')  # Path to 'raw' folder
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)  # Get list of file names in 'raw' folder
            current_items = [self.comboBox.itemText(i) for i in range(self.comboBox.count())]
            new_items = set(files) - set(current_items)
            removed_items = set(current_items) - set(files)
            print("Checking for Updates..")
            for item in new_items:
                self.comboBox.addItem(item)


            for item in removed_items:
                index = self.comboBox.findText(item)
                self.comboBox.removeItem(index)
            
        else:
            print("Error: 'raw' folder not found.")
    def retranslateUi(self, PythonApplication):
        _translate = QtCore.QCoreApplication.translate

        PythonApplication.setWindowTitle(_translate("PythonApplication", "Raw Material Prediction"))

        self.title_card.setText(_translate("PythonApplication", "Predictive Model"))
        self.Opening.setText(_translate("PythonApplication", "Opening"))
        self.Total_usuage.setText(_translate("PythonApplication", "Usuage"))
        self.Predicted_days.setText(_translate("PythonApplication", "Predicted Days"))
        self.menuPredictive_Model.setTitle(_translate("PythonApplication", "File"))

    def upload_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(None, "Upload File", "", "All Files (*);;Python Files (*.py)", options=options)
        if file_path:
            print("Selected File:", file_path)
            df = pd.read_excel(file_path)
            #Lets start the Files Creation process here :
            df = df.iloc[3:].reset_index(drop=True)
            df.drop(df.columns[4:7], axis=1, inplace=True)
            df.columns = range(df.shape[1])
            new_columns = {
        0: 'Material',
        1: 'Date',
        2: 'Opening',
        3: 'Purchase',
        4: 'Issues',
        5: 'Line_1',
        6: 'Line_2',
        7: 'Total',
        8: 'moisture',
        9: 'percentage',
        10: 'Closing'
    }
            df.rename(columns=new_columns, inplace=True)


            #-------------------===================================================------------------------------------------------------------
            # Assuming df is your DataFrame
            # Iterate over the DataFrame to find the starting and ending indices
            material_indices = []
            start_index = None
            print("Iteraring")
            for index, row in df.iterrows():
                print("Iteraring")
                # If the value in the first column is not NaN, it's a material name
                if not pd.isnull(row[0]):
                    # If this is the first material name encountered
                    if start_index is None:
                        start_index = index
                        print("Start Index at " , index)
                    # If it's NaN and we have a start index, it's the end of a material section
                    elif start_index is not None:
                        material_indices.append((start_index, index - 1))
                        print("End Index at " , index-1)
                        start_index = index

            # Check from the last row index -2 for the last material section
            if start_index is not None:
                material_indices.append((start_index, df.index[-2]))

            #-------------------===================================================------------------------------------------------------------

            
            for i in material_indices:
                print(i)
            #-------------------===================================================------------------------------------------------------------
            # Create Excel files for each set of material names along with their subheadings
            for start, end in material_indices:
                material_name = df.iloc[start, 0]  # Get the material name
                material_data = df.iloc[start:end+1]  # Get data for the material section

                print(f"Material Name: {material_name}")
                print(f"Material Data:\n{material_data}")

                raw_folder_path = os.path.join(os.getcwd(), 'raw')  # Path to 'raw' folder

# Ensure that the 'raw' folder exists
                if not os.path.exists(raw_folder_path):
                    os.makedirs(raw_folder_path)

# Modify the file path to include the 'raw' folder
                # excel_file = os.path.join(raw_folder_path, f"{material_name}.xlsx")
# Modify the file path to include the 'raw' folder
                excel_file = os.path.join(raw_folder_path, f"{material_name}.xlsx")
                # Create Excel writer object
                # excel_file = f"{material_name}.xlsx"
                print(f"Creating Excel file: {excel_file}")
                with pd.ExcelWriter(excel_file) as writer:
                    # Write data to Excel file
                    df.iloc[start:end+1].to_excel(writer, index=False, header=True)
                    print(f"Data written to {excel_file}")

                # Print confirmation message
                print("Data saved into Excel files.")
    

    def predicting_for_selected_material(self,filename):
        df = pd.read_excel(filename)
        df.drop([df.index[0]] + list(df.index[-1:]))
        df.drop('Material', axis=1)

         # Find the most recent data with non-zero usage
        last_non_zero_data = df[df['Total'] > 0]
        if not last_non_zero_data.empty:
            df = last_non_zero_data
        #-------------------===================================================------------------------------------------------------------
        print("-------------------================================DF===================------------------------------------------------------------")
        print(df)
        print("-------------------================================DF===================------------------------------------------------------------")
            # End of the File Creatio Process here
        max_opening = df['Closing'].max()
        df['Date'] = pd.to_datetime(df['Date'])
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,------------------------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,-------------------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,---------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,----------------------------------")
        print(df['Date'])
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,------------------------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,-------------------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,---------------------------------------------")
        print("-------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<,----------------------------------")
        last_6_months = df[df['Date'] >= df['Date'].max() - pd.DateOffset(months=10)].copy()
        print("-------------------================================Last 6 Month===================------------------------------------------------------------")
        print(last_6_months)
        print("-------------------================================Last 6 Month===================------------------------------------------------------------")
        for i in range(1, 22): 
            last_6_months[f'Total_lag_{i}'] = last_6_months['Total'].shift(i)

            # last_6_months['Zero_consumption_for_last_3_days'] = (last_6_months['Total'].rolling(window=3).sum() == 0).astype(int)

            # last_6_months.dropna(inplace=True)
        print("-------------------================================Last 6 Month AFter Drop NA===================------------------------------------------------------------")
        print(last_6_months)
        print("-------------------================================Last 6 Month After Drop NA===================------------------------------------------------------------")
        X = last_6_months.drop(['Date', 'Total','Material'], axis=1)  
        print("X is as follows : ",X)
        y = last_6_months['Total'] 
        print("Y is as the Follows :", y)

        model = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.1, random_state=42)
        model.fit(X, y)

        if last_6_months.iloc[-1]['Total'] > 0:
            last_day_features = X.tail(1) 
            predicted_total = model.predict(last_day_features)
        else:
            last_week_features = X.tail(1) 
            predicted_total = "Negative or zero consumption, cannot predict"

        if isinstance(predicted_total, np.ndarray) and predicted_total[0] > 0:
            days_stock_enough = last_6_months.iloc[-1]['Closing'] / predicted_total
        else:
            days_stock_enough = "Unknown"

        self.opening.display(last_6_months.iloc[-1]['Closing']) 
        self.total.display(predicted_total[0] if isinstance(predicted_total, np.ndarray) and predicted_total[0] > 0 else 0) 
        self.predicted_days.display(int(days_stock_enough[0]) if isinstance(days_stock_enough, np.ndarray) else 0) 

        print("Predicted Total Stock Consumption:", predicted_total[0] if isinstance(predicted_total, np.ndarray) and predicted_total[0] > 0 else "Negative or zero consumption, cannot predict")
        print("This is Maximum:",max_opening)
        high_factor = 0.3
        low_factor = 0.3

        if isinstance(predicted_total, np.ndarray) and predicted_total[0] > 0:
            high_prediction = predicted_total * (1 + high_factor)
            low_prediction = predicted_total * (1 - low_factor)
        else:
            high_prediction = "Unknown"
            low_prediction = "Unknown"

        print(f"High Prediction: {high_prediction[0]}" if isinstance(high_prediction, np.ndarray) and high_prediction[0] > 0 else "Unknown")
        print(f"Low Prediction: {low_prediction[0]}" if isinstance(low_prediction, np.ndarray) and low_prediction[0] > 0 else "Unknown")
        print(f"The opening stock is: {last_6_months.iloc[-1]['Closing']}")
        if isinstance(high_prediction, np.ndarray) and high_prediction[0] > 0:
            days_high_stock_enough = last_6_months.iloc[-1]['Closing'] / high_prediction
        else:
            days_high_stock_enough = "Unknown"

        if isinstance(low_prediction, np.ndarray) and low_prediction[0] > 0:
            days_low_stock_enough = last_6_months.iloc[-1]['Closing'] / low_prediction
        else:
            days_low_stock_enough = "Unknown"
        def convert_to_weeks_or_months(days):
            if days >= 30:
                months = int(days/30)
                remaining_days = days % 30
                if remaining_days > 0:
                    if remaining_days >= 7:
                        weeks = int(remaining_days/7)
                        return f"{months} {'month' if months == 1 else 'months'} and {weeks} {'week' if weeks == 1 else 'weeks'}"
                    else:
                        return f"{months} {'month' if months == 1 else 'months'}"
                else:
                    return f"{months} {'month' if months == 1 else 'months'}"
            elif days >= 7:
                weeks = int(days/7)
                return f"{weeks} {'week' if weeks == 1 else 'weeks'}"
            else:
                return f"{int(days)} {'day' if int(days) == 1 else 'days'}"
        days_stock_enough = convert_to_weeks_or_months(days_stock_enough[0]) if isinstance(days_stock_enough, np.ndarray) else days_stock_enough
        days_high_stock_enough = convert_to_weeks_or_months(days_high_stock_enough[0]) if isinstance(days_high_stock_enough, np.ndarray) else days_high_stock_enough
        days_low_stock_enough = convert_to_weeks_or_months(days_low_stock_enough[0]) if isinstance(days_low_stock_enough, np.ndarray) else days_low_stock_enough

        print(f"The stock will last for approximately {days_stock_enough}.")
        print(f"High Consumption will last for approximately {days_high_stock_enough}.")
        print(f"Low Prediction will last for approximately {days_low_stock_enough}.")

        print("\nDetails of last 3 days:")
        last_3_days = last_6_months.tail(3)
        print(last_3_days)

            # total_last_30_days = df.set_index('Date')['Total'].rolling(window=30).sum().dropna()

            # total_last_7_days = df.set_index('Date')['Total'].rolling(window=7).sum().dropna()
        last_30_days_opening = df.set_index('Date').tail(305)['Closing']
        last_7_days_opening = df.set_index('Date').tail(30)['Closing']
            # Read data into DataFrame
        df1 = pd.read_excel(filename)

        # Find the latest date available in the 'Date' column
        last_30_days_opening = df1.set_index('Date').tail(305)['Closing']
        last_7_days_opening = df1.set_index('Date').tail(30)['Closing']

        print(last_7_days_opening)

        fig, ax = plt.subplots(figsize=(10, 5)) 
        ax.bar(last_30_days_opening.index, last_30_days_opening.values, color='green')
        ax.set_title('Availability of Last 10 Months')
        ax.grid(True)
        ax.set_xticks([]) 
        self.plot_to_qgraphicsview(fig, self.Visual1)

        fig2, ax2 = plt.subplots(figsize=(4, 2))  
        ax2.plot(last_7_days_opening.index, last_7_days_opening.values, color='red')
        ax2.set_title('Availability of Last 30 Days')
        ax2.grid(True)
        ax2.set_xticks([])  
        self.plot_to_qgraphicsview(fig2, self.visual2)

    def plot_to_qgraphicsview(self, fig, graphics_view):
        if graphics_view.layout():
            for i in reversed(range(graphics_view.layout().count())):
                graphics_view.layout().itemAt(i).widget().setParent(None)

        canvas = FigureCanvas(fig)
        layout = graphics_view.layout()  
        layout.addWidget(canvas)
        canvas.draw()
def start_observer():
    # Start the observer
    observer = Observer()
    raw_folder_path = os.path.join(os.getcwd(), 'raw')
    observer.schedule(MyHandler(), path=raw_folder_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    PythonApplication = QtWidgets.QMainWindow()
    ui = Ui_PythonApplication()
    ui.setupUi(PythonApplication)
    # Convert logo image to QIcon object
    icon = QIcon("x_logo.ico")
    # Set window icon
    PythonApplication.setWindowIcon(icon)
    observer_thread = threading.Thread(target=start_observer)
    observer_thread.daemon = True
    observer_thread.start()
    PythonApplication.show()
    my_handler_instance = MyHandler()
    sys.exit(app.exec_())
