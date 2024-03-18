# Server-Client-Bot Trivia Game
A trivia game you can run locally. Here's the server side, client side and even a bot implementation in python. 

# Flowchart of the files:
The organization of the files

```sql

inputClass.py      Questions.py
|                      |
|                      |
v                      v
Client.py_________>Server.py<________Bot.py
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
Wait for Start Event                                                   |            
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


