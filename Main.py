from Server import Server
import threading

"""The starting of the game server"""
server = Server()
server.start_udp_broadcast()
udp_broadcast_thread = threading.Thread(target=server.start_udp_broadcast())
udp_broadcast_thread.start()
server.accept_tcp_connections()
