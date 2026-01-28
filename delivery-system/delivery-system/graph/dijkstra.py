"""
Dijkstra's Algorithm - Baseline Shortest Path
==============================================
Standard implementation of Dijkstra's algorithm for finding shortest paths
in a weighted graph. Uses a priority queue (min-heap) for efficiency.

Time Complexity: O((V + E) log V)
Space Complexity: O(V)

This serves as the baseline algorithm for comparison.
"""

import heapq
from typing import Dict, List, Tuple, Optional
from graph.road_graph import RoadGraph


class Dijkstra:
    """
    Standard Dijkstra's algorithm implementation.
    Finds shortest path based on road distance only.
    """
    
    def __init__(self, graph: RoadGraph):
        """
        Initialize Dijkstra solver with road graph.
        
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
        Find shortest path from start to end node using Dijkstra's algorithm.
        
        Algorithm:
        1. Initialize distances to infinity, start to 0
        2. Use min-heap priority queue for node selection
        3. For each node, update neighbor distances if shorter path found
        4. Track parent pointers for path reconstruction
        
        Args:
            start: Starting node ID
            end: Ending node ID
            
        Returns:
            Tuple of (path_nodes, total_distance, stats)
            path_nodes: List of node IDs from start to end
            total_distance: Total path distance in km
            stats: Dictionary with algorithm statistics
        """
        # Reset statistics
        self.stats = {
            'nodes_explored': 0,
            'edges_examined': 0,
            'path_length': 0,
            'explored_edges': []  # For visualization
        }
        
        # Initialize data structures
        distances = {node_id: float('inf') for node_id in self.graph.nodes.keys()}
        distances[start] = 0
        
        # Parent pointers for path reconstruction
        parents = {node_id: None for node_id in self.graph.nodes.keys()}
        
        # Priority queue: (distance, node_id)
        pq = [(0, start)]
        
        # Set of visited nodes
        visited = set()
        
        print(f"\n[Dijkstra] Finding path from Node {start} to Node {end}")
        
        while pq:
            # Extract node with minimum distance (greedy choice)
            current_dist, current_node = heapq.heappop(pq)
            
            # Skip if already visited (handles duplicate entries in PQ)
            if current_node in visited:
                continue
            
            visited.add(current_node)
            self.stats['nodes_explored'] += 1
            
            # Goal reached
            if current_node == end:
                print(f"[Dijkstra] Goal reached! Distance: {current_dist:.3f}km")
                break
            
            # Explore neighbors
            for neighbor, edge_dist, metadata in self.graph.get_neighbors(current_node):
                self.stats['edges_examined'] += 1
                
                # Track explored edges for visualization
                self.stats['explored_edges'].append((current_node, neighbor))
                
                # Skip if already visited
                if neighbor in visited:
                    continue
                
                # Calculate new distance through current node
                new_dist = distances[current_node] + edge_dist
                
                # Update if we found a shorter path
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    parents[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        path = self._reconstruct_path(parents, start, end)
        total_distance = distances[end]
        
        if path:
            self.stats['path_length'] = len(path)
            print(f"[Dijkstra] Path found: {' -> '.join(map(str, path))}")
            print(f"[Dijkstra] Total distance: {total_distance:.3f}km")
            print(f"[Dijkstra] Nodes explored: {self.stats['nodes_explored']}")
            print(f"[Dijkstra] Edges examined: {self.stats['edges_examined']}")
        else:
            print(f"[Dijkstra] No path exists from {start} to {end}")
            total_distance = float('inf')
        
        return path, total_distance, self.stats
    
    def _reconstruct_path(self, parents: Dict, start: int, end: int) -> List[int]:
        """
        Reconstruct path from parent pointers.
        
        Args:
            parents: Dictionary of parent pointers
            start: Start node ID
            end: End node ID
            
        Returns:
            List of node IDs representing the path, or empty list if no path
        """
        # Check if path exists
        if parents[end] is None and end != start:
            return []
        
        # Build path backwards from end to start
        path = []
        current = end
        
        while current is not None:
            path.append(current)
            current = parents[current]
        
        # Reverse to get start -> end
        path.reverse()
        
        return path
    
    def get_statistics(self) -> Dict:
        """Get algorithm performance statistics."""
        return self.stats.copy()


if __name__ == "__main__":
    # Test Dijkstra algorithm
    graph = RoadGraph('../data/roads.json')
    dijkstra = Dijkstra(graph)
    
    # Test path finding
    start_node = 0  # Creek Road Junction
    end_node = 13   # Malindi
    
    path, distance, stats = dijkstra.find_shortest_path(start_node, end_node)
    
    print("\n=== Path Details ===")
    for i, node_id in enumerate(path):
        node = graph.get_node(node_id)
        print(f"Step {i+1}: Node {node_id} - {node['name']}")
