import socket
import threading
import pickle
import sys
import random

class Connect4Game:
    def __init__(self, room_name, players):
        self.room_name = room_name
        self.players = players  # List of usernames
        self.ROWS = 6
        self.COLUMNS = 7
        self.grid = [[None for i in range(self.COLUMNS)] for j in range(self.ROWS)]
        self.current_player = 0
        self.game_over = False
        self.winner = None
        
        # Randomly assign player IDs
        random.shuffle(self.players)
        print(f"Game started in room {room_name}: {self.players[0]} (Red) vs {self.players[1]} (Yellow)")

    def add_chip(self, player_username, column):
        """Add a chip to the board and return the row it landed in, or -1 if invalid"""
        if self.game_over:
            return -1
            
        # Check if it's the correct player's turn
        if self.players[self.current_player] != player_username:
            return -1
            
        # Find the lowest available row in the column
        for row in range(self.ROWS):
            if self.grid[row][column] is None:
                self.grid[row][column] = self.current_player
                
                # Check for win
                if self.check_win(self.current_player):
                    self.game_over = True
                    self.winner = player_username
                elif self.is_board_full():
                    self.game_over = True
                    self.winner = "No_one" # Tie condition, no winner, used to be none but none is used for other things so No_one it is
                else:
                    # Switch players
                    self.current_player = (self.current_player + 1) % 2
                    
                return row
        return -1  # Column is full

    def check_win(self, player_id):
        """Check if the given player has won"""
        # Check horizontal
        for c in range(self.COLUMNS - 3):
            for r in range(self.ROWS):
                if (self.grid[r][c] == player_id and self.grid[r][c+1] == player_id and 
                    self.grid[r][c+2] == player_id and self.grid[r][c+3] == player_id):
                    return True

        # Check vertical
        for c in range(self.COLUMNS):
            for r in range(self.ROWS - 3):
                if (self.grid[r][c] == player_id and self.grid[r+1][c] == player_id and 
                    self.grid[r+2][c] == player_id and self.grid[r+3][c] == player_id):
                    return True

        # Check positive diagonal
        for c in range(self.COLUMNS - 3):
            for r in range(self.ROWS - 3):
                if (self.grid[r][c] == player_id and self.grid[r+1][c+1] == player_id and 
                    self.grid[r+2][c+2] == player_id and self.grid[r+3][c+3] == player_id):
                    return True

        # Check negative diagonal
        for c in range(self.COLUMNS - 3):
            for r in range(3, self.ROWS):
                if (self.grid[r][c] == player_id and self.grid[r-1][c+1] == player_id and 
                    self.grid[r-2][c+2] == player_id and self.grid[r-3][c+3] == player_id):
                    return True

        return False
    def is_board_full(self):
        """Check if the board is full (tie condition)"""
        for col in range(self.COLUMNS):
            if self.grid[self.ROWS-1][col] is None:
                return False
        return True
    
    def get_game_state(self):
        """Return the current game state"""
        return {
            "grid": self.grid,
            "current_player": self.players[self.current_player] if not self.game_over else None,
            "current_player_id": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "players": self.players
        }

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # Dictionary to store client sockets by username
        self.rooms = {}   # Dictionary to store room names and their users
        self.ready_users = {}  # Dictionary to store ready status by room
        self.games = {}   # Dictionary to store active games by room
        self.running = True  # Add this flag
        self.init_server()

    def init_server(self):
        """Initialize the server socket and start listening for connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Error starting server: {e}")
            sys.exit(1)

        # Start accepting client connections
        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        """Accept incoming client connections in a separate thread."""
        while self.running:  # Change from 'while True'
            try:
                self.server_socket.settimeout(1.0)  # Add timeout
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            except socket.timeout:
                continue  # Expected timeout, just continue
            except Exception as e:
                if self.running:  # Only print error if still running
                    print(f"Error accepting connection: {e}")
                break

    def handle_client(self, client_socket, addr):
        """Handle communication with a connected client."""
        username = None
        while True:
            try:
                data = client_socket.recv(1048576)
                if not data:
                    print(f"Client {addr} disconnected")
                    break
                message = pickle.loads(data)
                if not message:
                    continue
                print(f"Received from {addr}: {message}")

                # Process client commands
                if message["Command"] == "Check_Username":
                    username = message["User_Name"]
                    self.clients[username] = client_socket
                    response = {
                        "Command": "Check_Username",
                        "Status": "Valid",
                        "Users_In_Room": []
                    }
                    self.send_message(client_socket, response)
                    self.broadcast_room_state()
                    
               
                
                elif message["Command"] == "Create_Room":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    print(f"Creating room {room_name} for user {username}")
                    self.create_room(room_name, username)
                    self.broadcast_room_state()

                elif message["Command"] == "Join_Room":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    print(f"User {username} joining room {room_name}")
                    self.join_room(room_name, username)
                    response = {
                        "Command": "Join_Room",
                        "Room_Name": room_name,
                        "User_Name": username,
                        "Users_In_Room": self.rooms.get(room_name, [])
                    }
                    self.broadcast_to_room(room_name, response)
                    self.broadcast_to_room(room_name, {
                        "Command": "Room_State",
                        "Available_Rooms": list(self.rooms.keys()),
                        "Users_In_Room": self.rooms.get(room_name, [])
                    })
                    self.broadcast_to_room(room_name, {
                        "Command": "Sending_Message",
                        "Room_Name": room_name,
                        "User_Name": username,
                        "Text": f"{username} has joined the room."
                    })

                elif message["Command"] == "Sending_Message":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    text = message["Text"]
                    text_checker = f"{username} has left the room."
                    if text == text_checker and room_name in self.rooms:
                        if username in self.rooms[room_name]:
                            self.rooms[room_name].remove(username)
                            # Remove from ready users
                            if room_name in self.ready_users and username in self.ready_users[room_name]:
                                del self.ready_users[room_name][username]
                            print(f"Removed {username} from room {room_name}")
                            if not self.rooms[room_name]:
                                del self.rooms[room_name]
                                if room_name in self.ready_users:
                                    del self.ready_users[room_name]
                                if room_name in self.games:
                                    del self.games[room_name]
                                print(f"Deleted empty room {room_name}")
                                self.broadcast_room_state()
                            else:
                                self.broadcast_to_room(room_name, {
                                    "Command": "Room_State",
                                    "Available_Rooms": list(self.rooms.keys()),
                                    "Users_In_Room": self.rooms[room_name]
                                })
                                self.broadcast_to_room(room_name, {
                                    "Command": "Sending_Message",
                                    "Room_Name": room_name,
                                    "User_Name": username,
                                    "Text": text
                                })
                    else:
                        self.broadcast_room_state()
                        self.broadcast_to_room(room_name, {
                            "Command": "Sending_Message",
                            "Room_Name": room_name,
                            "User_Name": username,
                            "Text": text
                        })

                elif message["Command"] == "Ready_Status":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    ready = message["Ready"]
                    self.handle_ready_status(room_name, username, ready)

                elif message["Command"] == "Game_Move":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    column = message["Column"]
                    self.handle_game_move(room_name, username, column)

                elif message["Command"] == "Restart_Game":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    self.handle_restart_game(room_name, username)
                    
                #Added handling for game quit command
                elif message["Command"] == "Game_Quit":
                    room_name = message["Room_Name"]
                    username = message["User_Name"]
                    self.handle_ending_game_by_exit(room_name, username)
                    
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        # Cleanup when client disconnects
        if username and username in self.clients:
            print(f"Cleaning up for disconnected user {username}")
            del self.clients[username]
            for room_name, users in list(self.rooms.items()):
                if username in users:
                    users.remove(username)
                    # Remove from ready users
                    if room_name in self.ready_users and username in self.ready_users[room_name]:
                        del self.ready_users[room_name][username]
                    if not users:
                        del self.rooms[room_name]
                        if room_name in self.ready_users:
                            del self.ready_users[room_name]
                        if room_name in self.games:
                            del self.games[room_name]
                        print(f"Deleted empty room {room_name}")
                        self.broadcast_room_state()
                    else:
                        self.broadcast_to_room(room_name, {
                            "Command": "Join_Room",
                            "Room_Name": room_name,
                            "User_Name": username,
                            "Users_In_Room": users
                        })
                        self.broadcast_to_room(room_name, {
                            "Command": "Room_State",
                            "Available_Rooms": list(self.rooms.keys()),
                            "Users_In_Room": users
                        })
            if self.rooms:
                self.broadcast_room_state()
        try:
            client_socket.close()
        except:
            pass

    def create_room(self, room_name, username):
        """Create a new chat room without adding the user."""
        if room_name not in self.rooms:
            self.rooms[room_name] = []
            self.ready_users[room_name] = {}
            print(f"Created room {room_name} by user {username}")

    def join_room(self, room_name, username):
        """Add a user to an existing chat room."""
        if room_name not in self.rooms:
            self.rooms[room_name] = []
            self.ready_users[room_name] = {}
        if username not in self.rooms[room_name]:
            self.rooms[room_name].append(username)
            self.ready_users[room_name][username] = False

    def handle_ready_status(self, room_name, username, ready):
        """Handle ready status changes and start game if all users ready"""
        # Ensure the room exists and the user is in the room
        if room_name in self.ready_users:
            #set the user's ready status
            self.ready_users[room_name][username] = ready
            
            # Broadcast ready status update
            self.broadcast_to_room(room_name, {
                "Command": "Ready_Update",
                "Room_Name": room_name,
                "Ready_Users": self.ready_users[room_name]
            })
            
            # Check if we can start a game (exactly 2 players, both ready)
            room_users = self.rooms.get(room_name, [])
            if (len(room_users) == 2 and 
                all(self.ready_users[room_name].get(user, False) for user in room_users)):
                
                # Start the game
                self.games[room_name] = Connect4Game(room_name, room_users.copy())
                
                # Reset ready status
                for user in room_users:
                    self.ready_users[room_name][user] = False
                
                # Broadcast game start
                self.broadcast_to_room(room_name, {
                    "Command": "Game_Start",
                    "Room_Name": room_name,
                    "Game_State": self.games[room_name].get_game_state()
                })
                
                print(f"Started Connect 4 game in room {room_name}")

    def handle_game_move(self, room_name, username, column):
        """Handle a game move from a player"""
        if room_name not in self.games:
            return
            
        game = self.games[room_name] # Get the game instance for the room
        row = game.add_chip(username, column) # Add the chip to the game board
        
        if row != -1:  # Valid move
            # Broadcast the move to all players in the room
            self.broadcast_to_room(room_name, {
                "Command": "Game_Update",
                "Room_Name": room_name,
                "Move": {
                    "player": username,
                    "column": column,
                    "row": row
                },
                "Game_State": game.get_game_state()
            })
           
            # If game is over, send game over message
            if game.game_over:
                self.broadcast_to_room(room_name, {
                    "Command": "Game_Over",
                    "Room_Name": room_name,
                    "Winner": game.winner,
                    "Game_State": game.get_game_state()
                })

    def handle_restart_game(self, room_name, username):
        """Handle game restart request"""
        if room_name in self.games:
            # Remove the current game
            del self.games[room_name]
            
            # Reset ready status
            if room_name in self.ready_users:
                for user in self.ready_users[room_name]:
                    self.ready_users[room_name][user] = False
            
            # Broadcast restart
            self.broadcast_to_room(room_name, {
                "Command": "Game_Restart",
                "Room_Name": room_name,
                "Ready_Users": self.ready_users.get(room_name, {})
            })

    #Handle game ending due to player quitting via Pygame window
    def handle_ending_game_by_exit(self, room_name, quitting_username):
        """Handle game ending due to a player quitting via Pygame window."""
        if room_name in self.games and room_name in self.rooms:
            game = self.games[room_name]
            remaining_users = [user for user in self.rooms[room_name] if user != quitting_username]
            if len(remaining_users) == 1:  # Ensure exactly one player remains
                remaining_player = remaining_users[0]
                game.game_over = True
                game.winner = remaining_player
                print(f"Player {quitting_username} quit game in room {room_name}. Declaring {remaining_player} as winner.")
                self.broadcast_to_room(room_name, {
                    "Command": "Game_Over",
                    "Room_Name": room_name,
                    "Winner": remaining_player,
                    "Game_State": game.get_game_state()
                })
                del self.games[room_name]  # Remove the game after ending
                # Broadcast updated room state
                self.broadcast_to_room(room_name, {
                    "Command": "Room_State",
                    "Available_Rooms": list(self.rooms.keys()),
                    "Users_In_Room": self.rooms[room_name]
                })
                self.broadcast_to_room(room_name, {
                    "Command": "Sending_Message",
                    "Room_Name": room_name,
                    "User_Name": quitting_username,
                    "Text": f"{quitting_username} has quit the game."
                })
    
    
    def send_message(self, client_socket, message):
        """Send a message to a specific client."""
        print(f"Sending message: {message}")
        try:
            data = pickle.dumps(message)
            client_socket.sendall(data)
        except Exception as e:
            print(f"Error sending message: {e}")

    def broadcast(self, message):
        """Broadcast a message to all connected clients."""
        for client_socket in self.clients.values():
            self.send_message(client_socket, message)

    def broadcast_to_room(self, room_name, message):
        """Broadcast a message to all users in a specific room."""
        if room_name in self.rooms:
            for username in self.rooms[room_name]:
                if username in self.clients:
                    self.send_message(self.clients[username], message)

    def broadcast_room_state(self):
        """Send the current list of available rooms to all clients."""
        response = {
            "Command": "Room_State",
            "Available_Rooms": list(self.rooms.keys()),
            "Users_In_Room": []
        }
        self.broadcast(response)

    def shutdown(self):
        """Shutdown the server and close all connections."""
        print("Shutting down server...")
        self.running = False  # Set flag to stop threads
        
        # Close all client connections
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

if __name__ == "__main__":
    server = ChatServer("0.0.0.0", 12345)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        server.shutdown()  # Call shutdown method
        sys.exit(0)