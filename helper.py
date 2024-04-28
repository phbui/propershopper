from enums.direction import Direction
from shapely.geometry import Polygon, Point
from shapely.ops import nearest_points


def obj_collision(obj,  x_position, y_position, x_margin=0.55, y_margin=0.55):
    return obj.position[0] - x_margin < x_position < obj.position[0] + obj.width + x_margin and \
           obj.position[1] - y_margin < y_position < obj.position[1] + obj.height + y_margin


def overlap(x1, y1, width_1, height_1, x2, y2, width_2, height_2):
    return not (x1 > x2 + width_2 or x2 > x1 + width_1 or y1 > y2 + height_2 or y2 > y1 + height_1)


def objects_overlap(obj1, obj2):
    return overlap(obj1.position[0], obj1.position[1], obj1.width, obj1.height,
                   obj2.position[0], obj2.position[1], obj2.width, obj2.height)


def pos_collision(x1, y1,  x2, y2, x_margin, y_margin):
    return x1 - x_margin < x2 < x1 + x_margin and y1 - y_margin < y2 < y1 + y_margin


def can_interact_default(obj, player, range=0.5):
    if player.direction == Direction.NORTH:
        return obj.collision(player, player.position[0], player.position[1] - range)
    elif player.direction == Direction.SOUTH:
        return obj.collision(player, player.position[0], player.position[1] + range)
    elif player.direction == Direction.WEST:
        return obj.collision(player, player.position[0] - range, player.position[1])
    elif player.direction == Direction.EAST:
        return obj.collision(player, player.position[0] + range, player.position[1])
    return False

def is_visible(player_vision, obj_position, obj_height, obj_width):
    basket_points = [(obj_position), 
                    (obj_position[0], obj_position[1] + obj_height), 
                    (obj_position[0] + obj_width, obj_position[1] + obj_height),
                    (obj_position[0] + obj_width, obj_position[1])]
    basket_rectangle = Polygon(basket_points) 
    return basket_rectangle.intersection(player_vision)

def closest_relative_point(intersection, player_position):
    closest_point = list(nearest_points(intersection, Point(player_position)))[0]
    closest_relative = (closest_point.x - player_position[0], closest_point.y - player_position[1])
    return closest_relative
