"""
Desktop UI for StudyBuddy conversational agent.
"""

import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, 
                           QVBoxLayout, QWidget, QLabel, QSlider, QHBoxLayout,
                           QComboBox, QMessageBox, QFileDialog, QTabWidget,
                           QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import time
import os

from conversational_agent import ConversationalAgent
from document_processor import DocumentProcessor

class SignalEmitter(QObject):
    """Signal emitter for thread-safe UI updates"""
    text_update = pyqtSignal(str, str)
    speaking_status = pyqtSignal(bool)
    listening_status = pyqtSignal(bool)
    audio_level = pyqtSignal(float)
    error_message = pyqtSignal(str)

class AudioVisualizer(FigureCanvas):
    """Visualizer for audio input/output levels"""
    def __init__(self, parent=None, width=5, height=1, dpi=100):
        plt.style.use('dark_background')
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super(AudioVisualizer, self).__init__(fig)
        self.setParent(parent)
        
        # Initial empty plot
        self.x = np.linspace(0, 100, 100)
        self.y = np.zeros(100)
        self.line, = self.ax.plot(self.x, self.y, '-', lw=2, color='cyan')
        
        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0, 100)
        self.ax.axis('off')
        fig.tight_layout(pad=0)
        fig.patch.set_alpha(0.0)

    def update_plot(self, level):
        """Update the audio level visualization"""
        # Shift values left
        self.y[:-1] = self.y[1:]
        # Add new value
        self.y[-1] = min(level * 5, 1.0)  # Scale up for better visibility
        self.line.set_ydata(self.y)
        self.draw()

class ConversationalAgentUI(QMainWindow):
    """Main UI class for StudyBuddy"""
    def __init__(self):
        super().__init__()
        
        # Set dark theme
        self.set_dark_theme()
        
        # Initialize signals
        self.signals = SignalEmitter()
        
        # Initialize document processor
        self.document_processor = DocumentProcessor()
        
        # Create UI elements
        self.init_ui()
        
        # Set up signal connections
        self.setup_signal_connections()
        
        # Initialize agent in a separate thread
        self.agent = None
        self.agent_thread = None
        self.is_running = False
        self.init_agent()
        
        # Timer for updating audio level visualization
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_audio_level)
        self.timer.start(50)

    def set_dark_theme(self):
        """Apply dark theme to the application"""
        dark_palette = QPalette()
        
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.yellow)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.black)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('StudyBuddy')
        self.setGeometry(100, 100, 900, 700)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # App title
        title_label = QLabel("StudyBuddy")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 20, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Chat tab
        chat_tab = QWidget()
        chat_layout = QVBoxLayout()
        
        # Conversation history
        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setFont(QFont('Arial', 12))
        chat_layout.addWidget(self.conversation)
        
        # Audio visualizer
        self.visualizer = AudioVisualizer(self, width=5, height=1)
        chat_layout.addWidget(self.visualizer)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont('Arial', 10))
        chat_layout.addWidget(self.status_label)
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # TTS Engine selector
        tts_layout = QVBoxLayout()
        tts_label = QLabel("TTS Engine:")
        self.tts_selector = QComboBox()
        self.tts_selector.addItem("Auto-detect")
        self.tts_selector.addItem("Coqui TTS")
        self.tts_selector.addItem("System TTS")
        tts_layout.addWidget(tts_label)
        tts_layout.addWidget(self.tts_selector)
        controls_layout.addLayout(tts_layout)
        
        # Button controls
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Start Conversation")
        self.start_button.clicked.connect(self.toggle_conversation)
        button_layout.addWidget(self.start_button)
        
        controls_layout.addLayout(button_layout)
        
        chat_layout.addLayout(controls_layout)
        
        chat_tab.setLayout(chat_layout)
        
        # Study tab
        study_tab = QWidget()
        study_layout = QVBoxLayout()
        
        # Document panel
        doc_layout = QHBoxLayout()
        
        # Document list
        doc_list_layout = QVBoxLayout()
        doc_list_label = QLabel("Documents:")
        self.document_list = QListWidget()
        self.document_list.itemClicked.connect(self.select_document)
        
        upload_button = QPushButton("Upload Document")
        upload_button.clicked.connect(self.upload_document)
        
        doc_list_layout.addWidget(doc_list_label)
        doc_list_layout.addWidget(self.document_list)
        doc_list_layout.addWidget(upload_button)
        
        # Document content
        doc_content_layout = QVBoxLayout()
        doc_content_label = QLabel("Content:")
        self.document_content = QTextEdit()
        self.document_content.setReadOnly(True)
        
        doc_content_layout.addWidget(doc_content_label)
        doc_content_layout.addWidget(self.document_content)
        
        # Add to document panel
        doc_layout.addLayout(doc_list_layout, 1)
        doc_layout.addLayout(doc_content_layout, 3)
        
        # Study controls
        study_controls = QHBoxLayout()
        
        self.quiz_button = QPushButton("Generate Questions")
        self.quiz_button.clicked.connect(self.generate_questions)
        self.quiz_button.setEnabled(False)
        
        self.discuss_button = QPushButton("Discuss Document")
        self.discuss_button.clicked.connect(self.discuss_document)
        self.discuss_button.setEnabled(False)
        
        study_controls.addWidget(self.quiz_button)
        study_controls.addWidget(self.discuss_button)
        
        # Questions and answers section
        qa_label = QLabel("Questions:")
        self.qa_display = QTextEdit()
        self.qa_display.setReadOnly(True)
        
        # Add all to study layout
        study_layout.addLayout(doc_layout)
        study_layout.addLayout(study_controls)
        study_layout.addWidget(qa_label)
        study_layout.addWidget(self.qa_display)
        
        study_tab.setLayout(study_layout)
        
        # Add tabs to the tab widget
        self.tab_widget.addTab(chat_tab, "Chat")
        self.tab_widget.addTab(study_tab, "Study")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Welcome message
        self.conversation.append("<b>StudyBuddy:</b> Welcome! Click 'Start Conversation' to begin.")
        
    def setup_signal_connections(self):
        """Connect signals for thread-safe UI updates"""
        self.signals.text_update.connect(self.update_conversation)
        self.signals.speaking_status.connect(self.update_speaking_status)
        self.signals.listening_status.connect(self.update_listening_status)
        self.signals.audio_level.connect(self.visualizer.update_plot)
        self.signals.error_message.connect(self.show_error)
        
    def init_agent(self):
        """Initialize the conversational agent in a background thread"""
        def agent_init_thread():
            try:
                use_tts = self.tts_selector.currentIndex() != 2  # Not System TTS
                self.agent = ConversationalAgent(use_tts=use_tts)
                self.status_label.setText("Ready")
                self.start_button.setEnabled(True)
            except Exception as e:
                self.signals.error_message.emit(f"Error initializing agent: {str(e)}")
                
        self.status_label.setText("Initializing models...")
        self.start_button.setEnabled(False)
        
        # Start initialization in background
        init_thread = threading.Thread(target=agent_init_thread)
        init_thread.daemon = True
        init_thread.start()
    
    def update_conversation(self, speaker, text):
        """Update the conversation history with new text"""
        if speaker == "user":
            self.conversation.append(f"<b>You:</b> {text}")
        else:
            self.conversation.append(f"<b>StudyBuddy:</b> {text}")
        
        # Auto-scroll to the bottom
        scroll_bar = self.conversation.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
    def update_speaking_status(self, is_speaking):
        """Update UI to reflect speaking status"""
        if is_speaking:
            self.status_label.setText("Speaking...")
        elif self.agent and self.agent.is_listening:
            self.status_label.setText("Listening...")
        else:
            self.status_label.setText("Ready")
    
    def update_listening_status(self, is_listening):
        """Update UI to reflect listening status"""
        if is_listening:
            self.status_label.setText("Listening...")
        elif self.agent and self.agent.is_speaking:
            self.status_label.setText("Speaking...")
        else:
            self.status_label.setText("Ready")
    
    def update_audio_level(self):
        """Update the audio level visualization"""
        if self.agent and hasattr(self.agent, 'current_audio_level'):
            level = self.agent.current_audio_level
            self.signals.audio_level.emit(level)
        else:
            self.signals.audio_level.emit(0)
            
    def toggle_conversation(self):
        """Start or stop the conversation"""
        if not self.is_running:
            self.start_conversation()
        else:
            self.stop_conversation()
    
    def start_conversation(self):
        """Begin the conversation loop"""
        self.is_running = True
        self.start_button.setText("Stop Conversation")
        
        # Define the agent thread function
        def agent_thread_func():
            try:
                # Welcome message
                welcome_msg = "Hello! I'm your study buddy. How can I help you today?"
                self.signals.text_update.emit("agent", welcome_msg)
                self.agent.speak(welcome_msg)
                
                while self.is_running:
                    self.signals.listening_status.emit(True)
                    user_input = self.agent.listen(timeout=10)
                    if not user_input or not self.is_running:
                        continue
                        
                    self.signals.text_update.emit("user", user_input)
                    
                    response = self.agent.generate_response(user_input)
                    self.signals.text_update.emit("agent", response)
                    
                    self.signals.speaking_status.emit(True)
                    self.agent.speak(response)
                    self.signals.speaking_status.emit(False)
            except Exception as e:
                self.signals.error_message.emit(f"Error during conversation: {str(e)}")
                self.is_running = False
                self.signals.speaking_status.emit(False)
                self.signals.listening_status.emit(False)
        
        # Add audio level monitoring to the agent
        if self.agent:
            original_listen = self.agent.listen
            def listen_with_levels(*args, **kwargs):
                def update_level(indata, *_args):
                    if hasattr(indata, 'max'):
                        self.agent.current_audio_level = float(abs(indata).max())
                
                self.agent.callback_wrapper = update_level
                return original_listen(*args, **kwargs)
                
            self.agent.listen = listen_with_levels
            
            # Start the agent thread
            self.agent_thread = threading.Thread(target=agent_thread_func)
            self.agent_thread.daemon = True
            self.agent_thread.start()
    
    def stop_conversation(self):
        """Stop the ongoing conversation"""
        self.is_running = False
        if self.agent:
            self.agent.is_listening = False
        self.start_button.setText("Start Conversation")
        self.status_label.setText("Ready")
    
    def show_error(self, message):
        """Display an error message to the user"""
        QMessageBox.critical(self, "Error", message)
        self.stop_conversation()
    def upload_document(self):
        """Open file dialog to upload a document"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Document", 
            "", 
            "Text Documents (*.txt);;Markdown Files (*.md);;All Files (*.*)"
        )
        
        if file_path:
            if self.document_processor.load_document(file_path):
                # Add to document list
                doc_name = os.path.basename(file_path)
                self.document_list.addItem(doc_name)
                
                # Select the document
                items = self.document_list.findItems(doc_name, Qt.MatchExactly)
                if items:
                    self.document_list.setCurrentItem(items[0])
                
                # Update document content
                self.document_content.setText(self.document_processor.get_current_document_content())
                
                # Enable buttons
                self.quiz_button.setEnabled(True)
                self.discuss_button.setEnabled(True)
                
                # Inform user
                self.qa_display.setText(f"Document '{doc_name}' loaded successfully.")
            else:
                self.qa_display.setText("Failed to load document. Please try again.")
    
    def select_document(self, item):
        """Handle document selection from the list"""
        doc_name = item.text()
        
        # Set as current document
        if doc_name in self.document_processor.documents:
            self.document_processor.current_document = doc_name
            
            # Update document content
            self.document_content.setText(self.document_processor.get_current_document_content())
            
            # Enable buttons
            self.quiz_button.setEnabled(True)
            self.discuss_button.setEnabled(True)
            
            # Clear QA display
            self.qa_display.setText("Document selected. Click 'Generate Questions' or 'Discuss Document'.")
    
    def generate_questions(self):
        """Generate questions from the current document"""
        if not self.document_processor.current_document:
            self.qa_display.setText("No document selected. Please upload a document first.")
            return
        
        # Generate questions
        questions = self.document_processor.generate_questions(num_questions=5)
        
        if not questions:
            self.qa_display.setText("Couldn't generate questions from this document.")
            return
        
        # Display questions
        qa_text = ""
        for i, qa in enumerate(questions, 1):
            qa_text += f"<b>Question {i}:</b> {qa['question']}<br>"
            qa_text += f"<b>Answer:</b> {qa['answer']}<br><br>"
        
        self.qa_display.setText(qa_text)
    
    def discuss_document(self):
        """Start a conversation about the current document"""
        if not self.document_processor.current_document or not self.agent:
            self.qa_display.setText("No document selected or agent not initialized.")
            return
        
        # Switch to chat tab
        self.tab_widget.setCurrentIndex(0)
        
        # Get document summary
        summary = self.document_processor.get_document_summary()
        
        # Start conversation if not already running
        if not self.is_running:
            self.start_conversation()
        
        # Add document context to conversation
        doc_name = self.document_processor.current_document
        self.signals.text_update.emit("user", f"Let's discuss the document '{doc_name}'")
        
        # Generate response about the document
        response = f"I'd be happy to discuss the document '{doc_name}' with you. "
        response += "What specific aspects would you like to explore? "
        response += "I can help explain concepts, quiz you on the content, or summarize key points."
        
        self.signals.text_update.emit("agent", response)
        self.agent.speak(response)

    def closeEvent(self, event):
        """Clean up when closing the window"""
        self.is_running = False
        if self.agent_thread and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=1.0)
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = ConversationalAgentUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
