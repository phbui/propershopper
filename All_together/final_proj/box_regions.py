from final_proj.util import *

# @total_ordering
class BoxRegion:
    """Box Region class for fast high level A star"""

    def __init__(self, name:str=None, parent=None, box:dict=None, neighbors:set=None):
        self.name = name
        self.parent = parent
        if box is None:
            self.midpoint = None
        else:
            self.midpoint = (abs(box['westmost'] - box['eastmost']) / 2.0 + box['westmost'], abs(box['southmost'] - box['northmost']) / 2.0 + box['northmost'])
        self.box = box
        self.neighbors = neighbors if neighbors else set()


    def __eq__(self, other):
        if isinstance(other, BoxRegion):
            return self.midpoint == other.midpoint
        return False
    
    def __hash__(self):
        return hash(self.midpoint)

    def __repr__(self):
        return self.name
    
    def add_neighbors(self, neighbors):
        self.neighbors.update(neighbors)
    
    def contains(self, point):
        """Check whether a point is in the box region

        Args:
            point (list | tuple[float, float]): (x, y)
        Returns:
            bool: T for in region
        """
        return loc_in_box(box=self.box, loc=point)
    
    def contains_obj(self, obj:dict):
        """Check whether an object is fully contained within this box region

        Args:
            obj (dict): obj with position, width and height

        Returns:
            bool: True if obj is fully contained
        """
        return obj_in_with_box(obj=obj, box=self.box)
    
    def closest(self, point):
        """Return the closest point in the BoxRegion to the given point

        Args:
            point (list | tuple[float, float]): (x, y)

        Returns:
            tuple|list[float, float]: closest point to (x, y) in region
        """
        closest_x = point[0]
        if point[0] < self.box['westmost']:
            closest_x = self.box['westmost'] + 4 * STEP
        elif point[0] > self.box['eastmost']:
            closest_x = self.box['eastmost'] - 4 * STEP

        closest_y = point[1]
        if point[1] < self.box['northmost']:
            closest_y = self.box['northmost'] + 4 * STEP
        elif point[1] > self.box['southmost']:
            closest_y = self.box['southmost'] - 4 * STEP

        return closest_x, closest_y

    def empty_location(self, width:float, height:float, obs:dict):
        """Provide an unoccupied location inside this BoxRegion that's
        Args:
            width (float): the desired width of the unoccupied region
            height (float): the desired height of the unoccupied region
        """
        pass


NW_corner = BoxRegion(
    name = "NW_corner",
    box = {
        'westmost':-0.6,
        'eastmost':3.25,
        'northmost':1.5,
        'southmost':4.5
    }
)
W_corner = BoxRegion(
    name = "W_corner",
    box = {
        'westmost':-0.6,
        'eastmost':3.25,
        'northmost':7.0,
        'southmost':9.5
    }
)
SW_corner = BoxRegion(
    name = "SW_corner",
    box = {
        'westmost':-0.6,
        'eastmost':3.25,
        'northmost':12.0,
        'southmost':18.51
    }
)
NE_corner = BoxRegion(
    name = "NE_corner",
    box = {
        'westmost':17.6,
        'eastmost':19.75,
        'northmost':1.5,
        'southmost':4.75
    }
)
E_corner = BoxRegion(
    name = "E_corner",
    box = {
        'westmost':17.6,
        'eastmost':19.75,
        'northmost':7.0,
        'southmost':10.75
    }
)
SE_corner = BoxRegion(
    name = "SE_corner",
    box = {
        'westmost':17.6,
        'eastmost':19.75,
        'northmost':13.0,
        'southmost':25.0
    }
)

aisle1 = BoxRegion(
    name = "aisle1",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':2.5,
        'southmost':5.5
    }
)
aisle2 = BoxRegion(
    name = "aisle2",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':6.5,
        'southmost':9.5
    }
)
aisle3 = BoxRegion(
    name = "aisle3",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':10.5,
        'southmost':13.5
    }
)
aisle4 = BoxRegion(
    name = "aisle4",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':14.5,
        'southmost':17.5
    }
)
aisle5 = BoxRegion(
    name = "aisle5",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':18.5,
        'southmost':21.5
    }
)
aisle6 = BoxRegion(
    name = "aisle6",
    box = {
        'westmost':5.5,
        'eastmost':15.5,
        'northmost':22.5,
        'southmost':25
    }
)

W_walkway = BoxRegion(
    name = "W_walkway",
    box = {
        'westmost':3.25,
        'eastmost':5.49,
        'northmost':1.5,
        'southmost':25.0
    }
)
E_walkway = BoxRegion(
    name = "E_walkway",
    box = {
        'westmost':15.51,
        'eastmost':17.6,
        'northmost':1.5,
        'southmost':25.0
    }
)

NW_corner.add_neighbors(neighbors=[W_walkway])
W_corner.add_neighbors(neighbors=[W_walkway])
SW_corner.add_neighbors(neighbors=[W_walkway])
W_walkway.add_neighbors(neighbors=[
    NW_corner, W_corner, SW_corner, aisle1, aisle2, aisle3, aisle4, aisle5, aisle6
])
aisle1.add_neighbors(neighbors=[W_walkway, E_walkway])
aisle2.add_neighbors(neighbors=[W_walkway, E_walkway])
aisle3.add_neighbors(neighbors=[W_walkway, E_walkway])
aisle4.add_neighbors(neighbors=[W_walkway, E_walkway])
aisle5.add_neighbors(neighbors=[W_walkway, E_walkway])
aisle6.add_neighbors(neighbors=[W_walkway, E_walkway])

E_walkway.add_neighbors(neighbors=[
    NE_corner, E_corner, SE_corner, aisle1, aisle2, aisle3, aisle4, aisle5, aisle6
])

NE_corner.add_neighbors(neighbors=[E_walkway])
E_corner.add_neighbors(neighbors=[E_walkway])
SE_corner.add_neighbors(neighbors=[E_walkway])

regions = [
    NW_corner,
    W_corner,
    SW_corner,
    NE_corner,
    E_corner,
    SE_corner,
    W_walkway,
    E_walkway,
    aisle1,
    aisle2,
    aisle3,
    aisle4,
    aisle5,
    aisle6,
]