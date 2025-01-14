from PyQt6.QtWidgets import  (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea,
    QPushButton, QSpacerItem, QSizePolicy, QTextEdit, QTextBrowser
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSlot, pyqtSignal, QEvent
import sys
import google.generativeai as genai
from api_key import API_KEY
import threading
import re





class MainWindow(QMainWindow):
    
    response_received = pyqtSignal(str) 
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(700, 500)
        self.setWindowTitle('ChatBot')
        self.setWindowIcon(QIcon('robot.png'))
        
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
        self.input_area = CustomTextEdit(self)
        self.input_area.setPlaceholderText('Ask your assistant...')
        self.input_area.setObjectName('input')
        self.input_area.setMaximumHeight(40)
        input_area_layout.addWidget(self.input_area)
        
        self.sent_btn = QPushButton()
        self.sent_btn.setIcon(QIcon('sent.png'))
        self.sent_btn.setIconSize(QSize(20,20))
        self.sent_btn.setFixedSize(40, 40)
        self.sent_btn.setToolTip('Sent message. shortcut : shift+enter')
        self.sent_btn.clicked.connect(self.get_msg_from_user)
        input_area_layout.addWidget(self.sent_btn)
        main_layout.addLayout(input_area_layout)
        
        self.installEventFilter(self)
        
        
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
                    font-size: 14px;
                    padding: 15px;
                    padding-top: 6px;
                    padding-bottom: 0px;
                }
                
        ''')
        
    
    def get_response(self, message):
        try:
            response = self.model.generate_content(message)
            html_text = self.convert_to_html(response.text)
            self.response_received.emit(html_text)  
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
        msg = self.input_area.toPlainText()
        # To avoid empty messages
        if msg:
            self.input_area.clear()
            self.input_area.setDisabled(True)
            self.sent_btn.setDisabled(True)
            msg_widget = MsgWidget(msg, responser='user')
            self.container_layout.addWidget(msg_widget) # Add the message label to the message display area
            
            threading.Thread(target=self.get_response, args=(msg, )).start()
        
        
    
    def convert_to_html(self, markdown_text):
        # Convert **bold** to <b>bold</b>
        html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', markdown_text)
        
        # Convert *italic* to <i>italic</i>
        html_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html_text)
        
        # Replace newlines (\n) with <br> for line breaks
        html_text = html_text.replace('\n', '<br>')
        
        return html_text
        
        
        
    def eventFilter(self, obj, event):
        # Check if the event is a key press
        if event.type() == QEvent.Type.KeyPress:
            if obj is self:  # If the key press is in the main window and not inside QTextEdit
                # If QTextEdit does not have focus, set focus to QTextEdit
                if not self.input_area.hasFocus():
                    self.input_area.setFocus()  # Activate the QTextEdit

                # Insert the character of the pressed key into QTextEdit
                key_event = event  # Capture the key event
                key = key_event.text()  # Get the character corresponding to the key pressed

                # Insert the character into the QTextEdit at the cursor position
                cursor = self.input_area.textCursor()
                cursor.insertText(key)  # Insert the character

            return True  # Return True to stop further event propagation

        # If it's not a key event, continue normal event processing
        return super().eventFilter(obj, event)
        
        

class CustomTextEdit(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMaximumHeight(100)

        # Connect the sizeChanged signal to update height
        self.document().contentsChanged.connect(self.adjust_height)


    def adjust_height(self):
        doc_height = self.document().size().height()
        if doc_height < 150:  
            self.setFixedHeight(int(doc_height + 10))  # Add some padding      
            
    
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        # Check for Shift + Enter combination
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Return:
            self.parent.get_msg_from_user()  
        else:
            # Let the default behavior occur for other keys
            super().keyPressEvent(event)


        

class MsgWidget(QWidget):
    def __init__(self, msg, responser='bot'):
        super().__init__()
        self.message = msg
        
        layout = QHBoxLayout()
        icn_layout = QVBoxLayout()
        icn_layout.setContentsMargins(0, 15, 0, 15)
        icn_label = QLabel()
        icn_label.setFixedSize(25, 25)
        
        icn_layout.addWidget(icn_label)
        icn_layout.addStretch() # to push the icon to the top
        
        self.msg_container = QWidget()
        self.msg_container.setObjectName('msg_widget')
        msg_widget_color = 'lightblue' if responser == 'bot' else 'lightgray'
        self.msg_container.setStyleSheet(f'background-color: {msg_widget_color}; font-size: 14px; border-radius: 15px;')
        self.msg_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.msg_container_layout = QVBoxLayout()
        self.msg_container_layout.setContentsMargins(15, 15, 15, 15)
        self.msg_container.setLayout(self.msg_container_layout)
        
        self.text_browser = CustomTextBrowser()
        self.text_browser.setObjectName('messageLabel')
        self.msg_container_layout.addWidget(self.text_browser)
        
        if responser == 'bot':
            # Add the icon first
            icon = QPixmap('bot.png')
            layout.addLayout(icn_layout)
            # And the message box
            layout.addWidget(self.msg_container)
        
        else:
            layout.addWidget(self.msg_container)
            icon = QPixmap('profile.png')
            layout.addLayout(icn_layout)
            
        icn_label.setPixmap(icon)
            

        self.setStyleSheet('''
                #messageLabel{
                    color: #000000;
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
        self.text_browser.setHtml(self.message)
    
    
    
    
class CustomTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)
        # Disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setOpenExternalLinks(True)
        
        # Monitor content changes to adjust height
        self.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self):
        doc_height = self.document().size().height()
        self.setFixedHeight(int(doc_height)) 




if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())