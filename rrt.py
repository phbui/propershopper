import random
import math

class RRT:
    def __init__(self, map_data, start, goal, step_size=0.5, max_iter=1000, buffer=0.5):
        self.map_data = map_data
        self.start = tuple(start)  # Convert to tuple
        self.goal = tuple(goal)    # Convert to tuple
        self.step_size = step_size
        self.max_iter = max_iter
        self.buffer = buffer
        self.tree = {self.start: None}  # Ensure tree uses tuples as keys

    def is_collision_free(self, point):
        x, y = point
        # Check map boundaries
        if not (0 <= x < self.map_data.cols * self.map_data.grid_size and
                0 <= y < self.map_data.rows * self.map_data.grid_size):
            return False
        # Delegate to map's obstacle check
        return not self.map_data.is_obstacle((x, y))

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def sample_point(self):
        # Bias factor (e.g., 10% of the time, sample the goal)
        goal_bias = 0.1
        if random.random() < goal_bias:
            return self.goal  # Directly return the goal
        else:
            # Uniform random sampling
            x = random.uniform(0, self.map_data.cols * self.map_data.grid_size)
            y = random.uniform(0, self.map_data.rows * self.map_data.grid_size)
            return (x, y)

    def nearest_neighbor(self, point):
        return min(self.tree.keys(), key=lambda p: self.distance(p, point))

    def steer(self, from_point, to_point):
        angle = math.atan2(to_point[1] - from_point[1], to_point[0] - from_point[0])
        new_x = from_point[0] + self.step_size * math.cos(angle)
        new_y = from_point[1] + self.step_size * math.sin(angle)
        return (new_x, new_y)

    def reconstruct_path(self, end_point):
        path = []
        current = end_point
        while current is not None:
            path.append(current)
            current = self.tree[current]
        return path[::-1]

    def find_closest_open_space_vertical(self, goal, max_search_distance=10, step=0.5):
        """
        Scan vertically up and down from `goal` to find
        the first collision-free space on the same X coordinate.
        """
        goal_x, goal_y = goal
        # Try offsets in both directions (up/down)
        for i in range(int(max_search_distance / step) + 1):
            # Check upwards (north)
            up_y = goal_y + i * step
            if 0 <= up_y < self.map_data.rows * self.map_data.grid_size:
                if self.is_collision_free((goal_x, up_y)):
                    return (goal_x, up_y)

            # Check downwards (south)
            down_y = goal_y - i * step
            if 0 <= down_y < self.map_data.rows * self.map_data.grid_size:
                if self.is_collision_free((goal_x, down_y)):
                    return (goal_x, down_y)

        # Nothing found within max_search_distance
        return None

    def plan(self):
        """
        Attempt to plan directly to self.goal.
        If that fails, fall back to the closest free space
        on the vertical axis above/below the goal.
        """

        # 1) Normal RRT to the exact goal
        for _ in range(self.max_iter):
            rand_point = self.sample_point()
            nearest = self.nearest_neighbor(rand_point)
            new_point = self.steer(nearest, rand_point)

            if self.is_collision_free(new_point):
                self.tree[new_point] = nearest
                # Check if the goal is within reach
                if self.distance(new_point, self.goal) <= self.step_size:
                    # Connect to the goal
                    self.tree[self.goal] = new_point
                    return self.reconstruct_path(self.goal)

        # If we get here, no direct path was found in max_iter attempts
        # 2) Attempt fallback on vertical axis
        fallback = self.find_closest_open_space_vertical(self.goal)
        if fallback is None:
            # No vertical fallback
            return None

        # Reset the tree for a new plan to the fallback
        self.tree = {self.start: None}
        for _ in range(self.max_iter):
            rand_point = self.sample_point()
            nearest = self.nearest_neighbor(rand_point)
            new_point = self.steer(nearest, rand_point)

            if self.is_collision_free(new_point):
                self.tree[new_point] = nearest
                if self.distance(new_point, fallback) <= self.step_size:
                    self.tree[fallback] = new_point
                    return self.reconstruct_path(fallback)

        # Neither the goal nor fallback was reachable
        return None
