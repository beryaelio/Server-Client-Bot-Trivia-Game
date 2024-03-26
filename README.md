# Server-Client-Bot Trivia Game
A trivia game we created in python that you can run locally. Here's the server side, client side and even a bot implementation.

The Player's display:
![image](https://github.com/beryaelio/Server-Client-Bot-Trivia-Game/assets/47675083/e3e5c908-2e48-477b-932a-dcff849c2473)

The Server's display:
![image](https://github.com/beryaelio/Server-Client-Bot-Trivia-Game/assets/47675083/ce3932d3-db4b-4340-8796-2f89a5ce2530)

# Introduction
## Brief Description: 
This is a trivia game of 20 questions about Aston Villa FC.

To answer 'True' you should type 'Y', 'T' or 1. To answer 'False' you should type 'N', 'F' or 0. 

In this project we made 3 main python files: Server.py, Client.py, Bot.py

We also have 4 helper python files: Input.py, Statistics.py, Questions.py and QuestionManager.py

To run the game you need to run the following files: Server.py, Main.py, ClientInstance.py and the Bot.py file.

To run the game you need to run the Server.py first and the ClientInstance.py, Main.py, Bot.py to be players in the game.

## Motivation:
This project was made as part of our 'Data Networking' course in uni. We synchronize and manage udp (for the server) and tcp (for the clients) connections.

This projct taught us a lot about the network, server-client communications and the management of it all. 


# Flowchart of the files:
The organization of the project's files

Server.py - The game class. Sends out connection requests through udp broadcast and listens for tcp connections. After connecting the game starts and the server manages the game run.

Client.py - The player class. Listens for connection requests, connects to the server and then manages the player's interface and game prints.

Bot.py - A bot class that acts like a player. Sends a random answer for each question given. The same as the Client.py file besides it's random answers generator. 

Questions.py - A python file imported in the Server.py file that contains all the questions and their answers.

QuestionManager.py - A python class that manages the randon question 

Statistics.py - Stores and calculates statistics about a player's performance n the game. Imported in the Client.py/Bot.py.

Input.py - Imported in the Client.py/Bot.py. Creates an input dialog for answering questions and manages timeout.

```sql

                                                   Questions.py
                                 Input.py       QuestionManager.py
                                 |                      |
                                 |                      |
                                 v                      v
ClientInstance.py/ ________>  Client.py/  ________>  Server.py
     Main.py                   Bot.py
                                 ^
                                 |
                                 |
                                 Statistics.py
                       
```


# Flowchart of the Server's Executation: 
Here's a flowchart of the server's game run. The game will always look for connections and will try to start over until succeeding


```sql
Start
  |
  v
Initialize Server --> Start UDP Broadcast for game offers
  |
  v
Wait for TCP Connections from Clients
  |
  v                                                  
Accept TCP Connection                                
  |                                                  
  v                                                  
Start Timer for Game Start (reset on new connection) <-----------------,
  |                                                                    |                 
  v                                                                    |                 
Handle Client in a Thread                                              |            
  |                                                                    |                 
  v                                                                    |                 
  Receive Player Name                                                  |            
  |                                                                    |                 
  v                                                                    |                 
Add Player to Connected Clients List                                   |             
  |                                                                    |                 
  v                                                                    |                 
Broadcast the Start Event                                              |            
  |                                                                    |                 
  v                                                                    |                 
Broadcast Question to All Clients <------------------------------------,
  |                                                                    |
  v                                                                    |
Collect Answers                                                        |         
  |                                                                    |
  v                                                                    |
Evaluate and Update Scores                                             |
  |                                                                    |
  v                                                                    |
Declare Round Winner / Update Game State                               |
  |                                                                    |
  v                                                                    |
Check if Game Should Continue                                          |
  |                                                                    |
  v                                                                    |
End Game if Necessary / Prepare for Next Round ------------------------'
```

# Authors

Guy Dulberg | Mickael Zeitoun | Yael Berkovich


