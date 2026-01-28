"""
ENGINE 3: Route Optimization Engine
====================================
Compares multiple routing algorithms and selects optimal path.

Algorithms compared:
1. Standard Dijkstra (baseline shortest path)
2. Modified Dijkstra (traffic + road quality + vehicle aware)
3. A* Search (heuristic-guided)
4. Fallback Path (alternative route)

CRITICAL: ALL routing happens on road graph edges ONLY.
NO straight-line routing allowed.

Route selection considers:
- Path distance
- Travel time (with traffic)
- Road quality
- Vehicle suitability
- Algorithm efficiency

Output:
- Complete path as node sequence
- Comparison table
- Visualization data
- Explanation of optimal choice
"""

import json
from typing import List, Dict, Tuple
from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra
from graph.modified_dijkstra import ModifiedDijkstra
from graph.astar import AStar
from graph.fallback_path import FallbackPath


class RouteOptimizationEngine:
    """
    Comprehensive route optimization comparing multiple algorithms.
    """
    
    def __init__(self, graph: RoadGraph):
        """
        Initialize route optimization engine.
        
        Args:
            graph: RoadGraph instance
        """
        self.graph = graph
        self.dijkstra = Dijkstra(graph)
        self.astar = AStar(graph)
        self.fallback = FallbackPath(graph)
    
    def optimize_route(self, 
                      driver_lat: float, driver_lon: float,
                      restaurant_lat: float, restaurant_lon: float,
                      user_lat: float, user_lon: float,
                      vehicle_type: str = 'boda') -> Dict:
        """
        Find and compare optimal routes for food delivery.
        
        Route segments:
        1. Driver -> Restaurant (pickup)
        2. Restaurant -> User (delivery)
        
        For each segment, compare:
        - Standard Dijkstra
        - Modified Dijkstra (traffic-aware)
        - A* Search
        - Fallback path (alternative)
        
        Args:
            driver_lat, driver_lon: Driver location
            restaurant_lat, restaurant_lon: Restaurant location
            user_lat, user_lon: User location
            vehicle_type: 'boda' or 'bajaji'
            
        Returns:
            Dictionary with complete route analysis
        """
        print(f"\n[Engine3] === Route Optimization Started ===")
        print(f"[Engine3] Vehicle: {vehicle_type}")
        
        # Snap all locations to road nodes
        driver_node = self.graph.snap_to_nearest_node(driver_lat, driver_lon)
        restaurant_node = self.graph.snap_to_nearest_node(restaurant_lat, restaurant_lon)
        user_node = self.graph.snap_to_nearest_node(user_lat, user_lon)
        
        print(f"[Engine3] Driver at node {driver_node}")
        print(f"[Engine3] Restaurant at node {restaurant_node}")
        print(f"[Engine3] User at node {user_node}")
        
        # Initialize Modified Dijkstra with vehicle type
        mod_dijkstra = ModifiedDijkstra(self.graph, vehicle_type=vehicle_type)
        
        # Segment 1: Driver -> Restaurant (PICKUP)
        print(f"\n[Engine3] ========== SEGMENT 1: PICKUP ==========")
        pickup_results = self._compare_algorithms(
            driver_node, restaurant_node, mod_dijkstra, "Driver→Restaurant"
        )
        
        # Segment 2: Restaurant -> User (DELIVERY)
        print(f"\n[Engine3] ========== SEGMENT 2: DELIVERY ==========")
        delivery_results = self._compare_algorithms(
            restaurant_node, user_node, mod_dijkstra, "Restaurant→User"
        )
        
        # Select best routes
        best_pickup = self._select_best_route(pickup_results)
        best_delivery = self._select_best_route(delivery_results)
        
        # Find alternative routes
        alt_pickup_paths = self.fallback.find_k_shortest_paths(driver_node, restaurant_node, k=2)
        alt_delivery_paths = self.fallback.find_k_shortest_paths(restaurant_node, user_node, k=2)
        
        # Compile complete route
        complete_route = {
            'pickup': {
                'start_node': driver_node,
                'end_node': restaurant_node,
                'algorithms': pickup_results,
                'selected': best_pickup,
                'alternatives': alt_pickup_paths
            },
            'delivery': {
                'start_node': restaurant_node,
                'end_node': user_node,
                'algorithms': delivery_results,
                'selected': best_delivery,
                'alternatives': alt_delivery_paths
            },
            'total_distance': best_pickup['distance'] + best_delivery['distance'],
            'total_nodes': len(best_pickup['path']) + len(best_delivery['path']) - 1,
            'vehicle_type': vehicle_type
        }
        
        # Generate explanation
        complete_route['explanation'] = self._generate_route_explanation(complete_route)
        
        print(f"\n[Engine3] ========== OPTIMIZATION COMPLETE ==========")
        print(f"[Engine3] Total distance: {complete_route['total_distance']:.3f}km")
        print(f"[Engine3] Total nodes: {complete_route['total_nodes']}")
        print(f"\n{complete_route['explanation']}")
        
        return complete_route
    
    def _compare_algorithms(self, start: int, end: int, 
                           mod_dijkstra: ModifiedDijkstra,
                           segment_name: str) -> Dict:
        """
        Run and compare all algorithms for a route segment.
        
        Returns:
            Dictionary with results from each algorithm
        """
        print(f"[Engine3] Comparing algorithms for {segment_name}")
        
        results = {}
        
        # 1. Standard Dijkstra
        print(f"\n  [1/3] Running Standard Dijkstra...")
        path_d, dist_d, stats_d = self.dijkstra.find_shortest_path(start, end)
        results['dijkstra'] = {
            'name': 'Standard Dijkstra',
            'path': path_d,
            'distance': dist_d,
            'stats': stats_d,
            'description': 'Shortest path by distance only'
        }
        
        # 2. Modified Dijkstra
        print(f"\n  [2/3] Running Modified Dijkstra (Traffic-Aware)...")
        path_m, cost_m, stats_m = mod_dijkstra.find_optimal_path(start, end)
        results['modified_dijkstra'] = {
            'name': 'Modified Dijkstra',
            'path': path_m,
            'distance': stats_m['cost_breakdown']['base_distance'] if 'cost_breakdown' in stats_m else cost_m,
            'cost': cost_m,
            'stats': stats_m,
            'description': 'Traffic + road quality + vehicle aware'
        }
        
        # 3. A* Search
        print(f"\n  [3/3] Running A* Search...")
        path_a, dist_a, stats_a = self.astar.find_shortest_path(start, end)
        results['astar'] = {
            'name': 'A* Search',
            'path': path_a,
            'distance': dist_a,
            'stats': stats_a,
            'description': 'Heuristic-guided pathfinding'
        }
        
        # Performance comparison
        print(f"\n  Algorithm Performance:")
        print(f"    Dijkstra:  {stats_d['nodes_explored']} nodes explored")
        print(f"    A*:        {stats_a['nodes_explored']} nodes explored " +
              f"({(1-stats_a['nodes_explored']/stats_d['nodes_explored'])*100:.1f}% more efficient)")
        print(f"    Modified:  {stats_m['nodes_explored']} nodes explored")
        
        return results
    
    def _select_best_route(self, results: Dict) -> Dict:
        """
        Select best route from algorithm results.
        
        Selection criteria (in order):
        1. Modified Dijkstra if cost significantly different from standard
        2. A* if equally good but more efficient
        3. Standard Dijkstra as fallback
        """
        dijkstra_result = results['dijkstra']
        modified_result = results['modified_dijkstra']
        astar_result = results['astar']
        
        # Check if Modified Dijkstra found a significantly better route
        if 'cost' in modified_result:
            base_dist = modified_result['stats']['cost_breakdown']['base_distance']
            penalty_ratio = modified_result['stats']['cost_breakdown']['penalty_ratio']
            
            # If penalties are significant (>10%), use modified route
            if penalty_ratio > 1.1:
                print(f"  → Selected Modified Dijkstra (penalty ratio: {penalty_ratio:.2f}x)")
                return modified_result
        
        # Otherwise, prefer A* if it found same distance more efficiently
        if abs(dijkstra_result['distance'] - astar_result['distance']) < 0.01:
            if astar_result['stats']['nodes_explored'] < dijkstra_result['stats']['nodes_explored']:
                print(f"  → Selected A* (same distance, more efficient)")
                return astar_result
        
        # Default to standard Dijkstra
        print(f"  → Selected Standard Dijkstra (baseline)")
        return dijkstra_result
    
    def _generate_route_explanation(self, route: Dict) -> str:
        """Generate human-readable route explanation."""
        pickup = route['pickup']['selected']
        delivery = route['delivery']['selected']
        
        explanation = []
        explanation.append("=== OPTIMAL ROUTE ANALYSIS ===\n")
        
        explanation.append("PICKUP ROUTE (Driver → Restaurant):")
        explanation.append(f"  Algorithm: {pickup['name']}")
        explanation.append(f"  Distance: {pickup['distance']:.3f}km")
        explanation.append(f"  Nodes: {len(pickup['path'])}")
        explanation.append(f"  Path: {' → '.join(map(str, pickup['path']))}\n")
        
        explanation.append("DELIVERY ROUTE (Restaurant → User):")
        explanation.append(f"  Algorithm: {delivery['name']}")
        explanation.append(f"  Distance: {delivery['distance']:.3f}km")
        explanation.append(f"  Nodes: {len(delivery['path'])}")
        explanation.append(f"  Path: {' → '.join(map(str, delivery['path']))}\n")
        
        explanation.append(f"TOTAL JOURNEY: {route['total_distance']:.3f}km")
        
        # Add alternative routes info
        if len(route['pickup']['alternatives']) > 1:
            alt = route['pickup']['alternatives'][1]
            explanation.append(f"\nAlternative pickup route available: {alt[1]:.3f}km (+{alt[1]-pickup['distance']:.3f}km)")
        
        if len(route['delivery']['alternatives']) > 1:
            alt = route['delivery']['alternatives'][1]
            explanation.append(f"Alternative delivery route available: {alt[1]:.3f}km (+{alt[1]-delivery['distance']:.3f}km)")
        
        return "\n".join(explanation)
    
    def get_visualization_data(self, route: Dict) -> Dict:
        """
        Prepare route data for visualization.
        
        Returns:
            Dictionary with node coordinates and paths for drawing
        """
        viz_data = {
            'pickup_path': [],
            'delivery_path': [],
            'explored_edges': []
        }
        
        # Get pickup path coordinates
        for node_id in route['pickup']['selected']['path']:
            lat, lon = self.graph.get_node_coords(node_id)
            viz_data['pickup_path'].append({'lat': lat, 'lon': lon, 'node_id': node_id})
        
        # Get delivery path coordinates
        for node_id in route['delivery']['selected']['path']:
            lat, lon = self.graph.get_node_coords(node_id)
            viz_data['delivery_path'].append({'lat': lat, 'lon': lon, 'node_id': node_id})
        
        # Get explored edges for visualization
        explored = route['pickup']['selected']['stats']['explored_edges']
        explored += route['delivery']['selected']['stats']['explored_edges']
        
        for from_node, to_node in explored:
            from_lat, from_lon = self.graph.get_node_coords(from_node)
            to_lat, to_lon = self.graph.get_node_coords(to_node)
            viz_data['explored_edges'].append({
                'from': {'lat': from_lat, 'lon': from_lon},
                'to': {'lat': to_lat, 'lon': to_lon}
            })
        
        return viz_data


if __name__ == "__main__":
    # Test Engine 3
    graph = RoadGraph('../data/roads.json')
    engine = RouteOptimizationEngine(graph)
    
    # Test route optimization
    driver_lat, driver_lon = -6.1624, 39.1923
    restaurant_lat, restaurant_lon = -6.1628, 39.1922
    user_lat, user_lon = -6.1642, 39.1916
    
    route = engine.optimize_route(
        driver_lat, driver_lon,
        restaurant_lat, restaurant_lon,
        user_lat, user_lon,
        vehicle_type='boda'
    )
    
    print("\n=== ROUTE COMPLETE ===")
    print(f"Total distance: {route['total_distance']:.3f}km")
    print(f"Total nodes: {route['total_nodes']}")
