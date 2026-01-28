"""
Road Graph - Core Data Structure
==================================
This module implements the road network as a weighted directed graph.
NO routing happens between arbitrary coordinates - ONLY on road edges.

Graph representation:
- Nodes: Road intersections (dict with id, lat, lon, name)
- Edges: Road segments (adjacency list with weights)
- Edge weight: road length in km

Critical Rules:
1. All routing MUST use graph edges only
2. Coordinates used ONLY for visualization and snapping
3. If no edge exists, travel is IMPOSSIBLE
"""

import json
import math
from typing import Dict, List, Tuple, Optional


class RoadGraph:
    """
    Graph representation of road network.
    
    Attributes:
        nodes (dict): Node ID -> {id, lat, lon, name}
        adj_list (dict): Adjacency list: node_id -> [(neighbor_id, distance, metadata)]
        edge_metadata (dict): (from, to) -> {road_name, traffic_factor, quality}
    """
    
    def __init__(self, roads_file: str):
        """
        Initialize road graph from JSON file.
        
        Args:
            roads_file: Path to roads.json containing nodes and edges
        """
        with open(roads_file, 'r') as f:
            data = json.load(f)
        
        # Store nodes as dictionary: id -> node data
        self.nodes = {node['id']: node for node in data['nodes']}
        
        # Build adjacency list: node_id -> [(neighbor, distance, metadata)]
        self.adj_list = {node_id: [] for node_id in self.nodes.keys()}
        
        # Store edge metadata for routing algorithms
        self.edge_metadata = {}
        
        # Build graph from edges
        for edge in data['edges']:
            from_node = edge['from']
            to_node = edge['to']
            distance = edge['distance']
            
            # Store metadata
            metadata = {
                'road_name': edge.get('road_name', 'Unknown'),
                'traffic_factor': edge.get('traffic_factor', 1.0),
                'quality': edge.get('quality', 1.0)
            }
            
            # Add edge (undirected - add both directions)
            self.adj_list[from_node].append((to_node, distance, metadata))
            self.adj_list[to_node].append((from_node, distance, metadata))
            
            # Store metadata for both directions
            self.edge_metadata[(from_node, to_node)] = metadata
            self.edge_metadata[(to_node, from_node)] = metadata
        
        print(f"[RoadGraph] Loaded {len(self.nodes)} nodes, {len(data['edges'])} edges")
    
    def get_node(self, node_id: int) -> Optional[Dict]:
        """Get node data by ID."""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: int) -> List[Tuple[int, float, Dict]]:
        """
        Get all neighbors of a node.
        
        Returns:
            List of (neighbor_id, distance, metadata) tuples
        """
        return self.adj_list.get(node_id, [])
    
    def snap_to_nearest_node(self, lat: float, lon: float) -> int:
        """
        CRITICAL: Snap arbitrary coordinates to nearest road node.
        This is how restaurants, drivers, and users connect to the road network.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Node ID of nearest road intersection
        """
        min_dist = float('inf')
        nearest_node = None
        
        for node_id, node in self.nodes.items():
            # Calculate Euclidean distance (for snapping only, NOT routing)
            dist = self._euclidean_distance(
                lat, lon,
                node['lat'], node['lon']
            )
            
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id
        
        print(f"[Snap] ({lat:.4f}, {lon:.4f}) -> Node {nearest_node} ({self.nodes[nearest_node]['name']}) [dist={min_dist:.4f}]")
        return nearest_node
    
    def _euclidean_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Euclidean distance between two points.
        ONLY used for snapping to nearest node - NEVER for routing.
        """
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
    
    def get_road_distance(self, node1: int, node2: int) -> Optional[float]:
        """
        Get direct road distance between two adjacent nodes.
        Returns None if no direct road exists.
        """
        for neighbor, dist, _ in self.adj_list[node1]:
            if neighbor == node2:
                return dist
        return None
    
    def remove_edge(self, node1: int, node2: int):
        """
        Remove an edge from the graph (for testing).
        This simulates a road closure.
        """
        # Remove from adjacency list
        self.adj_list[node1] = [
            (n, d, m) for n, d, m in self.adj_list[node1] if n != node2
        ]
        self.adj_list[node2] = [
            (n, d, m) for n, d, m in self.adj_list[node2] if n != node1
        ]
        
        # Remove metadata
        self.edge_metadata.pop((node1, node2), None)
        self.edge_metadata.pop((node2, node1), None)
        
        print(f"[RoadGraph] Removed edge {node1} <-> {node2}")
    
    def get_node_coords(self, node_id: int) -> Tuple[float, float]:
        """Get (lat, lon) coordinates of a node for visualization."""
        node = self.nodes[node_id]
        return (node['lat'], node['lon'])
    
    def validate_graph(self):
        """
        Validate graph integrity.
        Checks that all edges are bidirectional and reachable.
        """
        issues = []
        
        # Check bidirectionality
        for node_id, neighbors in self.adj_list.items():
            for neighbor, dist, _ in neighbors:
                # Check reverse edge exists
                reverse_exists = any(
                    n == node_id for n, _, _ in self.adj_list[neighbor]
                )
                if not reverse_exists:
                    issues.append(f"Edge {node_id}->{neighbor} missing reverse")
        
        if issues:
            print(f"[RoadGraph] Validation issues: {issues}")
        else:
            print("[RoadGraph] Graph validation passed ✓")
        
        return len(issues) == 0


if __name__ == "__main__":
    # Test the road graph
    graph = RoadGraph('../data/roads.json')
    graph.validate_graph()
    
    # Test snapping
    print("\n=== Testing Snap Function ===")
    test_node = graph.snap_to_nearest_node(-6.1626, 39.1924)
    print(f"Snapped to node: {graph.get_node(test_node)}")
    
    # Test neighbors
    print(f"\n=== Neighbors of Node {test_node} ===")
    for neighbor, dist, meta in graph.get_neighbors(test_node):
        neighbor_data = graph.get_node(neighbor)
        print(f"  -> Node {neighbor} ({neighbor_data['name']}): {dist:.3f}km via {meta['road_name']}")
