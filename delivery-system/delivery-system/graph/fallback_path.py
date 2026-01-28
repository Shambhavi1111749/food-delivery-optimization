"""
Fallback Path Algorithm - Second-Best Route
============================================
Finds an alternative route when the primary route is blocked or undesirable.

Algorithm:
1. Find shortest path using Dijkstra
2. Temporarily remove edges from shortest path
3. Find new shortest path (this will be different)
4. Restore removed edges

Use case: Road closures, accidents, or user preference for alternate routes
"""

from typing import List, Tuple, Dict, Optional
from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra


class FallbackPath:
    """
    Finds alternative (second-best) routes by temporarily blocking primary path.
    """
    
    def __init__(self, graph: RoadGraph):
        """
        Initialize fallback path finder.
        
        Args:
            graph: RoadGraph instance
        """
        self.graph = graph
        self.dijkstra = Dijkstra(graph)
    
    def find_alternative_path(self, start: int, end: int, 
                            blocked_edges: List[Tuple[int, int]] = None) -> Tuple[List[int], float, Dict]:
        """
        Find alternative path avoiding specified edges.
        
        Args:
            start: Starting node ID
            end: Ending node ID
            blocked_edges: List of (from, to) tuples to avoid
            
        Returns:
            Tuple of (path, distance, stats)
        """
        if blocked_edges is None:
            blocked_edges = []
        
        print(f"\n[FallbackPath] Finding alternative path from {start} to {end}")
        if blocked_edges:
            print(f"[FallbackPath] Blocking {len(blocked_edges)} edges")
        
        # Temporarily remove blocked edges
        removed_edges_data = []
        for from_node, to_node in blocked_edges:
            # Store edge data before removal
            edge_data = self._get_edge_data(from_node, to_node)
            if edge_data:
                removed_edges_data.append((from_node, to_node, edge_data))
                self.graph.remove_edge(from_node, to_node)
        
        # Find path with blocked edges removed
        path, distance, stats = self.dijkstra.find_shortest_path(start, end)
        
        # Restore removed edges
        for from_node, to_node, edge_data in removed_edges_data:
            self._restore_edge(from_node, to_node, edge_data)
        
        if path:
            print(f"[FallbackPath] Alternative found: {distance:.3f}km")
        else:
            print(f"[FallbackPath] No alternative path exists")
        
        return path, distance, stats
    
    def find_k_shortest_paths(self, start: int, end: int, k: int = 2) -> List[Tuple[List[int], float]]:
        """
        Find k shortest paths from start to end.
        
        Algorithm (Yen's k-shortest paths simplified):
        1. Find shortest path
        2. For each edge in shortest path, find path without that edge
        3. Keep k best paths
        
        Args:
            start: Starting node
            end: Ending node
            k: Number of paths to find
            
        Returns:
            List of (path, distance) tuples, sorted by distance
        """
        print(f"\n[FallbackPath] Finding {k} shortest paths from {start} to {end}")
        
        paths = []
        
        # Find primary path
        primary_path, primary_dist, _ = self.dijkstra.find_shortest_path(start, end)
        if not primary_path:
            return []
        
        paths.append((primary_path, primary_dist))
        
        # Find alternative paths by blocking edges from primary
        for i in range(len(primary_path) - 1):
            blocked_edge = (primary_path[i], primary_path[i+1])
            alt_path, alt_dist, _ = self.find_alternative_path(start, end, [blocked_edge])
            
            if alt_path and alt_path != primary_path:
                # Check if this path is new
                is_new = True
                for existing_path, _ in paths:
                    if alt_path == existing_path:
                        is_new = False
                        break
                
                if is_new:
                    paths.append((alt_path, alt_dist))
        
        # Sort by distance and return top k
        paths.sort(key=lambda x: x[1])
        paths = paths[:k]
        
        print(f"[FallbackPath] Found {len(paths)} unique paths")
        for idx, (path, dist) in enumerate(paths):
            print(f"  Path {idx+1}: {dist:.3f}km ({len(path)} nodes)")
        
        return paths
    
    def _get_edge_data(self, from_node: int, to_node: int) -> Optional[Dict]:
        """Get edge data before removal."""
        for neighbor, dist, metadata in self.graph.get_neighbors(from_node):
            if neighbor == to_node:
                return {
                    'distance': dist,
                    'metadata': metadata
                }
        return None
    
    def _restore_edge(self, from_node: int, to_node: int, edge_data: Dict):
        """Restore a previously removed edge."""
        dist = edge_data['distance']
        metadata = edge_data['metadata']
        
        # Add edge back (bidirectional)
        self.graph.adj_list[from_node].append((to_node, dist, metadata))
        self.graph.adj_list[to_node].append((from_node, dist, metadata))
        
        # Restore metadata
        self.graph.edge_metadata[(from_node, to_node)] = metadata
        self.graph.edge_metadata[(to_node, from_node)] = metadata


if __name__ == "__main__":
    # Test fallback path
    graph = RoadGraph('../data/roads.json')
    fallback = FallbackPath(graph)
    
    start_node = 0
    end_node = 13
    
    # Find multiple paths
    paths = fallback.find_k_shortest_paths(start_node, end_node, k=3)
    
    print("\n=== Path Comparison ===")
    for idx, (path, dist) in enumerate(paths):
        print(f"\nPath {idx+1} ({dist:.3f}km):")
        node_names = [graph.get_node(n)['name'] for n in path]
        print(f"  Route: {' -> '.join(node_names)}")
    
    # Test with blocked edge
    print("\n\n=== Testing Road Closure ===")
    print("Simulating closure of edge 0-1 (Creek Road)")
    alt_path, alt_dist, _ = fallback.find_alternative_path(0, 13, blocked_edges=[(0, 1)])
    print(f"Alternative route: {' -> '.join(map(str, alt_path))}")
    print(f"Distance: {alt_dist:.3f}km")
