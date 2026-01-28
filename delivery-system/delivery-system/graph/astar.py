"""
A* Search Algorithm - Heuristic-Guided Pathfinding
===================================================
A* combines Dijkstra's guarantee of optimality with heuristic guidance
to find shortest paths more efficiently.

Key difference from Dijkstra:
- Priority: f(n) = g(n) + h(n)
  - g(n): actual cost from start to n
  - h(n): heuristic estimate from n to goal

Heuristic: Straight-line distance (Euclidean) - admissible and consistent
This heuristic ONLY guides search; actual routing still uses road graph.

Time Complexity: O((V + E) log V) in practice, often much faster than Dijkstra
"""

import heapq
import math
from typing import Dict, List, Tuple
from graph.road_graph import RoadGraph


class AStar:
    """
    A* search algorithm for shortest path with heuristic guidance.
    """
    
    def __init__(self, graph: RoadGraph):
        """
        Initialize A* solver.
        
        Args:
            graph: RoadGraph instance
        """
        self.graph = graph
        self.stats = {
            'nodes_explored': 0,
            'edges_examined': 0,
            'path_length': 0
        }
    
    def find_shortest_path(self, start: int, end: int) -> Tuple[List[int], float, Dict]:
        """
        Find shortest path using A* algorithm.
        
        Algorithm:
        1. Priority queue ordered by f(n) = g(n) + h(n)
        2. g(n): actual cost from start to n
        3. h(n): straight-line distance heuristic to goal
        4. Heuristic guides search but doesn't affect final path
        
        Args:
            start: Starting node ID
            end: Ending node ID
            
        Returns:
            Tuple of (path_nodes, total_distance, stats)
        """
        # Reset statistics
        self.stats = {
            'nodes_explored': 0,
            'edges_examined': 0,
            'path_length': 0,
            'explored_edges': [],
            'heuristic_savings': 0
        }
        
        # Get goal coordinates for heuristic
        goal_lat, goal_lon = self.graph.get_node_coords(end)
        
        # Initialize data structures
        # g_score: actual cost from start
        g_score = {node_id: float('inf') for node_id in self.graph.nodes.keys()}
        g_score[start] = 0
        
        # f_score: g_score + heuristic
        f_score = {node_id: float('inf') for node_id in self.graph.nodes.keys()}
        f_score[start] = self._heuristic(start, end, goal_lat, goal_lon)
        
        parents = {node_id: None for node_id in self.graph.nodes.keys()}
        
        # Priority queue: (f_score, node_id)
        pq = [(f_score[start], start)]
        visited = set()
        
        print(f"\n[A*] Finding path from Node {start} to Node {end}")
        print(f"[A*] Using Euclidean distance heuristic")
        
        while pq:
            # Extract node with minimum f_score (g + h)
            current_f, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            self.stats['nodes_explored'] += 1
            
            # Goal reached
            if current_node == end:
                print(f"[A*] Goal reached! Distance: {g_score[end]:.3f}km")
                break
            
            # Explore neighbors
            for neighbor, edge_dist, metadata in self.graph.get_neighbors(current_node):
                self.stats['edges_examined'] += 1
                self.stats['explored_edges'].append((current_node, neighbor))
                
                if neighbor in visited:
                    continue
                
                # Calculate tentative g_score
                tentative_g = g_score[current_node] + edge_dist
                
                # Update if better path found
                if tentative_g < g_score[neighbor]:
                    parents[neighbor] = current_node
                    g_score[neighbor] = tentative_g
                    
                    # Calculate f_score with heuristic
                    h_score = self._heuristic(neighbor, end, goal_lat, goal_lon)
                    f_score[neighbor] = tentative_g + h_score
                    
                    heapq.heappush(pq, (f_score[neighbor], neighbor))
        
        # Reconstruct path
        path = self._reconstruct_path(parents, start, end)
        total_distance = g_score[end]
        
        if path:
            self.stats['path_length'] = len(path)
            
            # Calculate heuristic efficiency
            straight_line = self._heuristic(start, end, goal_lat, goal_lon)
            self.stats['heuristic_savings'] = (straight_line / total_distance) if total_distance > 0 else 0
            
            print(f"[A*] Path found: {' -> '.join(map(str, path))}")
            print(f"[A*] Total distance: {total_distance:.3f}km")
            print(f"[A*] Straight-line heuristic: {straight_line:.3f}km")
            print(f"[A*] Nodes explored: {self.stats['nodes_explored']}")
            print(f"[A*] Edges examined: {self.stats['edges_examined']}")
        else:
            print(f"[A*] No path exists")
            total_distance = float('inf')
        
        return path, total_distance, self.stats
    
    def _heuristic(self, node_id: int, goal_id: int, goal_lat: float, goal_lon: float) -> float:
        """
        Calculate heuristic (straight-line distance) from node to goal.
        
        This is an ADMISSIBLE heuristic (never overestimates).
        Used ONLY to guide search - actual routing uses road graph.
        
        Args:
            node_id: Current node
            goal_id: Goal node
            goal_lat: Goal latitude
            goal_lon: Goal longitude
            
        Returns:
            Estimated distance to goal
        """
        node_lat, node_lon = self.graph.get_node_coords(node_id)
        
        # Euclidean distance (approximation)
        # In production, would use Haversine for lat/lon
        dx = node_lat - goal_lat
        dy = node_lon - goal_lon
        
        # Convert to approximate km (rough approximation for visualization)
        # 1 degree ≈ 111km at equator
        dist_km = math.sqrt(dx**2 + dy**2) * 111
        
        return dist_km
    
    def _reconstruct_path(self, parents: Dict, start: int, end: int) -> List[int]:
        """Reconstruct path from parent pointers."""
        if parents[end] is None and end != start:
            return []
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = parents[current]
        path.reverse()
        return path
    
    def get_statistics(self) -> Dict:
        """Get algorithm performance statistics."""
        return self.stats.copy()


if __name__ == "__main__":
    # Test A* algorithm
    graph = RoadGraph('../data/roads.json')
    astar = AStar(graph)
    
    start_node = 0
    end_node = 13
    
    path, distance, stats = astar.find_shortest_path(start_node, end_node)
    
    print("\n=== Path Details ===")
    for i, node_id in enumerate(path):
        node = graph.get_node(node_id)
        print(f"Step {i+1}: Node {node_id} - {node['name']}")
    
    # Compare with Dijkstra
    from graph.dijkstra import Dijkstra
    dijkstra = Dijkstra(graph)
    _, _, dijkstra_stats = dijkstra.find_shortest_path(start_node, end_node)
    
    print("\n=== Algorithm Comparison ===")
    print(f"A* nodes explored: {stats['nodes_explored']}")
    print(f"Dijkstra nodes explored: {dijkstra_stats['nodes_explored']}")
    print(f"Efficiency gain: {(1 - stats['nodes_explored']/dijkstra_stats['nodes_explored'])*100:.1f}%")
