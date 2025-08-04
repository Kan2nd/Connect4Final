import sys
import pickle
import threading
import socket
import errno
import pygame
from PyQt5.QtWidgets import QSizePolicy, QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLineEdit, QLabel, QComboBox, QMainWindow, QHBoxLayout, QListWidget, QMessageBox
from PyQt5.QtCore import Qt, QEvent, QCoreApplication, QTimer
from PyQt5.QtGui import QColor

class Connect4GameUI:
    def __init__(self, parent):
        self.parent = parent
        self.CHIP_SIZE = 60
        self.OFFSET = 40
        self.CHIP_OFFSET = 15
        self.BOARD_HEIGHT = 450
        self.CHIP_RADIUS = int(self.CHIP_SIZE / 2)
        self.ROWS = 6
        self.COLUMNS = 7
        self.grid = [[None for i in range(self.COLUMNS)] for j in range(self.ROWS)]
        self.current_player_id = 0
        self.players = []
        self.game_over = False
        self.winner = None
        self.my_player_id = None
        self.end_game = False
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Connect 4')
        
        self.screen = pygame.display.set_mode((600, 550))
        self.font = pygame.font.SysFont('Calibri', 20)
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.my_turn = False
        
    def get_player_color(self, player_id):
        """Get color for player ID"""
        if player_id == 0:
            return (255, 0, 0)  # Red
        else:
            return (255, 255, 0)  # Yellow
            
    def get_player_name(self, player_id):
        """Get name for player ID"""
        if player_id == 0:
            return "Red"
        else:
            return "Yellow"
    
    def start_game(self, game_state):
        """Initialize the game with server state"""
        self.grid = game_state["grid"]
        self.current_player_id = game_state["current_player_id"]
        self.players = game_state["players"]
        self.game_over = game_state["game_over"]
        self.winner = game_state["winner"]
        
        # Determine which player ID I am
        if self.parent.current_user in self.players:
            self.my_player_id = self.players.index(self.parent.current_user)
        
        self.my_turn = (not self.game_over and 
                       game_state["current_player"] == self.parent.current_user)
        
        # Start game loop in a separate thread
        threading.Thread(target=self.game_loop, daemon=True).start()
        
    def update_game_state(self, game_state):
        """Update game state from server"""
        self.grid = game_state["grid"]
        self.current_player_id = game_state["current_player_id"]
        self.game_over = game_state["game_over"]
        self.winner = game_state["winner"]
        
        self.my_turn = (not self.game_over and 
                       game_state["current_player"] == self.parent.current_user)
        
    def game_loop(self):
        """Main game loop"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.end_game==False:
                        self.send_game_quit_message()
                        self.running = False
                    pygame.quit()
                    return
                elif event.type == pygame.KEYUP and self.my_turn and not self.game_over:
                    # Handle column selection (1-7 keys)
                    column = event.key - 49  # Convert key to column (1 key = column 0)
                    if 0 <= column < self.COLUMNS:
                        # Validate move locally first
                        if self.is_valid_move(column):
                            # Send move to server
                            self.parent.send_game_move(column)
                elif event.type == pygame.KEYUP and self.game_over:
                    # Handle restart (Y key)
                    if event.key in [121, 122]:  # Y or Z key
                        self.parent.send_restart_game()
            
            self.draw()
            self.clock.tick(60)
            
    def is_valid_move(self, column):
        """Check if a move is valid locally"""
        if column < 0 or column >= self.COLUMNS:
            return False
        # Check if column has space
        return self.grid[self.ROWS-1][column] is None
    
    def draw(self):
        """Draw the game board and pieces"""
        self.screen.fill((255, 255, 255))
        
        # Draw current player info
        if not self.game_over:
            if self.my_turn:
                text = f"Your turn - {self.get_player_name(self.my_player_id)}"
                color = (0, 150, 0)
            
            else:
                other_player = self.players[1 - self.my_player_id] if self.my_player_id is not None else "Other Player"
                text = f"{other_player}'s turn - {self.get_player_name(self.current_player_id)}"
                color = (150, 0, 0)
        else:
            if self.winner == self.parent.current_user:
                text = "You won! Now please leave the game."
                color = (0, 150, 0)
            elif self.winner == "No_one":
                text = "IT IS A DRAW LOL! Now please leave the game."
                color = (150, 0, 150)
            else:
                text = f"{self.winner} won! Now please leave the game."
                color = (150, 0, 0)
                
            
            self.end_game = True
                
        
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (20, 10))
        
        # Draw the game board
        self.draw_board()
        
        # Draw column numbers
        for i in range(self.COLUMNS):
            text = self.font.render(str(i + 1), True, (0, 0, 0))
            x = self.OFFSET + self.CHIP_RADIUS + i * (self.CHIP_SIZE + self.CHIP_OFFSET) - 5
            self.screen.blit(text, (x, self.OFFSET + self.BOARD_HEIGHT + 10))
        
        pygame.display.flip()
    
    def draw_board(self):
        """Draw the board and all pieces"""
        # Draw board outline
        board_width = self.COLUMNS * self.CHIP_SIZE + (self.COLUMNS - 1) * self.CHIP_OFFSET + 20
        board_height = self.ROWS * self.CHIP_SIZE + (self.ROWS - 1) * self.CHIP_OFFSET + 20
        pygame.draw.rect(self.screen, (0, 0, 255), 
            [self.OFFSET - 10, self.OFFSET - 10, board_width, board_height], 5)
        
        # Draw all pieces
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if self.grid[row][col] is not None:
                    player_id = self.grid[row][col]
                    color = self.get_player_color(player_id)
                    x = (self.OFFSET + self.CHIP_RADIUS + self.CHIP_OFFSET * col + 
                         self.CHIP_SIZE * col)
                    y = (self.BOARD_HEIGHT - self.CHIP_SIZE * row - 
                         self.CHIP_OFFSET * row)
                    pygame.draw.circle(self.screen, color, (x, y), self.CHIP_RADIUS)
        
        # Draw empty spaces
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if self.grid[row][col] is None:
                    x = (self.OFFSET + self.CHIP_RADIUS + self.CHIP_OFFSET * col + 
                         self.CHIP_SIZE * col)
                    y = (self.BOARD_HEIGHT - self.CHIP_SIZE * row - 
                         self.CHIP_OFFSET * row)
                    pygame.draw.circle(self.screen, (200, 200, 200), (x, y), self.CHIP_RADIUS, 2)
    # Added to handle Pygame window close event
    def send_game_quit_message(self):
        """Send a message to the server when the Pygame window is closed."""
        if client_menu.client_socket and self.parent.room_name and self.parent.current_user:
            message = {
                "Command": "Game_Quit",
                "Room_Name": self.parent.room_name,
                "User_Name": self.parent.current_user
            }
            try:
                data = pickle.dumps(message)
                client_menu.client_socket.sendall(data)
            except Exception as e:
                print(f"Error sending game quit message: {e}")
    
    def close(self):
        """Close the game window"""
        self.running = False
        
        try:
            pygame.quit()
        except:
            pass

class MessageEvent(QEvent):
    EventType = QEvent.Type(QEvent.registerEventType())
    def __init__(self, message_type, data):
        super().__init__(self.EventType)
        self.message_type = message_type
        self.data = data

class New_game_room(QMainWindow):  
    def __init__(self, current_user, room_name, list_of_users, client_socket):
        super().__init__()  
        self.current_user = current_user 
        self.room_name = room_name
        self.list_of_users_in_room = [user for user in (list_of_users or []) if isinstance(user, str)]
        self.client_socket = client_socket
        self.ready_users = {}
        self.game_ui = None
        print(f"Initializing New_game_room for user {self.current_user} in room {self.room_name} with users {self.list_of_users_in_room}")
        self.init_ui()
        self.show()  

    def init_ui(self):
        self.setWindowTitle(f"Game Room: {self.room_name}")
        self.setGeometry(800, 350, 700, 550)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
        """)

        # Chat area (left side)
        chat_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_edit.setAlignment(Qt.AlignTop)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                line-height: 1.6;
                font-family: 'Arial', sans-serif;
            }
        """)
        chat_layout.addWidget(self.text_edit)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here")
        self.message_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.message_input.setFixedHeight(40)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
                font-family: 'Arial', sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #1e90ff;
            }
        """)
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setFixedSize(100, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
                font-family: 'Arial', sans-serif;
            }
            QPushButton:hover {
                background-color: #4682b4;
            }
            QPushButton:pressed {
                background-color: #1c86ee;
            }
        """)
        input_layout.addWidget(self.send_button)

        # Ready button
        self.ready_button = QPushButton("Ready")
        self.ready_button.clicked.connect(self.toggle_ready)
        self.ready_button.setFixedSize(100, 40)
        self.ready_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-size: 16px;
                font-family: 'Arial', sans-serif;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        input_layout.addWidget(self.ready_button)

        chat_layout.addLayout(input_layout)
        chat_layout.addSpacing(10)
        main_layout.addLayout(chat_layout, stretch=3)

        # User list (right side)
        user_layout = QVBoxLayout()
        user_layout.setSpacing(10)
        self.user_list_label = QLabel("Users in Room:")
        self.user_list_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                margin: 10px;
                font-size: 16px;
                font-family: 'Arial', sans-serif;
            }
        """)
        user_layout.addWidget(self.user_list_label)

        self.user_list = QListWidget()
        self.user_list.setFixedWidth(160)
        self.update_user_list()
        self.user_list.setStyleSheet("""
            QListWidget {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Arial', sans-serif;
            }
            QListWidget::item {
                padding: 8px 0;
            }
            QListWidget::item:selected {
                background-color: #1e90ff;
            }
        """)
        user_layout.addWidget(self.user_list)
        user_layout.addStretch()
        main_layout.addLayout(user_layout, stretch=1)

    def update_user_list(self):
        """Update the user list with ready status"""
        self.user_list.clear()
        for user in self.list_of_users_in_room:
            ready_status = " (Ready)" if self.ready_users.get(user, False) else ""
            self.user_list.addItem(f"{user}{ready_status}")
            
    def changing_color(self,new_ready):
        if new_ready:
            self.ready_button.setText("Not Ready")
            self.ready_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 16px;
                    font-family: 'Arial', sans-serif;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
        else:
            self.ready_button.setText("Ready")
            self.ready_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    padding: 8px;
                    font-size: 16px;
                    font-family: 'Arial', sans-serif;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:pressed {
                    background-color: #1e7e34;
                }
            """)
    def toggle_ready(self):
        """Toggle ready status"""
        current_ready = self.ready_users.get(self.current_user, False)
        new_ready = not current_ready
        
        # Update button appearance
        self.changing_color(new_ready)
        

        # Send ready status to server
        if client_menu.client_socket:
            message = {
                "Command": "Ready_Status",
                "Room_Name": self.room_name,
                "User_Name": self.current_user,
                "Ready": new_ready
            }
            try:
                data = pickle.dumps(message)
                client_menu.client_socket.sendall(data)
            except Exception as e:
                self.text_edit.append(f"Error sending ready status: {e}")

    def send_message(self):
        """Send a message to the server"""
        message_text = self.message_input.text().strip()
        if message_text and client_menu.client_socket:
            message = {
                "Command": "Sending_Message",
                "Room_Name": self.room_name,
                "User_Name": self.current_user,
                "Text": message_text
            }
            try:
                data = pickle.dumps(message)
                client_menu.client_socket.sendall(data)
                self.message_input.clear()
            except Exception as e:
                self.text_edit.append(f"Error sending message: {e}")
        else:
            self.text_edit.append("Please enter a message to send.")

    def handle_ready_update(self, ready_users):
        """Handle ready status update from server"""
        self.ready_users = ready_users
        self.update_user_list()
        
        # Update own ready button state
        my_ready = self.ready_users.get(self.current_user, False)
        if my_ready:
            self.ready_button.setText("Not Ready")
        else:
            self.ready_button.setText("Ready")
        
        # Show ready status in chat
        ready_list = [user for user, ready in ready_users.items() if ready]
        if ready_list:
            self.text_edit.append(f"Ready players: {', '.join(ready_list)}")

    def handle_game_start(self, game_state):
        """Handle game start from server"""
        self.text_edit.append("Connect 4 game starting!")
        self.ready_button.setEnabled(False)
        # Create and start game UI
        self.game_ui = Connect4GameUI(self)
        self.game_ui.start_game(game_state)

    def handle_game_update(self, move, game_state):
        """Handle game move update from server"""
        # Update the game UI with the move
        
        player = move["player"]# This variable should be the username of the player making the move
        
        column = move["column"]
        self.text_edit.append(f"{player} played column {column + 1}")
        
        if self.game_ui:
            self.game_ui.update_game_state(game_state)

    def handle_game_over(self, winner, game_state):
        """Handle game over from server"""
        if winner == "No_one":
            self.text_edit.append("Game Over! IT IS A DRAW LOL!")
        else:
            self.text_edit.append(f"Game Over! Winner: {winner}")
        self.ready_button.setEnabled(True)
        
        #New sending message here to reshow the ready after game over
    
        current_ready = self.ready_users.get(self.current_user, False)
        message = {
                "Command": "Ready_Status",
                "Room_Name": self.room_name,
                "User_Name": self.current_user,
                "Ready": not current_ready
            }
        try:
            data = pickle.dumps(message)
            client_menu.client_socket.sendall(data)
        except Exception as e:
            self.text_edit.append(f"Error sending ready status: {e}")
        # Update the ready button color to match the new state
        self.changing_color(not current_ready)
        if self.game_ui:
            self.game_ui.update_game_state(game_state)

    def handle_game_restart(self, ready_users):
        """Handle game restart from server"""
        self.text_edit.append("Game restarted!")
        self.ready_users = ready_users
        self.update_user_list()
        
        if self.game_ui:
            self.game_ui.close()
            self.game_ui = None

    def send_game_move(self, column):
        """Send a game move to the server"""
        if client_menu.client_socket:
            message = {
                "Command": "Game_Move",
                "Room_Name": self.room_name,
                "User_Name": self.current_user,
                "Column": column
            }
            try:
                data = pickle.dumps(message)
                client_menu.client_socket.sendall(data)
            except Exception as e:
                self.text_edit.append(f"Error sending move: {e}")

    def send_restart_game(self):
        """Send a game restart request to the server"""
        if client_menu.client_socket:
            message = {
                "Command": "Restart_Game",
                "Room_Name": self.room_name,
                "User_Name": self.current_user
            }
            try:
                data = pickle.dumps(message)
                client_menu.client_socket.sendall(data)
            except Exception as e:
                self.text_edit.append(f"Error restarting game: {e}")

    def updating_text_edit(self, message, list_of_users):
        """Update the text edit and user list with a new message."""
        self.list_of_users_in_room = [user for user in (list_of_users or []) if isinstance(user, str)]
        self.text_edit.append(message)
        self.update_user_list()
        print(f"Updated chat room {self.room_name} with message: {message}, users: {self.list_of_users_in_room}")

    def closeEvent(self, event):
        """Handle window close event."""
        if self.game_ui:
            self.game_ui.close()
            
        if self.client_socket:
            try:
                leave_message = {
                    "Command": "Sending_Message",
                    "Room_Name": self.room_name,
                    "User_Name": self.current_user,
                    "Text": f"{self.current_user} has left the room."
                }
                print(f"Sending close Box_chat: {leave_message}")
                data = pickle.dumps(leave_message)
                self.client_socket.sendall(data)
                client_menu.alreadyinroom = False
            except:
                pass
        event.accept()

class ClientMenu(QMainWindow):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.list_of_users_in_room = None
        self.username = None  
        self.room_name = None
        self.list_of_available_rooms = []
        self.client_socket = None
        self.chatroom = None
        self.running = True
        self.is_disconnected = False
        self.alreadyinroom = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the main client window UI for connecting to the server and managing rooms."""
        self.setWindowTitle("CONNECT 4 MULTIPLAYER CHAT")
        self.setGeometry(760, 330, 400, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout()
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
        """)

        # Server info section
        self.server_label = QLabel(f"Server IP: {self.host}:{self.port}")
        self.server_label.setAlignment(Qt.AlignCenter)
        self.server_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: bold;
                margin: 10px;
                font-size: 14px;
            }
        """)
        self.layout.addWidget(self.server_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setAlignment(Qt.AlignCenter)
        self.username_input.setFixedHeight(30)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1e90ff;
            }
        """)
        self.layout.addWidget(self.username_input)

        # Connection buttons layout
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.Create_socket)
        self.connect_button.setFixedWidth(100)
        self.connect_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4682b4;
            }
            QPushButton:pressed {
                background-color: #1c86ee;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        button_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setFixedWidth(100)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4682b4;
            }
            QPushButton:pressed {
                background-color: #1c86ee;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        button_layout.addWidget(self.disconnect_button)
        
        self.layout.addLayout(button_layout)

        self.room_selector_label = QLabel("Select Room:")
        self.room_selector_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                margin-top: 10px;
                font-size: 14px;
            }
        """)
        self.layout.addWidget(self.room_selector_label)

        self.room_selector = QComboBox()
        self.room_selector.setPlaceholderText("Select Room")
        self.room_selector.currentTextChanged.connect(self.Choose_room) 
        self.room_selector.setEnabled(False)
        self.room_selector.setFixedHeight(30)
        self.room_selector.setStyleSheet("""
            QComboBox {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #ffffff;
                selection-background-color: #1e90ff;
                border: 1px solid #555555;
            }
        """)
        self.layout.addWidget(self.room_selector)

        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Enter New Room Name (if creating one)")
        self.room_input.setFixedHeight(30)
        self.room_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1e90ff;
            }
        """)
        self.layout.addWidget(self.room_input)

        # Room action buttons layout
        room_button_layout = QHBoxLayout()
        self.create_room_button = QPushButton("Create Room")
        self.create_room_button.clicked.connect(self.Create_room)
        self.create_room_button.setEnabled(False)
        self.create_room_button.setFixedWidth(100)
        self.create_room_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4682b4;
            }
            QPushButton:pressed {
                background-color: #1c86ee;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        room_button_layout.addWidget(self.create_room_button)

        self.join_room_button = QPushButton("Join Room")
        self.join_room_button.clicked.connect(self.Join_room)
        self.join_room_button.setEnabled(False)
        self.join_room_button.setFixedWidth(100)
        self.join_room_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4682b4;
            }
            QPushButton:pressed {
                background-color: #1c86ee;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        room_button_layout.addWidget(self.join_room_button)
        
        self.layout.addLayout(room_button_layout)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumHeight(200)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        self.layout.addWidget(self.text_edit)
        
        self.layout.addStretch()
        central_widget.setLayout(self.layout)

    def Create_socket(self):
        """Create socket connection to server"""
        check = self.username_input.text().strip()
        if not check:
            self.text_edit.append("Please enter a username to connect.")
            return
        
        self.username = self.username_input.text().strip()
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.text_edit.append(f"Connected to server at {self.host}:{self.port}")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.username_input.setEnabled(False)
            self.running = True
            self.is_disconnected = False
        except Exception as e:
            self.text_edit.append(f"Error connecting to server: {e}")
            self.client_socket = None
            return
            
        self.send_message({
            "Command": "Check_Username",
            "User_Name": self.username
        })
        
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def disconnect(self):
        """Disconnect from the server."""
        if self.is_disconnected:
            return
        self.running = False
        self.is_disconnected = True
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.username_input.setEnabled(True)
        self.room_selector.setEnabled(False)
        self.create_room_button.setEnabled(False)
        self.join_room_button.setEnabled(False)
        self.text_edit.append("Disconnected from server.")
        if self.chatroom:
            self.chatroom.close()
            self.chatroom = None

    def receive_messages(self):
        """Receive messages from the server in a separate thread."""
        while self.running and self.client_socket:
            try:
                data = self.client_socket.recv(1048576)
                if not data:
                    QCoreApplication.postEvent(self, MessageEvent("status", "Server disconnected."))
                    self.disconnect()
                    break
                message = pickle.loads(data)
                if message:
                    print(f"Processing message: {message}")
                    if message["Command"] in ["Join_Room", "Sending_Message"]:
                        QCoreApplication.postEvent(self, MessageEvent("chat", message))
                    elif message["Command"] in ["Room_State", "Check_Username"]:
                        QCoreApplication.postEvent(self, MessageEvent("rooms", message))
                    elif message["Command"] in ["Ready_Update", "Game_Start", "Game_Update", "Game_Over", "Game_Restart"]:
                        QCoreApplication.postEvent(self, MessageEvent("game", message))
                    else:
                        QCoreApplication.postEvent(self, MessageEvent("status", f"Unknown command received: {message['Command']}"))
            except socket.error as e:
                if self.running and e.errno == errno.WSAEWOULDBLOCK:
                    continue
                if self.running:
                    QCoreApplication.postEvent(self, MessageEvent("status", f"Error receiving message: {e}"))
                    self.disconnect()
                break

    def customEvent(self, event):
        """Handle custom events for thread-safe UI updates."""
        if event.type() == MessageEvent.EventType:
            if event.message_type == "chat":
                self.process_chat_update(event.data)
            elif event.message_type == "rooms":
                self.process_rooms_update(event.data)
            elif event.message_type == "status":
                self.process_status_update(event.data)
            elif event.message_type == "game":
                self.process_game_update(event.data)

    def process_chat_update(self, message):
        """Handle chat message updates."""
        print(f"Received chat message: {message}")
        
        try:
            if message["Command"] == "Join_Room":
                room_name = message["Room_Name"]
                list_of_users = message["Users_In_Room"]
                self.list_of_users_in_room = list_of_users
                if self.alreadyinroom == False:
                    print(f"Creating New_chat_room for {room_name} with users {list_of_users}")
                    if self.chatroom:
                        self.chatroom.close()
                    self.chatroom = New_game_room(self.username, room_name, list_of_users, self.client_socket)   
                    self.alreadyinroom = True
                
            elif message["Command"] == "Sending_Message":
                room_name = message["Room_Name"]
                text = message["Text"]
                username = message["User_Name"]
                if self.chatroom and self.chatroom.room_name == room_name:
                    self.chatroom.updating_text_edit(f"{username}: {text}", self.list_of_users_in_room)
                else:
                    print(f"Chat room not found for room {room_name}. Message: {text}")
            
        except Exception as e:
            QCoreApplication.postEvent(self, MessageEvent("status", f"Error processing chat message: {e}"))

    def process_rooms_update(self, message):
        """Handle room state updates."""
        print(f"Received rooms_update: {message}")
        try:
            if message["Command"] == "Check_Username":
                self.list_of_users_in_room = message["Users_In_Room"]
                self.text_edit.append(f"Username {self.username} is valid.")
                self.room_selector.setEnabled(True)
                self.join_room_button.setEnabled(True)
                self.create_room_button.setEnabled(True)
                self.room_input.setEnabled(True)
                
            elif message["Command"] == "Room_State":
                new_rooms = set(message["Available_Rooms"])
                old_rooms = set(self.list_of_available_rooms)
                userinrooms = message["Users_In_Room"]
                if message["Users_In_Room"]: 
                    self.list_of_users_in_room = userinrooms
                self.list_of_available_rooms = message["Available_Rooms"]
                self.room_selector.clear()
                self.room_selector.addItems(self.list_of_available_rooms)
                added_rooms = new_rooms - old_rooms
                if added_rooms:
                    self.text_edit.append(f"New room(s) created: {', '.join(added_rooms)}")
                elif new_rooms != old_rooms:
                    self.text_edit.append("Available rooms updated.")
                self.room_selector.setEnabled(True)
                self.join_room_button.setEnabled(True)
                self.create_room_button.setEnabled(True)
                self.room_input.setEnabled(True)
                
        except Exception as e:
            QCoreApplication.postEvent(self, MessageEvent("status", f"Error processing room update: {e}"))

    def process_game_update(self, message):
        """Handle game-related updates."""
        print(f"Received game message: {message}")
        try:
            if self.chatroom:
                if message["Command"] == "Ready_Update":
                    self.chatroom.handle_ready_update(message["Ready_Users"])
                elif message["Command"] == "Game_Start":
                    self.chatroom.handle_game_start(message["Game_State"])
                elif message["Command"] == "Game_Update":
                    self.chatroom.handle_game_update(message["Move"], message["Game_State"])
                elif message["Command"] == "Game_Over":
                    self.chatroom.handle_game_over(message["Winner"], message["Game_State"])
                elif message["Command"] == "Game_Restart":
                    self.chatroom.handle_game_restart(message["Ready_Users"])
        except Exception as e:
            QCoreApplication.postEvent(self, MessageEvent("status", f"Error processing game update: {e}"))

    def process_status_update(self, message):
        """Handle status updates."""
        self.text_edit.append(message)

    def Create_room(self):
        """Create a new room and send request to server"""
        current_room = self.room_input.text().strip()
        if current_room:
            message = {
                "Command": "Create_Room",
                "Room_Name": current_room,
                "User_Name": self.username
            }
            self.send_message(message)
            self.text_edit.append(f"Requested creation of room {current_room}")
        else:
            self.text_edit.append("Please enter a room name to create.")
            
    def Join_room(self):
        """Join a room and request room state update"""
        current_room = self.room_input.text().strip()
        if current_room:
            message = {
                "Command": "Join_Room",
                "Room_Name": current_room,
                "User_Name": self.username
            }
            self.send_message(message)
            self.send_message({
                "Command": "Request_Room_State",
                "User_Name": self.username
            })
            self.send_message({
                "Command": "Sending_Message",
                "Room_Name": current_room,
                "User_Name": self.username,
                "Text": f"{self.username} has joined the room."
            })
        else:
            self.text_edit.append("Please enter a room name to join.")
     
    def Choose_room(self):
        """Handle room selection from the combo box."""
        selected_room = self.room_selector.currentText()
        if selected_room:
            self.room_input.setText(selected_room)
            self.join_room_button.setEnabled(True)
        else:
            self.join_room_button.setEnabled(False)   
                
    def send_message(self, message):
        """Send a message to the server."""
        if self.client_socket and self.running and not self.is_disconnected:
            try:
                self.client_socket.setblocking(True)
                data = pickle.dumps(message)
                self.client_socket.sendall(data)
            except socket.error as e:
                if e.errno == errno.WSAEWOULDBLOCK:
                    pass
                else:
                    print(f"Error sending message: {e}")
                    QCoreApplication.postEvent(self, MessageEvent("status", f"Error sending message: {e}"))
                    self.disconnect()
            except Exception as e:
                print(f"Error sending message: {e}")
                QCoreApplication.postEvent(self, MessageEvent("status", f"Error sending message: {e}"))
                self.disconnect()

    def closeEvent(self, event):
        """Handle window close event."""
        self.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client_menu = ClientMenu("127.0.0.1", 12345)
    client_menu.show()
    sys.exit(app.exec_())
            