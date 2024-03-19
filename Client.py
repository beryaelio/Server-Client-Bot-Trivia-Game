import socket
import struct
from Statistics import Statistics
import time
import Input

'''ANSI'''
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
RESET = "\033[0m"
player_name = "Niki\n"
Stati = Statistics()

'''Connecting to server'''


def listen_for_offers():
    """
     Listen for offers from the server and send data to the connect_to_server() function
     once a connection offer is received.
     It will construct the data for the connection according to the project's requirements.

     input - nothing, we just wait for the server to send data for connection.

     output - nothing, we just gather the data, and send it in the correct way
     to the connect_to_server() to establish connection.

     the data received from the server has to be constructed in the following way:
     Magic cookie (4 bytes): 0xabcddcba, Message type (1 byte), ->
     Server name (32 character string, Unicode encoded), Server port (2 bytes)
     if the data is not constructed in this way then we don't connect to the sever.
    """
    print(YELLOW + "Client started, listening for offer requests..." + RESET)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind(("", 13117))

    while True:
        data, addr = client_socket.recvfrom(1024)
        try:
            magic_cookie, message_type, server_name, server_port = struct.unpack('!Ib32sH', data)
            server_name = server_name.decode('utf-8').rstrip()
            if magic_cookie == 0xabcddcba and message_type == 0x2:
                print(GREEN + f"Received offer from server '{server_name}' at address {addr[0]}, attempting to connect..." + RESET)
                time.sleep(1)
                connect_to_server(addr[0], server_port)
        except struct.error as e:
            print(f"Error unpacking data: {e}")


def connect_to_server(server_ip, server_port):
    """
    Connects to the server and starts calls the game_mode() function to start the game.
    :param server_ip: the IP address of the server we want to connect to.
    :param server_port: the port address of the server we want to connect to.
    """
    global player_name
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((server_ip, server_port))
        print(BLUE + "Connected to the server." + RESET)
        sock.sendall(player_name.encode())

        try:
            while True:
                time.sleep(0.5)
                game_mode(sock)
        except Exception as e:
            print(f"An error occurred during the game: {e}")


'''Playing the game'''


def game_mode(sock):
    """
    The game mode is what runs the game itself.
    The messages that the client receives once the game starts are being sorted (with if clauses)
    and the client "acts" according to the messages content.
    If the message is a question then it will call the get_input_with_timeout(10) method of the Input file.
    That function returns the input and if it's not None it will send it back.
    """
    global player_name, Stati
    viewer_player = 0
    count_correct_answers = 0
    count_num_rounds = 1
    try:
        server_msg = sock.recv(1024).decode()
        flag = 0
        while True:
            if flag != 0:
                sock.settimeout(40)
                server_msg = sock.recv(1024).decode()
            if flag == 0:
                flag = 1
            print(CYAN + server_msg + RESET)
            if player_name.lower().strip('\n') + " is correct" in server_msg.lower():
                count_correct_answers += 1
            if Stati.extract_round_number(server_msg) :
                count_num_rounds = Stati.extract_round_number(server_msg)
            if "game over" in server_msg.lower():
                percentage = 100 * (count_correct_answers / count_num_rounds)
                print("Your success rate: " + str(percentage) + " %")
                print("Server disconnected, listening for offer requests...")
                listen_for_offers()
            elif "true or false" in server_msg.lower():
                if viewer_player == 0:
                    answer = Input.get_input_with_timeout(10)
                    if answer is not None:
                        sock.sendall(answer.strip().encode())
                        print('Your answer is: ' + str(answer))
                    else:
                        print("You did not answer in the time limit, you are assigned as viewer")
                        viewer_player = 1
            elif player_name.lower().strip('\n') + " is incorrect" in server_msg.lower() \
                    and "is correct" in server_msg.lower():
                viewer_player = 1
    except Exception as e:
        print(MAGENTA + "Disconnected from server." + RESET)
        print(RED + f"An error occurred during the game: {e}" + RESET)

        listen_for_offers()


listen_for_offers()
