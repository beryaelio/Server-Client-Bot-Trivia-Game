import struct
import time
from QuestionManager import QuestionManager
import socket
import threading
from threading import Barrier, BrokenBarrierError

'''QuestionManager instance'''
qm = QuestionManager()

'''Locks'''
round_answers_lock = threading.Lock()
correct_players_lock = threading.Lock()
connected_clients_lock = threading.Lock()
current_question = None

''' Barriers'''
declare_barrier = None
round_barrier = None

''' Events'''
declare_winner_event = threading.Event()
result_event = threading.Event()
round_event = threading.Event()  # Indicates the start of a new round
start_event = threading.Event()

''' ANSI '''
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

'''General global inits'''
server_name = ""
correct_answer = ""
result_message = ""
connected_clients = []  # Store tuples of (client_socket, player_name)
correct_players = set()
timer_thread = None
timer_thread_for_response = None
General_round = 1
correct_answers = 0
round_answers = {}  # Track answers: {player_name: (answer, correct)}

'''Server initialization'''


def start_udp_broadcast():
    """
    Starts the udp broadcast. Sends a message that includes the magic_cookie, message_type,
    padded_server_name(which is the server name just padded so it will be 32 bits long),
    and the port_number. This function broadcasts the message so that
    the clients could use the message to connect to the server.
    """
    global server_name, port_number
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_name = "Bodymoor"
    padded_server_name = server_name.ljust(32)
    magic_cookie = 0xabcddcba
    message_type = 0x2
    message = struct.pack('!Ib32sH', magic_cookie, message_type, padded_server_name.encode('utf-8'), port_number)
    print(GREEN + f"Server started, listening on IP address {get_server_ip()}" + RESET)

    while True:
        server_socket.sendto(message, ('<broadcast>', 13117))
        time.sleep(1)


def is_port_in_use(port):
    """
    Check if a port is in use or not. Check if we can use the port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_free_port(start=49152, end=65535):
    """
    Find a free port we can use.
    """
    for port in range(start, end + 1):
        if not is_port_in_use(port):
            return port
    raise IOError("No free port found.")


def get_server_ip():
    """
    Get the server's IP address.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            # Get the socket's own address
            ip_address = s.getsockname()[0]
        return ip_address
    except Exception:
        return "127.0.0.1"


def accept_tcp_connections():
    """
    Accept TCP connections from clients (the players) and adds them to the players' variables.
    """
    global timer_thread, qm, connected_clients, correct_players, port_number
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tcp_server_socket.bind((str(get_server_ip()), port_number))

    tcp_server_socket.listen()

    reset_timer()

    while True:

        client_socket, client_address = tcp_server_socket.accept()
        # print(f"Connection from {client_address}")

        # Reset the timer each time a new player connects
        reset_timer()

        # Start a new thread for the client
        thread = threading.Thread(target=client_handler, args=(client_socket, client_address))
        thread.start()


def reset_timer():
    """
    Reset the timer of 10 seconds for the players connection.
    """
    global timer_thread, start_event
    with connected_clients_lock:
        if timer_thread:
            timer_thread.cancel()  # Stop the current timer
        start_event.clear()  # Reset the event for the next game start
        timer_thread = threading.Timer(10, start_game)
        timer_thread.start()


'''Handling clients threads'''


def client_handler(client_socket, client_address):
    """
    Handle a client connection to the server. add the player to the game variables and reset the timer.
    """
    global correct_players, qm, current_question, correct_answer, result_message,\
        round_barrier, declare_barrier, round_event, start_event, declare_barrier, round_answers, round_answers_lock, result_event
    try:
        # Initial setup as before
        client_socket.settimeout(0.1)
        player_name = client_socket.recv(1024).strip().decode()
        duplicate_player = ""
        player_name = player_name.strip('\n')

        with correct_players_lock:
            with connected_clients_lock:
                if player_name in correct_players :
                    # Handling duplicate players
                    player_name = player_name + str(len(correct_players))
                    duplicate_player = f"You have been assigned {player_name}\n"
                correct_players.add(player_name)
                # Add player to the shared list
                connected_clients.append((player_name, client_socket))
                print(GREEN + f"{player_name} has joined the game from {client_address}" + RESET)

        # Wait for the signal to start the game
        start_event.wait()
        while True:
            #Waiting for the game loop to start
            round_event.wait()
            # If no duplicate player duplicate_player == ""
            # else duplicate_player == player_name + str(len(correct_players))
            client_socket.sendall((duplicate_player + current_question).encode())
            if player_name in correct_players:
                # Checking if the player is still in the game
                # He's not in the game if he has been timed out or incorrect
                handle_answers(correct_answer, player_name, client_socket)
            # The thread waits for the game loop for the signal to send the result message
            result_event.wait()
            send_results(result_message, client_socket)
            # Wait on the barrier here, ensuring all threads reach this point before proceeding
            try:
                round_barrier.wait()
            except BrokenBarrierError:
                pass  # Handle error as needed

            if len(correct_players) == 1:

                declare_winner_event.wait()
                declare_winner(list(correct_players)[0], player_name,client_socket)
                # Wait on the barrier here, ensuring all threads reach this point before proceeding
                try:
                    declare_barrier.wait()
                except BrokenBarrierError:
                    pass  # Handle error as needed
                break
            if len(correct_players) == 0:
                break

    except socket.timeout:
        print(RED + f"Timeout waiting for player name from {client_address}" + RESET)
    finally:
        client_socket.close()


'''Starting the game'''


def start_game():
    """
    This function starts the game, and calls the game_loop() function to run it.
    """
    global start_event, connected_clients_lock
    with connected_clients_lock:
        print(RED + "Timer expired, game starting..." + RESET)
        start_event.set()
    game_loop()
    start_event.clear()


def game_loop():
    """
    The actual management of the game play. Determines what happens when and calls the appropriate functions.
    """
    global correct_players,connected_clients, qm,General_round,\
        round_barrier, declare_barrier, round_event, start_event,\
        declare_barrier, round_answers, round_answers_lock, result_event, declare_winner_event
    General_round = 1
    round_barrier = Barrier(len(connected_clients) + 1)
    declare_barrier = Barrier(len(connected_clients) + 1)
    round_answers.clear()

    while len(correct_players) > 1:
        if General_round == 1:
            broadcast_game_start()
            General_round = 2
        else:
            with round_answers_lock:
                round_answers.clear()
            broadcast_question()
            General_round += 1
        time.sleep(12)
        round_event.clear()
        evaluate_and_update_scores()
        result_event.set()
        result_event.clear()
        try:
            round_barrier.wait()
        except BrokenBarrierError:
            pass
    if len(correct_players) == 1:
        print(f"Game over!\nCongratulations to the winner: {list(correct_players)[0]}")
        print("Game over, sending out offer requests...")
        General_round = 1
        declare_winner_event.set()
        try:
            declare_barrier.wait()
        except BrokenBarrierError:
            pass
    result_event.clear()
    connected_clients = []
    correct_players = set()


def broadcast_game_start():
    """
    Broadcasts the start of the game. Including a welcome message to the player and the first question.
    """
    global connected_clients, qm, server_name, correct_answer, current_question
    welcome_message = (f"Welcome to the {server_name} server, where we are answering trivia questions "
                       f"about Aston Villa FC.\n")
    player_list_message = ""
    for idx, (player_name, _) in enumerate(connected_clients, start=1):
        player_list_message += f"Player {idx}: {player_name}\n"

    first_question = qm.get_random_question()
    current_question = welcome_message + player_list_message + "==\nTrue or False: " + first_question + "\n"
    print(MAGENTA + current_question + RESET)
    correct_answer = qm.get_correct_answer()
    correct_answer = [str(element) for element in correct_answer]
    round_event.set()


def broadcast_question():
    """
    Broadcasts a question to all the players simultaneously.
    """
    global correct_players, current_question, correct_answer, qm, round_event
    with connected_clients_lock:
        current_question = qm.get_random_question()
        current_question = (f"\nRound {General_round}, played by {' and '.join(list(correct_players))}:\nTrue or False:"
                          f" {current_question}\n")
        correct_answer = qm.get_correct_answer()
        correct_answer = [str(element) for element in correct_answer]
        print(CYAN + current_question + RESET)
        round_event.set()


def evaluate_and_update_scores():
    """
    This function handles the evaluation of the answers given by the players and updating the game state if needed.
    """
    global connected_clients, correct_answers, round_answers, qm, timer_thread_for_response, correct_players,\
        General_round, correct_answer, result_message

    if len(correct_players) == 0:
        correct_players = set()
        print(YELLOW + "No players had answer within the time limit\nGame over!\n" + RESET)
        print(YELLOW + "Game over, sending out offer requests..." + RESET)
        result_message = "No players had answer within the time limit\nGame over!\n"
    if len(correct_players) == 1:
        correct_players = set()
        print(YELLOW + "Only one player in the game\nGame over!\n" + RESET)
        print(YELLOW + "Game over, sending out offer requests..." + RESET)
        result_message = "Only one player in the game\nGame over!\n"
    elif len(correct_players) > 1:
        with round_answers_lock:
            who_is_correct = ""
            copy_of_correct_players = correct_players.copy()
            for player_name, (answer, correct) in round_answers.items():
                if player_name in correct_players:
                    if str(answer) in correct:
                        correct_answers += 1
                        who_is_correct += f"\n{player_name} is correct!"
                    else:
                        correct_players.remove(player_name)
                        incorrect = f"\n{player_name} is incorrect!" + who_is_correct
                        who_is_correct = incorrect
        if len(correct_players) == 0:
            correct_players = copy_of_correct_players.copy()
        if len(correct_players) == 1:
            who_is_correct += " " + list(correct_players)[0] + ' Wins!'
        print(who_is_correct)
        result_message = who_is_correct


def send_results(result_message, client_socket):
    """
    Sends the results (result_message) to all the players in the game.
    """
    try:
        client_socket.sendall(result_message.encode())
    except Exception as e:
        print(f"Error sending message to client: {e}")


def handle_answers(correct_answer,player_name, client_socket):
    """
    A helper function that handles the gathering of answers from the players.
    """
    global correct_players, connected_clients, round_answers_lock, round_answers

    try:
        client_socket.settimeout(10)
        answer = client_socket.recv(1024).decode()
        with round_answers_lock:
            round_answers[player_name] = (answer, correct_answer)
    except:
        with correct_players_lock:
            if player_name in correct_players:
                print(f"Timeout waiting for answer from {player_name}")
                correct_players.remove(player_name)


def declare_winner(winner, player_name, client_socket):
    """
    A helper function that sends a message to the players about who won the game.
    """
    global General_round, correct_players, connected_clients

    try:
        client_socket.sendall(f"Game over!\nCongratulations to the winner: {winner}\n"
                              f"The total number of correct answers from all clients this round: {correct_answers}".encode())
    except Exception as e:
        print(f"Error declaring winner: {e}")


port_number = find_free_port()
udp_broadcast_thread = threading.Thread(target=start_udp_broadcast)
udp_broadcast_thread.start()
accept_tcp_connections()