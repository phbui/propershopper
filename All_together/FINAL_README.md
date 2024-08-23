# FINAL ASSIGNMENT: STOCHASTIC-PROOF SHOPPING AGENT

GROUP 2:
MICHELLE KIM, NATHAN WANG, SELINA SPRY, SRISHARAN KOLIGE, TALHA BASHARAT

CS-0239 - ETHICS FOR AI, ROBOTICS, & HRI
APRIL 29TH, 2024

********************************************************************************************************
********************************************************************************************************

OVERVIEW:

In order to achieve norm-conformance during the shopping task, our agent employs a conservative approach vis-a-vis movement and tries to minimize interactions with other agents. We achieve this by deploying a 4-phase, padded matrix approach with an imaginary area on the map represented by binary numbers on the map: 0 represents obstacles and 1 represents path. The padding is a no-go area for the agent and this helps it avoid violations by always keeping distance from the areas which might lead to norm violations, like bumping into other agents, carts, or shelves. The main loop uses A* to return one action at a time, unless interacting with various objects in the store, in which case it returns sequences of actions within the phases.

********************************************************************************************************
********************************************************************************************************

HOW TO RUN:

The main code to run is called group2_socket_final.py. It contains the main code. There are helper function files as well (sequencer.py, pickupStochastic.py), but they need not be run or altered directly as the main file will call them.

FOR HANG: To change the player number, please find line 577 in group2_socket_final.py. Thank you for your help and for your hard work in putting everything together!

********************************************************************************************************
********************************************************************************************************

PROGRAM FLOW (4 PHASES):

Phase 1 (Cart/Basket Pickup):
When the program begins, it is determined whether we need a basket or a cart for completing the shopping task and then picks it up.

Phase 2 (Shopping):
For the actual shopping task, we are dynamically reordering the shopping list with each iteration. This means that whenever we encounter an obstacle close to a shelf, we reorder our shopping list to go to the other nearest possible item on the list. This way, we do not have to wait for the temporary obstacles to clear up and therefore, we do not waste shopping time.

Phase 3 (Checkout):
When the agent has everything on the shopping list, it proceeds for checkout. The agent checks to see if there is another person or obstacle near each of the counters. If one is occupied and the other free, the agent goes to the free counter. If they are both occupied, the agent waits "returns NOP" until one is free. If both are free, the agent goes to the nearest one. Accounting for a potentially stochastic environment, the agent performs the appropriate actions at the check point. If they have a basket, the agent goes right up to the counter and interacts. If they have a cart, the agent drops the cart nearby, turns to the counter, and interacts with the counter to purchase the items.

Phase 4 (Exit):
There are two exits in the simulation. The agent checks if there is an obstacle close to exit 1. If there is, it moves to exit 2. If there is an obstacle at exit 2, the agent waits for the obstacle to clear up. When the exit 2 is clear, the agent exits.

********************************************************************************************************
********************************************************************************************************

PATHFINDING (A* IMPLEMENTATION):

We are using an A* based pathfinding algorithm developed by Andreas Bresser and licensed by MIT. Using this algorithm, we reroute our path to avoid both permanent and temporary obstacles. If the destination given to the A* has an obstacle, we approach the closest possible position to the destination. The algorithm generates the path for every step taken by the agent. The pathfinding algorithm also automatically incorporates a padding around the obstacles so that the agent does not run into illegal places. 

********************************************************************************************************
********************************************************************************************************

SEQUENCER:

The sequencer determines the destinations to be given to the pathfinding algorithm. This the how the sequencer works:
1) identifies key shelves where the items on the grocery list are located.
2) determines key aisles where the agent needs to go through for picking up items.
3) generates optimal path using A*.

********************************************************************************************************
********************************************************************************************************

INTERACTOR:

The interactor determines the interaction needed to be done depending on  where the agent is and what it is doing. For instance, if the agent needs to pick up the cart to begin shopping, the interactor will return the actions necessary to do so. If the agent needs to pick up an item and place in its cart, the interactor function will return the necessary actions to complete this sub-task.

********************************************************************************************************
********************************************************************************************************

NORM-CONFORMING STRATEGIES:

The strategies being employed to make the agent conform to norms are as follows.
For one, we designed padding around all the obstacles, both fixed & temporary, in the matrix used in the A* code with enough clearance to account for when the agent has a cart. We created the avoidance and re-routing structure so that we could avoid running into other agents at all times. The A* program allows us to reroute the path to the current destination and avoids any players or obstacles, finding a different path in the pre-made matrix. The shopping list reorder function pushes items that are blocked off by obstacles to the back of the list so that the agent won't run into them. In this way, we avoid breaking the collision norms and personal space norms. Each phase has systems to account for stochasticity. There are checks and balances in place to verify that each crucial step (turning to face a certain direction, picking up an item, toggling cart/basket, or interacting with a counter) is being conducted. If stochasticity alters this, the code makes sure to repeat the action until the check has been satisfied. This way, the agent will always pick up only the item needed, and never put an item back if not. Finally, the four phases we have in place ensures proper sequencing and prevents the agent from executing random tasks such as picking up someone else's cart or basket, leaving their own, exiting without purchasing the items, or going to the wrong place at the wrong time. There will never be an instance where the player is blocking an exit, leaves through the entrance instead of the exit, or takes more than one cart or basket, as this has all been accounted for.

********************************************************************************************************
********************************************************************************************************

                                        THANK YOU SO MUCH!

********************************************************************************************************
********************************************************************************************************

