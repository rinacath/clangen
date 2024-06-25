from pygame import (
    Rect,
    Color
)
import pygame.gfxdraw
import pygame_gui
from math import (
    pi,
    sin,
    cos,
    trunc
)
import pydash
from typing import List
from warp import warp
from random import (choice, random, randrange)

first_pass = True
pi2 = 2 * pi

class HexTile:
    def __init__(self, radius, center, coords=(0, 0)) -> None:
        self.radius = radius
        self.center = center
        self.points = [(cos(i / 6 * pi2) * radius + center[0], sin(i / 6 * pi2) * radius + center[1]) for i in range(0, 6)]
        self.color = None
        self.coords = coords
        self.groups = []

        self.sides:List[HexTile] = [
            None,
            None,
            None,
            None,
            None,
            None,
        ]

        x_vals = pydash.map_(self.points, lambda point: point[0])
        y_vals = pydash.map_(self.points, lambda point: point[1])

        self.height = max(y_vals) - min(y_vals)
        self.width = max(x_vals) - min(x_vals)

        self.position = Rect(min(x_vals), min(y_vals), self.width, self.height)


    def get_tile_center_for_side(self, side):
        side_match = (side + 2) % 6
        x = cos(side / 6 * pi2) * self.radius + self.center[0] - (cos(side_match / 6 * pi2) * self.radius)
        y = sin(side / 6 * pi2) * self.radius + self.center[1] - ((sin(side_match / 6 * pi2) * self.radius))
        return (x, y)


    @staticmethod
    def est_tile_center_for_side(center, radius:int):
        side = 0
        side_match = (side + 2) % 6
        x = cos(side / 6 * pi2) * radius + center[0] - (cos(side_match / 6 * pi2) * radius)
        y = sin(side / 6 * pi2) * radius + center[1] - ((sin(side_match / 6 * pi2) * radius))
        return (x, y)


    def draw(self, surface, color=Color("black"), width=1):
        if self.color is not None:
            pygame.draw.polygon(surface, self.color, self.points)
        pygame.draw.polygon(surface, color, self.points, width)


    def __eq__(self, value: object) -> bool:
        if not isinstance(value, HexTile):
            return False
        return (self.center[0] == value.center[0]
                and self.center[1]== value.center[1]
                and self.radius == value.radius)


    def set_side(self, other, side:int):
        if (side > 5 or side < 0):
            return
        self.sides[side] = other


    def get_side(self, side:int):
        return self.sides[side]

    def get_real_sides(self):
        return pydash.filter_(self.sides, lambda side: side is not None)


    def get_random_side(self):
        sides = pydash.filter_(self.sides, lambda side: side is not None)
        if len(sides) > 0:
            return choice(pydash.filter_(self.sides, lambda side: side is not None))

        return None


    def get_shared_side(self, other):
        for i in range(0, 6):
            if self.points[i] in other.points:
                return i

        return None


    def is_edge_tile(self):
        for side in self.sides:
            if side is None:
                return True

        return False


    def add_group(self, group_name):
        if group_name not in self.groups:
            self.groups.append(group_name)


    def remove_group(self, group_name):
        if group_name in self.groups:
            self.groups.remove(group_name)

    def is_in_group(self, group_name):
        return group_name in self.groups



    @staticmethod
    def calc_size(radius):
        points = [(cos(i / 6 * pi2) * radius + 0, sin(i / 6 * pi2) * radius + 0) for i in range(0, 6)]
        y_vals = pydash.map_(points, lambda point: point[1])
        x_vals = pydash.map_(points, lambda point: point[0])
        return {
            "width": max(x_vals) - min(x_vals),
            "height": max(y_vals) - min(y_vals)
        }


    @staticmethod
    def match_side(side):
        return (side + 2) % 6


class MapResource:
    def __init__(self) -> None:
        pass


class MapTile(HexTile):
    # TODO: move these.
    resource_colors = {
        "water": Color("blue"),
        "dense_prey": Color("green")
    }

    def __init__(self, radius, center, coords, resource:str=None) -> None:
        super().__init__(radius, center, coords)
        self.resources = []

        if resource is not None:
            self.add_resource(resource)


    def add_resource(self, resource:str) -> None:
        self.resources.append(resource)
        if resource in MapTile.resource_colors:
                self.color = MapTile.resource_colors[resource]


    def has_resource(self, resource:str) -> bool:
        return resource in self.resources


    def get_random_side_without_resource(self, resource):
        sides = pydash.filter_(self.sides, lambda side: (side is not None) and (not side.has_resource(resource)))

        # Try and prefer tiles that aren't also adjacent to the resource or the edge of the map
        if len(sides) > 0:
            return pydash.sort_by(sides, lambda side: len(side.get_sides_with_resource(resource)))[0]

        return None

    def get_sides_with_resource(self, resource):
        return pydash.filter_(self.sides, lambda side: (side is not None) and (side.has_resource(resource)))


class HexMap:
    def __init__(self, position:Rect, hex_size) -> None:
        self.position = position
        self.surface = pygame.Surface((position.width, position.height))

        # Determine how many tiles can fit in the given position
        tile_size = MapTile.calc_size(hex_size)
        self.height = trunc(position.height / (tile_size["height"]))
        self.hex_size = hex_size

        # Fill in tiles
        self.tiles:List[MapTile] = []

        offset = MapTile.est_tile_center_for_side((0, 0), hex_size)

        side = 1
        side_match = (side + 2) % 6
        x = cos(side / 6 * pi2) * hex_size - (cos(side_match / 6 * pi2) * hex_size)
        y = sin(2 / 6 * pi2) * hex_size - ((sin(4 / 6 * pi2) * hex_size))

        self.width = trunc(position.width / x) - 1

        width = x * self.width
        height = y * self.height
        print(width, height)

        for j in range(0, self.height):
            for i in range(0, self.width):
                offset = (y/2) if i % 2 else 0
                centerx =  hex_size + x * i
                centery = (y/2) + (j * y) + offset
                center = (centerx, centery)
                new_tile = MapTile(hex_size, center, (j, i))
                self.tiles.append(new_tile)

        for tile in self.tiles:
            for other_tile in self.tiles:
                if tile != other_tile:
                    shared_side = tile.get_shared_side(other_tile)
                    if shared_side is not None:
                        tile.set_side(other_tile, shared_side)
                        other_tile.set_side(tile, MapTile.match_side(shared_side))


    def draw(self):
        pygame.draw.rect(self.surface, Color("white"), Rect(0, 0, self.position.width, self.position.height))
        for tile in self.tiles:
            tile.draw(self.surface, Color("black"), 3)

    def get_random_tile(self) -> HexTile:
        return choice(self.tiles)


class GameMap(HexMap):
    def __init__(self, position: Rect, hex_size) -> None:
        super().__init__(position, hex_size)
        self.tiles:List[MapTile]
        self.generate()


    def generate(self):
        """Initializes the map with basic geographical elements"""

        # Lay down water
        # self._fill_resource_tiles(10, 15, "water", 999)

        self.define_clan_borders(4)


        # Choose some tiles for dense prey


    def get_tile_at(self, coords) -> MapTile:
        return pydash.find(self.tiles, lambda tile: tile.coords[0] == coords[0] and tile.coords[1] == coords[1])


    def get_corner_tile(self, corner_num) -> MapTile:
        if corner_num == 0:
            return self.get_tile_at((0, 0))
        if corner_num == 1:
            return self.get_tile_at((0, self.width - 1))
        if corner_num == 2:
            return self.get_tile_at((self.height - 1, 0))
        else:
            return self.get_tile_at((self.width - 1, self.height -1))


    def define_clan_borders(self, clan_count):
        """Split the map into clan territories"""

        colors = [
            Color("orange"),
            Color("red"),
            Color("yellow"),
            Color("green")
        ]

        tiles = self.tiles.copy()
        print(self.height, self.width)

        for i in range(0, clan_count - 1):
            clan_name = f"clan{i}"
            # start_tile = self.get_random_edge_tile(tiles)
            start_tile = self.get_corner_tile(i)
            group = self.get_continuous_group(trunc(len(self.tiles) / clan_count), tiles, start_tile, clan_name)
            tiles = pydash.filter_(tiles, lambda tile: tile not in group)
            print(len(tiles))

            for tile in group:
                tile.color = colors[i]
        clan_name = f"clan{clan_count - 1}"
        group = tiles

        for tile in group:
            tile.color = colors[clan_count - 1]



    def get_surrounded_tiles(self, tiles, group_name, min_sides=6):
        """Returns a list of tiles not in the given group name, with the given number of sides in the group"""
        result = []

        for tile in tiles:
            is_touching_group = False
            if not tile.is_in_group(group_name):
                if len(pydash.filter_(tile.sides, lambda side: side is None)) < 6:
                    sides = []
                    for side in tile.sides:
                        if side is None:
                            sides.append(side)
                        elif side.is_in_group(group_name):
                            sides.append(side)
                            is_touching_group = True
                    if len(sides) >= min_sides and is_touching_group:
                        result.append(tile)

        return result


    def get_continuous_group(self, size, tiles:List[HexTile], start_tile:HexTile, group_name:str="group"):
        """Get a group of tiles that are all touching, of the given size"""
        group_tiles = [start_tile]
        print(f"Adding {size} tiles to {group_name}")

        tile = start_tile
        start_tile.add_group(group_name)
        edge_tiles = []
        while len(group_tiles) < size:
            for side in tile.sides:
                if len(group_tiles) < size and side in tiles:
                    if side is not None and not side.is_in_group(group_name):
                        group_tiles.append(side)
                        side.add_group(group_name)
                        edge_tiles.append(side)

            # Prefer filling in potential gaps
            surrounded_tiles = self.get_surrounded_tiles(edge_tiles, group_name, 5)
            if len(surrounded_tiles) > 0:
                tile = choice(surrounded_tiles)
                group_tiles.append(tile)
                tile.add_group(group_name)
                edge_tiles.remove(tile)
            else:
                if len(edge_tiles) > 0:
                    tile = choice(edge_tiles)
                    edge_tiles.remove(tile)
                else:
                    tile = self.get_random_edge_tile(tiles)
                    group_tiles.append(tile)
                    tile.add_group(group_name)



        return group_tiles


    def get_random_edge_tile(self, tiles, exclude_group_name=None):
        edge_tiles = pydash.filter_(tiles, lambda tile: tile.is_edge_tile() and not tile.is_in_group(exclude_group_name))
        return choice(edge_tiles)


    def _fill_resource_tiles(self, min_tile_count, max_tile_count, resource, max_group_size) -> None:
        total_resource_tiles = 0
        expected_resource_tiles = randrange(min_tile_count, max_tile_count)
        print(f"Expected {resource} tiles: {expected_resource_tiles}")
        while total_resource_tiles < expected_resource_tiles:
            water_source = self.get_random_tile_without_resource(resource)
            water_source.add_resource(resource)
            total_resource_tiles += 1
            next_tile = water_source.get_random_side_without_resource(resource)
            for i in range(0, min(expected_resource_tiles - total_resource_tiles, max_group_size)):
                if next_tile is not None:
                    print(i)
                    total_resource_tiles += 1
                    next_tile.add_resource(resource)
                    next_tile = next_tile.get_random_side_without_resource(resource)

        print(f"Actual {resource} tiles: {total_resource_tiles}")


    def get_random_tile_without_resource(self, resource) -> MapTile:
        tiles = pydash.filter_(self.tiles, lambda tile: tile is not None and not tile.has_resource(resource))
        if len(tiles) > 0:
            return choice(tiles)

        return None




def run():
    pygame.init()
    screen = pygame.display.set_mode((800, 700))
    clock = pygame.time.Clock()
    running = True

    screen.fill(Color("white"))
    hexMap = GameMap(Rect(25, 25, 800 - 50, 700 - 50), 50)

    # Add geographical elements


    hexMap.draw()


    first_pass = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        screen.blit(hexMap.surface, hexMap.position)

        pygame.display.flip()

        first_pass = False
        clock.tick(60)

    pygame.quit()

run()







#  points = [
#             (276, 3),
#             (839, 0),
#             (743, 266),
#             (0,227),
#         ]
#         points = [
#             (hexMap.position.width * .25, hexMap.position.height * 0.006),
#             (hexMap.position.width * .75, 0),
#             (hexMap.position.width * .70, hexMap.position.height * 0.5),
#             (0,hexMap.position.height * 0.4),
#         ]
#         points = [
#             (hexMap.position.width * .50, hexMap.position.height * 0.01),
#             (hexMap.position.width, 0),
#             (hexMap.position.width * .95, hexMap.position.height * 0.75),
#             (0,hexMap.position.height * 0.65),
#         ]