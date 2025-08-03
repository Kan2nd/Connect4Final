# Connect 4 Multiplayer Game

## Overview
This is a multiplayer Connect 4 game implemented using Python with a client-server architecture. The game allows multiple users to connect to a server, create or join chat rooms, and play Connect 4 against each other. The client uses PyQt5 for the user interface and Pygame for rendering the game board.

## Features
- **Multiplayer Support**: Players can join rooms and play Connect 4 against one another.
- **Chat System**: Players can communicate in chat rooms before and during games.
- **Game Mechanics**: Classic Connect 4 rules with a 6x7 grid, where players take turns dropping colored chips to connect four in a row (horizontally, vertically, or diagonally).
- **Ready System**: Players must mark themselves as ready to start a game (2 players required).
- **Game Restart**: Players can restart the game after it ends.
- **User Interface**:
  - PyQt5-based lobby for server connection, room creation/joining, and chat.
  - Pygame-based game board for playing Connect 4.
- **Networked Gameplay**: Client-server communication using sockets and pickled messages.

## Prerequisites
- Python 3.6+
- Required Python packages (listed in `requirements.txt`)

## Installation
1. Clone or download the repository.
2. Install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure you have a working Python environment with access to PyQt5 and Pygame.

## Running the Application
1. **Start the Server**:
   - Run the server script to start the server on localhost (127.0.0.1) at port 12345:
     ```bash
     python server.py
     ```
   - The server will listen for client connections and manage rooms and games.

2. **Start the Client**:
   - Run the client script to launch the game client:
     ```bash
     python client.py
     ```
   - The client window will open, allowing you to connect to the server, choose a username, and create or join a room.

3. **Gameplay**:
   - Connect to the server by entering a username and clicking "Connect".
   - Create a new room or join an existing one.
   - In the room, click "Ready" to indicate readiness to play.
   - When two players are ready, the game starts automatically.
   - Use number keys (1-7) to select a column to drop your chip.
   - Press 'Y' after a game ends to restart.

## File Structure
- `server.py`: The server script that handles client connections, room management, and game logic.
- `client.py`: The client script that provides the user interface and communicates with the server.
- `requirements.txt`: Lists the required Python packages.
- `README.md`: This documentation file.

## Dependencies
See `requirements.txt` for the full list of dependencies. Key libraries include:
- PyQt5: For the graphical user interface (lobby and chat).
- Pygame: For rendering the Connect 4 game board.
- Python standard libraries: `socket`, `threading`, `pickle`, etc.

## Notes
- The server must be running before clients can connect.
- The game requires exactly two players in a room to start.
- The client uses a combination of PyQt5 for the lobby/chat interface and Pygame for the game board.
- The server uses a simple socket-based communication protocol with pickled Python objects for message passing.
- Ensure the server and client are running on the same network (default is localhost).

## Known Issues
- Limited error handling for network disconnections.
- No support for more than two players per game.
- Basic UI with minimal styling.

## Future Improvements
- Add better error handling for network issues.
- Implement spectator mode for rooms with more than two players.
- Enhance the UI with better styling and animations.
- Add support for saving game states or replays.

## License
This project is unlicensed and provided as-is for educational purposes.