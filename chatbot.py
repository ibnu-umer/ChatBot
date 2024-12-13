from PyQt6.QtWidgets import  (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QLineEdit, QScrollArea,
    QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSlot, pyqtSignal, QMetaObject
import sys
import textwrap
import google.generativeai as genai
from api_key import API_KEY
import threading






class MainWindow(QMainWindow):
    
    response_received = pyqtSignal(str) 
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(700, 500)
        self.setWindowTitle('ChatBot')
        
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        self.response_received.connect(self.create_response_msg_widget)
        
        # main layout to contain heading, messages display area and input area
        main_layout = QVBoxLayout()
        
        # main heading of the page
        heading = QLabel('How can I help you ?')
        heading.setObjectName('heading')
        main_layout.addWidget(heading)
        
        # Message display area
        container = QWidget()
        self.container_layout = QVBoxLayout()
        container.setLayout(self.container_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(container)
        main_layout.addWidget(self.scroll_area)
        
        # Spacer to push the messages to down
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.container_layout.addItem(self.spacer)
        
        # Message input area with sent button
        input_area_layout = QHBoxLayout()
        self.input_area = QLineEdit(placeholderText='Ask your assistant...')
        self.input_area.setObjectName('input')
        self.input_area.setFixedHeight(40)
        input_area_layout.addWidget(self.input_area)
        
        self.sent_btn = QPushButton()
        self.sent_btn.setIcon(QIcon('sent.png'))
        self.sent_btn.setIconSize(QSize(20,20))
        self.sent_btn.setFixedSize(40, 40)
        self.sent_btn.clicked.connect(self.get_msg_from_user)
        input_area_layout.addWidget(self.sent_btn)
        main_layout.addLayout(input_area_layout)
        
        
        # Central widget and layout setup
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        
        self.setStyleSheet('''
                #heading{
                    font-size: 22px;
                    font-weight: bold;
                }
                #input{
                    font-size: 13px;
                }
        ''')
        
    
    def get_response(self, message):
        try:
            response = self.model.generate_content(message)
            self.response_received.emit(response.text)  
        except Exception as e:
            self.response_received.emit(f"Error: {str(e)}")  # Emit an error message
        finally:
            self.input_area.setDisabled(False)
            self.sent_btn.setDisabled(False)
            
    
    @pyqtSlot(str)
    def create_response_msg_widget(self, response):
        msg_widget = MsgWidget(response, responser='bot')
        self.container_layout.addWidget(msg_widget)
        
        
        
    def get_msg_from_user(self):
        msg = self.input_area.text()
        # To avoid empty messages
        if msg:
            self.input_area.clear()
            self.input_area.setDisabled(True)
            self.sent_btn.setDisabled(True)
            msg_widget = MsgWidget(msg, responser='user')
            self.container_layout.addWidget(msg_widget) # Add the message label to the message display area
            
            threading.Thread(target=self.get_response, args=(msg, )).start()
        
        

class MsgWidget(QWidget):
    def __init__(self, msg, responser='bot'):
        super().__init__()
        self.setMinimumHeight(40)
        self.message = msg
        
        layout = QHBoxLayout()
        icon = QPixmap('bot.png')
        icn_label = QLabel()
        icn_label.setFixedSize(25, 25)
        icn_label.setPixmap(icon)
        
        self.msg_container = QWidget()
        self.msg_container.setObjectName('msg_widget')
        msg_widget_color = 'lightblue' if responser == 'bot' else 'lightgray'
        self.msg_container.setStyleSheet(f'background-color: {msg_widget_color}; font-size: 14px; border-radius: 15px;')
        self.msg_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.msg_container_layout = QVBoxLayout()
        self.msg_container_layout.setContentsMargins(15, 15, 15, 15)
        self.msg_container.setLayout(self.msg_container_layout)
        
        self.msg_label = QLabel('', self.msg_container)
        self.msg_label.setObjectName('messageLabel')
        self.msg_container_layout.addWidget(self.msg_label)
        
        if responser == 'bot':
            # Add the icon first
            icon = QPixmap('bot.png')
            layout.addWidget(icn_label)
            # And the message box
            layout.addWidget(self.msg_container)
        
        else:
            layout.addWidget(self.msg_container)
            icon = QPixmap('profile.png')
            layout.addWidget(icn_label)
            
        icn_label.setPixmap(icon)
            

        self.setStyleSheet('''
                #messageLabel{
                    background-color: transparent;
                    font-family: roboto;
                    font-size: 14px;
                }      
        ''')
        
        self.setLayout(layout)
        
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        available_width = self.width() - 50  
        self.msg_container.setFixedWidth(available_width)
        max_line_width = available_width // self.fontMetrics().averageCharWidth()
        max_line_width = int(max_line_width - (max_line_width / 3) + 5) 
        wrapped_msg = textwrap.fill(self.message, width=max_line_width)
        self.msg_label.setText(wrapped_msg)
    
    



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())