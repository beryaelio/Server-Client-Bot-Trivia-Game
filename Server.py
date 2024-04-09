import struct
import time
import socket
import threading
from threading import Barrier, BrokenBarrierError, Lock, Event
from QuestionManager import QuestionManager

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


class Server:

    def __init__(self):
        """
                Initializes the server with necessary attributes for managing a multiplayer trivia game.

                Attributes:
                    qm (QuestionManager): An instance of the QuestionManager class to manage trivia questions.
                    round_answers_lock (Lock): A threading lock to ensure thread-safe operations on round_answers.
                    correct_players_lock (Lock): A lock to manage concurrent access to the correct_players set.
                    connected_clients_lock (Lock): A lock for thread-safe operations on the connected_clients set.
                    addresses_lock (Lock): A lock to manage access to the addresses set which tracks client IP addresses.

                    timer_thread (threading.Thread): A thread for managing game timing events.

                    declare_barrier (Barrier): A synchronization primitive to manage the transition from game play to declaring a winner.
                    round_barrier (Barrier): A barrier to synchronize the end of a game round.

                    declare_winner_event (Event): An event to signal the declaration of a game winner.
                    result_event (Event): An event to manage the timing of sending game results to players.
                    round_event (Event): An event to start a new game round.
                    start_event (Event): An event that signals the start of the game.

                    server_name (str): The name of the server.
                    correct_answer (str): The correct answer for the current trivia question.
                    result_message (str): The message summarizing the results of a game round.
                    addresses (set): A set of IP addresses to track connected clients.
                    connected_clients (set): A set of tuples storing information about connected clients.
                    correct_players (set): A set of player names who have not been eliminated.
                    General_round (int): The current round of the game.
                    correct_answers (int): The number of correct answers in the current round.
                    round_answers (dict): A dictionary to track players' answers {player_name: (answer, correct)}.
                    current_question (str): The current trivia question being asked.
                    broadcast_udp_flag (int): A flag to control UDP broadcast for game invitations.

                    port_number (int): The TCP port number on which the server operates.
                    udp_broadcast_thread (threading.Thread): A thread dedicated to broadcasting UDP invitations.

                Methods:
                    start_udp_broadcast: Broadcasts a game invitation message over UDP.
                    accept_tcp_connections: Accepts TCP connections from clients and handles them.

                This initialization sets up the game server, starts broadcasting invitations, and accepts incoming TCP connections from clients.
                """
        self.qm = QuestionManager()
        self.round_answers_lock = Lock()
        self.correct_players_lock = Lock()
        self.connected_clients_lock = Lock()
        self.addresses_lock = Lock()
        self.timer_thread = None
        # Barriers
        self.declare_barrier = None
        self.round_barrier = None

        # Events
        self.declare_winner_event = Event()
        self.result_event = Event()
        self.round_event = Event()
        self.start_event = Event()

        # General variables
        self.server_name = ""
        self.correct_answer = ""
        self.result_message = ""
        self.addresses = set()
        self.connected_clients = set()  # Store tuples of (client_socket, player_name)
        self.correct_players = set()
        self.General_round = 1
        self.correct_answers = 0
        self.round_answers = {}  # Track answers: {player_name: (answer, correct)}
        self.current_question = None
        self.broadcast_udp_flag = 0

        # Server init
        self.port_number = self.find_free_port()
        self.udp_broadcast_thread = threading.Thread(target=self.start_udp_broadcast)
        self.udp_broadcast_thread.start()
        self.accept_tcp_connections()

    def start_udp_broadcast(self):
        """
        Starts the udp broadcast. Sends a message that includes the magic_cookie, message_type,
        padded_server_name(which is the server name just padded so it will be 32 bits long),
        and the port_number. This function broadcasts the message so that
        the clients could use the message to connect to the server.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Define a creative server name and ensure it's 32 characters long
        self.server_name = "Gym"
        padded_server_name = self.server_name.ljust(32)  # Pad the server name to ensure it's 32 characters

        # Magic cookie, message type, and server port
        magic_cookie = 0xabcddcba
        message_type = 0x2

        # Pack the message according to the given format
        message = struct.pack('!Ib32sH', magic_cookie, message_type, padded_server_name.encode('utf-8'), self.port_number)

        print(GREEN + f"Server started, listening on IP address {self.get_server_ip()}" + RESET)
        broadcast_udp_flag = 1
        while True:
            if broadcast_udp_flag == 1:
                server_socket.sendto(message, ('<broadcast>', 13117))
            time.sleep(1)

    def reset_timer(self):
        """
        Reset the timer of 10 seconds for the players connection.
        """
        with self.connected_clients_lock:
            if self.timer_thread:
                self.timer_thread.cancel()
            self.start_event.clear()
            self.timer_thread = threading.Timer(10, self.start_game)
            self.timer_thread.start()

    def is_port_in_use(self, port):
        """
        Check if a port is in use or not. Check if we can use the port.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def find_free_port(self, start=49152, end=65535):
        """
        Find a free port we can use.
        """
        for port in range(start, end + 1):
            if not self.is_port_in_use(port):
                return port
        raise IOError("No free port found.")

    def get_server_ip(self):
        """
        Get the server's IP address.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
            return ip_address
        except Exception:
            return "127.0.0.1"

    def accept_tcp_connections(self):
        """
        Accept TCP connections from clients (the players) and adds them to the players' variables.
        """
        tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        tcp_server_socket.bind((str(self.get_server_ip()), self.port_number))

        tcp_server_socket.listen()

        while True:
            try:
                client_socket, client_address = tcp_server_socket.accept()
            except Exception as e:
                print("\033[31m" + f"An error occurred during the connection: {e}" + "\033[0m")

            self.reset_timer()

            thread = threading.Thread(target=self.client_handler, args=(client_socket, client_address))
            thread.start()

    def client_handler(self, client_socket, client_address):
        """
        Manages an individual client's connection and participation in the game.

        Steps:
        1. Receives the client's player name and checks for duplicates. If a duplicate is found, it assigns a unique name.
        2. Adds the player to the game by updating game state variables, ensuring thread-safe access through locks.
        3. Waits for the game to start, signaled by the 'start_event'.
        4. Enters a loop that continues for the duration of the client's participation in the game:
           a. Waits for the 'round_event', signaling the start of a new round.
           b. Sends the current question to the client, handling any potential disconnection.
           c. Calls 'handle_answers' to receive and process the client's answer.
           d. Waits for the 'result_event' to signal that results can be sent, then calls 'send_results'.
           e. Waits at a 'round_barrier' to ensure synchronization with other client handlers before proceeding to the next round or concluding the game.
        5. If the client is the last correct player remaining or if all players have been eliminated, declares the winner and breaks the loop.
        6. Cleans up by closing the client socket upon completion of the game or encountering a timeout exception.

        This function uses several synchronization mechanisms (Events, Barriers, Locks) to ensure that game state updates are consistent across multiple threads and that clients are processed in sync with the game's progression.
        """
        try:
            client_socket.settimeout(0.1)
            player_name = client_socket.recv(1024).strip().decode()

            duplicate_player = ""
            player_name = player_name.strip('\n')

            with self.correct_players_lock, self.connected_clients_lock, self.addresses_lock:
                if player_name in self.correct_players and client_address[0] not in self.addresses:
                    player_name = player_name + str(len(self.correct_players))
                    duplicate_player = f"You have been assigned {player_name}\n"
                self.addresses.add(client_address[0])
                self.correct_players.add(player_name)
                self.connected_clients.add((player_name, client_socket))
                print(CYAN + f"{player_name} has joined the game from {client_address}" + RESET)

            self.start_event.wait()
            while True:
                self.round_event.wait()
                try:
                    client_socket.sendall((duplicate_player + self.current_question).encode())
                except:
                    print(f'player:{player_name} disconnected')
                    with self.correct_players_lock:
                        self.correct_players.remove(player_name)
                if player_name in self.correct_players:
                    self.handle_answers(self.correct_answer, player_name, client_socket)
                self.result_event.wait()
                self.send_results(self.result_message, client_socket)

                try:
                    self.round_barrier.wait()
                except BrokenBarrierError:
                    pass

                if len(self.correct_players) == 1:
                    self.declare_winner_event.wait()
                    self.declare_winner(list(self.correct_players)[0], player_name, client_socket)
                    try:
                        self.declare_barrier.wait()
                    except BrokenBarrierError:
                        pass
                    break
                if len(self.correct_players) == 0:
                    break

        except socket.timeout:
            print("\033[31m" + f"Timeout waiting for {player_name} from {client_address}" + "\033[0m")
        finally:
            client_socket.close()

    def start_game(self):
        """
        This function starts the game, and calls the game_loop() function to run it.
        """
        print(RED + "Timer expired, game starting..." + RESET)
        self.start_event.set()
        self.game_loop()
        self.start_event.clear()

    def game_loop(self):
        """
        Manages the game's progression by controlling the flow of rounds, broadcasting questions, and evaluating answers.
        Utilizes synchronization primitives like Barriers and Events to coordinate between threads handling individual clients.

        Steps:
        1. Initializes barriers based on the number of connected clients.
        2. Enters a loop that continues as long as more than one player remains correct.
        3. Broadcasts the start of the game or questions for each round.
        4. Waits for answers within a timeout period and evaluates them, updating scores.
        5. After each round, waits at a barrier to ensure all threads have processed the round before proceeding.
        6. Declares a winner if only one correct player remains, broadcasting the result.
        7. Resets game state for potential new rounds and continues listening for new offers.

        The round and result events control the flow within each client handler thread, ensuring that messages are sent and received in sync.
        """
        self.General_round = 1
        self.round_barrier = Barrier(len(self.connected_clients) + 1)
        self.declare_barrier = Barrier(len(self.connected_clients) + 1)
        self.round_answers.clear()
        self.broadcast_udp_flag = 0

        while len(self.correct_players) > 1:
            if self.General_round == 1:
                self.broadcast_game_start()
                self.General_round = 2
            else:
                self.broadcast_question()
                self.General_round += 1

            time.sleep(12)
            self.round_event.clear()
            self.evaluate_and_update_scores()
            self.result_event.set()
            self.result_event.clear()
            try:
                self.round_barrier.wait()
            except BrokenBarrierError:
                pass

        if len(self.correct_players) == 1:
            winner_msg = f"Game over!\nCongratulations to the winner: {list(self.correct_players)[0]}"
            print(BLUE + winner_msg + RESET)
            print("Game over, sending out offer requests...")
            self.General_round = 1
            self.declare_winner_event.set()
            try:
                self.declare_barrier.wait()
            except BrokenBarrierError:
                pass
        self.result_event.clear()
        self.connected_clients = set()
        self.correct_players = set()
        self.broadcast_udp_flag = 1

    def broadcast_game_start(self):
        """
        Broadcasts the start of the game. Including a welcome message to the player and the first question.
        """
        welcome_message = f"Welcome to the {self.server_name} server, where we are answering trivia questions about Aston Villa FC.\n"
        player_list_message = ""
        for idx, (player_name, _) in enumerate(self.connected_clients, start=1):
            player_list_message += f"Player {idx}: {player_name}\n"

        first_question = self.qm.get_random_question()
        self.current_question = welcome_message + player_list_message + "==\nTrue or False: " + first_question + "\n"
        print(MAGENTA + self.current_question + RESET)
        self.correct_answer = self.qm.get_correct_answer()
        self.correct_answer = [str(element) for element in self.correct_answer]
        self.round_event.set()

    def broadcast_question(self):
        """
        Broadcasts a question to all the players simultaneously.
        """
        self.current_question = self.qm.get_random_question()
        self.current_question = (f"\nRound {self.General_round}, played by {' and '.join(list(self.correct_players))}:\nTrue or False:"
                      f" {self.current_question}\n")
        self.correct_answer = self.qm.get_correct_answer()
        self.correct_answer = [str(element) for element in self.correct_answer]
        print(MAGENTA + self.current_question + RESET)
        self.round_event.set()

    def evaluate_and_update_scores(self):
        """
        Evaluates the answers submitted by players during a game round and updates the scores accordingly.
        Process:
        1. Checks if any players have submitted answers within the time limit.
           a. If no players responded in time, it resets the game state for a new round and informs all players that no answers were received.
           b. If there are players who responded, it processes their answers.
        2. Iterates over the collected answers from players, determining whether each answer is correct or incorrect.
           a. Correct answers are acknowledged, and the player's status in the game is maintained.
           b. Incorrect answers lead to the removal of the player from the list of players eligible to win the round.
        3. Updates the game state based on the results of the answer evaluations.
           a. If no correct answers are provided by any player, all players are given another chance in a new round.
           b. If only one player remains as having provided a correct answer, that player is declared the winner.
        4. Constructs a message summarizing the outcomes of the round's answers, which is then broadcast to all players.

        The method ensures thread-safe operations on shared resources, particularly when accessing and modifying player answers and game state.
        """
        if len(self.correct_players) == 0:
            self.correct_players = set()
            # If all the players have disconnected
            print(YELLOW + "No players had answer within the time limit\nGame over!" + RESET)
            print(YELLOW + "Game over, sending out offer requests..." + RESET)
            self.result_message = "No players had answer within the time limit\nGame over!\n"
 
        elif len(self.correct_players) >= 1:
            with self.round_answers_lock:
                who_is_correct = ""
                copy_of_correct_players = self.correct_players.copy()
                for player_name, (answer, correct) in self.round_answers.items():
                    if player_name in self.correct_players:
                        if str(answer) in correct:
                            who_is_correct += f"\n{player_name} is correct!"
                        else:
                            self.correct_players.remove(player_name)
                            incorrect = f"\n{player_name} is incorrect!" + who_is_correct
                            who_is_correct = incorrect
                if len(self.correct_players) == 0:
                    self.correct_players = copy_of_correct_players.copy()
                if len(self.correct_players) == 1 and "is correct" in who_is_correct:
                    who_is_correct += " " + list(self.correct_players)[0] + ' Wins!'

            print(BLUE + who_is_correct + RESET)
            self.result_message = who_is_correct

    def handle_answers(self, correct_answer, player_name, client_socket):
        """
        A helper function that handles the gathering of answers from the players.
        """
        try:
            client_socket.settimeout(10)
            answer = client_socket.recv(1024).decode()
            with self.round_answers_lock:
                self.round_answers[player_name] = (answer, correct_answer)
        except:
            with self.correct_players_lock:
                if player_name in self.correct_players:
                    print(f"Timeout waiting for answer from {player_name}")
                    self.correct_players.remove(player_name)

    def send_results(self, result_message, client_socket):
        """
        Sends the results (result_message) to all the players in the game.
        """
        try:
            client_socket.sendall(result_message.encode())
        except Exception as e:
            print(f"Error sending message to client: {e}")

    def declare_winner(self, winner, player_name, client_socket):
        """
        A helper function that sends a message to the players about who won the game.
        """
        try:
            client_socket.sendall(f"Game over!\nCongratulations to the winner: {winner}\n"
                                  f"The total number of correct answers from all clients this round: {self.correct_answers}".encode())
        except Exception as e:
            print(f"Error declaring winner: {e}")


server = Server()
server.start_udp_broadcast()
udp_broadcast_thread = threading.Thread(target=server.start_udp_broadcast())
udp_broadcast_thread.start()
server.accept_tcp_connections()


