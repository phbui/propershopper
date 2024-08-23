## Installing
To install the agent, clone the following repo:

```
git clone https://github.com/marlow-fawn/propershopper.git
```

## Running

To run the standard agent, use:
```
<python-command> socket_agent_proj.py
```

To run the waiting agent, use:
```
<python-command> socket_agent_proj_wait.py
```

## Structure
The agent begins in an initialization phase, followed by a hierarchical architecture consisting of:

After initialization, the agent has the follows this hierarchical architecture:
1. State machine
2. Planned navigation
3. Reactive navigation

### Initialization
The agent begins by initializing its environment, including:
1. Reading the initial state of the world
2. Populating a set of relevant locations (such as shelves, checkouts, etc)
3. Populating its shopping list
4. Set various flags for use in the state machine.

### State Machine
The state machine lives in `socket_agent_proj.py` in the `transition()` method.
It handles getting a cart, iterating over the shopping list, and exiting. 


The state machine's states are:
- done
- no container
- empty shopping list
- have item

The state machine's transitions are:
- get_container
- get_item
- add_to_container
- exit
- nop (no action)

These transitions are made up of primitive actions, namely variations of `goto` and `interact`

There is an additional state and action `put_back_item` to account for stochastic or novel results from the `get_item` action.

A state machine was chosen as the top level controller to keep the agent robust against external changes, as the next
action taken is always dependent on the most recent state of the world.

### Planned Navigation
The agent uses A* to navigate to different areas of the store, which are represented as nodes in the graph. 
These areas were hand-crafted.
The weight of each edge represents an area's "business", meaning the agent will prefer less populated paths.


As a top level controller, A* would be susceptible to external state changes.
As a low level controller, planning times could be very long.
As such, A* was chosen as a mid level controller to allow informed decision making about navigation goals. 
These decisions improve norm adherence without several of the drawbacks of a typical planning agent.

### Reactive Navigation

The agent uses a hand-crafted reactive controller for low level navigation. 
It projects local collisions based off the most recent state of the world, allowing it to navigate without collisions.
This controller was chosen for its speed and resilience to external state changes, either by stochasticity or dynamic obstacles (other agents).

## Previous Designs

- A* was attempted as a solo navigation planner in two iterations. Planning times were too high to properly take into account dynamic obstacles. In addition, any stochasticity would have disrupted the plan.
- Use of a cart was attempted, but drastically changed the observation space required for navigation. Even with proper observation, the likelihood of norm violations with a cart are much greater than with a basket, so a basket is solely used.