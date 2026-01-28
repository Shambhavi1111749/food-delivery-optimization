"""
Modified Dijkstra's Algorithm - Context-Aware Routing
======================================================
Enhanced Dijkstra that considers multiple factors beyond distance:
- Traffic congestion
- Road quality
- Vehicle type suitability

Edge weight = base_distance × traffic_factor × road_quality_factor × vehicle_factor

This produces more realistic routes that avoid congested or poor-quality roads.
"""

import heapq
from typing import Dict, List, Tuple, Optional
from graph.road_graph import RoadGraph


class ModifiedDijkstra:
    """
    Modified Dijkstra's algorithm with weighted edge costs.
    Considers traffic, road quality, and vehicle type.
    """
    
    # Vehicle penalties for different road types
    VEHICLE_PENALTIES = {
        'boda': {  # Motorcycles - better on narrow roads
            'high_quality': 1.0,
            'medium_quality': 1.1,
            'low_quality': 1.3
        },
        'bajaji': {  # Three-wheelers - need better roads
            'high_quality': 1.0,
            'medium_quality': 1.3,
            'low_quality': 1.8
        }
    }
    
    def __init__(self, graph: RoadGraph, vehicle_type: str = 'boda'):
        """
        Initialize Modified Dijkstra solver.
        
        Args:
            graph: RoadGraph instance
            vehicle_type: 'boda' or 'bajaji'
        """
        self.graph = graph
        self.vehicle_type = vehicle_type
        self.stats = {
            'nodes_explored': 0,
            'edges_examined': 0,
            'path_length': 0
        }
    
    def find_optimal_path(self, start: int, end: int) -> Tuple[List[int], float, Dict]:
        """
        Find optimal path considering traffic, road quality, and vehicle type.
        
        Algorithm enhancements over standard Dijkstra:
        1. Edge weight includes traffic_factor (congestion multiplier)
        2. Edge weight includes quality_factor (road condition)
        3. Edge weight includes vehicle_factor (vehicle suitability)
        
        Args:
            start: Starting node ID
            end: Ending node ID
            
        Returns:
            Tuple of (path_nodes, total_cost, stats)
        """
        # Reset statistics
        self.stats = {
            'nodes_explored': 0,
            'edges_examined': 0,
            'path_length': 0,
            'explored_edges': [],
            'cost_breakdown': {}
        }
        
        # Initialize data structures
        costs = {node_id: float('inf') for node_id in self.graph.nodes.keys()}
        costs[start] = 0
        
        parents = {node_id: None for node_id in self.graph.nodes.keys()}
        
        # Priority queue: (cost, node_id)
        pq = [(0, start)]
        visited = set()
        
        print(f"\n[ModifiedDijkstra] Finding optimal path from Node {start} to Node {end}")
        print(f"[ModifiedDijkstra] Vehicle type: {self.vehicle_type}")
        
        while pq:
            current_cost, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            self.stats['nodes_explored'] += 1
            
            if current_node == end:
                print(f"[ModifiedDijkstra] Goal reached! Total cost: {current_cost:.3f}")
                break
            
            # Explore neighbors with weighted costs
            for neighbor, base_dist, metadata in self.graph.get_neighbors(current_node):
                self.stats['edges_examined'] += 1
                self.stats['explored_edges'].append((current_node, neighbor))
                
                if neighbor in visited:
                    continue
                
                # Calculate weighted edge cost
                edge_cost = self._calculate_edge_cost(base_dist, metadata)
                new_cost = costs[current_node] + edge_cost
                
                if new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parents[neighbor] = current_node
                    heapq.heappush(pq, (new_cost, neighbor))
        
        # Reconstruct path
        path = self._reconstruct_path(parents, start, end)
        total_cost = costs[end]
        
        if path:
            self.stats['path_length'] = len(path)
            
            # Calculate cost breakdown
            actual_distance = self._calculate_actual_distance(path)
            self.stats['cost_breakdown'] = {
                'base_distance': actual_distance,
                'total_cost': total_cost,
                'penalty_ratio': total_cost / actual_distance if actual_distance > 0 else 1.0
            }
            
            print(f"[ModifiedDijkstra] Path: {' -> '.join(map(str, path))}")
            print(f"[ModifiedDijkstra] Base distance: {actual_distance:.3f}km")
            print(f"[ModifiedDijkstra] Weighted cost: {total_cost:.3f}")
            print(f"[ModifiedDijkstra] Penalty ratio: {self.stats['cost_breakdown']['penalty_ratio']:.2f}x")
        else:
            print(f"[ModifiedDijkstra] No path exists")
            total_cost = float('inf')
        
        return path, total_cost, self.stats
    
    def _calculate_edge_cost(self, base_distance: float, metadata: Dict) -> float:
        """
        Calculate weighted edge cost considering multiple factors.
        
        Cost = base_distance × traffic_factor × quality_penalty × vehicle_penalty
        
        Args:
            base_distance: Physical road length in km
            metadata: Edge metadata (traffic_factor, quality, road_name)
            
        Returns:
            Weighted edge cost
        """
        traffic_factor = metadata.get('traffic_factor', 1.0)
        road_quality = metadata.get('quality', 1.0)
        
        # Determine quality category
        if road_quality >= 0.85:
            quality_category = 'high_quality'
        elif road_quality >= 0.75:
            quality_category = 'medium_quality'
        else:
            quality_category = 'low_quality'
        
        # Get vehicle penalty
        vehicle_penalty = self.VEHICLE_PENALTIES[self.vehicle_type][quality_category]
        
        # Calculate total cost
        cost = base_distance * traffic_factor * vehicle_penalty
        
        return cost
    
    def _calculate_actual_distance(self, path: List[int]) -> float:
        """Calculate actual road distance without penalties."""
        total = 0.0
        for i in range(len(path) - 1):
            dist = self.graph.get_road_distance(path[i], path[i+1])
            if dist:
                total += dist
        return total
    
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
    # Test Modified Dijkstra
    graph = RoadGraph('../data/roads.json')
    
    print("=== Testing with Boda (Motorcycle) ===")
    mod_dijkstra_boda = ModifiedDijkstra(graph, vehicle_type='boda')
    path1, cost1, stats1 = mod_dijkstra_boda.find_optimal_path(0, 13)
    
    print("\n=== Testing with Bajaji (Three-wheeler) ===")
    mod_dijkstra_bajaji = ModifiedDijkstra(graph, vehicle_type='bajaji')
    path2, cost2, stats2 = mod_dijkstra_bajaji.find_optimal_path(0, 13)
    
    print("\n=== Comparison ===")
    print(f"Boda path cost: {cost1:.3f}")
    print(f"Bajaji path cost: {cost2:.3f}")
    print(f"Cost difference: {abs(cost1-cost2):.3f}")
