# Server-Client-Bot Trivia Game
A trivia game you can run locally. Here's the server side, client side and even a bot implementation in python. 



# Flowchart of the Server's Executation: 
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
 
