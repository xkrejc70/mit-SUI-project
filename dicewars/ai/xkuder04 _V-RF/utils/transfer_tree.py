from .debug import debug_print, DP_FLAG

class transfer_tree:
    def __init__(self, dist_dict):
        self.dist_dict = dist_dict

    def find_best_transfer(self, start_depth = 0, available_steps = 6):
        roots = []
        for area in self.dist_dict.get(start_depth, []):
            if area.dice < 8:
                roots.append(node(area, start_depth, available_steps, self.dist_dict))
        min_route = []
        min_space = 420
        min_route_len = 420
        for root in roots:
            route, space = self.bfs(root)
            if space == min_space:
                if len(route) < min_route_len:
                    min_route = route
                    min_space = space
                    min_route_len = len(route)
            if space < min_space:
                min_route = route
                min_space = space
                min_route_len = len(route)
        debug_print(f"Min_space: {min_space}", DP_FLAG.TRANSFER_VECTOR)
        return min_route

    def bfs(self, root):
        queue = [root]
        min_space = 8
        min_route = []
        while len(queue) > 0:
            curr_node = queue.pop()
            curr_node.create_childs()
            if curr_node.space < min_space:
               min_space = curr_node.space
               min_route = curr_node.transfers
            if min_space <= 0:
                break
            for child in curr_node.child_nodes:
                child.set_space(curr_node.space)
                queue.append(child)
        
        return min_route, min_space


class node:
    def __init__(self, area, depth, available_steps, dist_dict, transfers = []):
        self.area = area
        self.name = area.name
        self.depth = depth
        self.available_steps = available_steps
        self.dist_dict = dist_dict
        self.transfers = transfers
        self.space = 8 - area.dice

    def set_space(self, space):
        self.space = space - self.area.dice + 1

    def create_childs(self):
        self.child_nodes = []
        child_depth = self.depth + 1
        if self.available_steps <= 0:
            return

        if self.depth > 1:
            for area in self.dist_dict.get(self.depth,[]):
                if self.area.dice < 8 and area.name in self.area.get_adjacent_areas_names():
                    self.child_nodes.append(node(area, self.depth, self.available_steps - 1, self.dist_dict, self.transfers + [(area.name, self.name)]))

        for area in self.dist_dict.get(child_depth,[]):
            if self.area.dice < 8 and area.name in self.area.get_adjacent_areas_names():
                self.child_nodes.append(node(area, child_depth, self.available_steps - 1, self.dist_dict, self.transfers + [(area.name, self.name)]))
