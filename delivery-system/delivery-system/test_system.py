#!/usr/bin/env python3
"""
Test Suite for Food Delivery System
====================================
Verifies all critical components and rules.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra
from graph.modified_dijkstra import ModifiedDijkstra
from graph.astar import AStar
from engines.engine1_restaurant import RestaurantRankingEngine
from engines.engine2_driver import DriverAssignmentEngine
from engines.engine3_route import RouteOptimizationEngine


def test_graph_loading():
    """Test 1: Graph loads correctly."""
    print("\n" + "="*60)
    print("TEST 1: Graph Loading")
    print("="*60)
    
    graph = RoadGraph('data/roads.json')
    assert len(graph.nodes) == 21, "Should have 21 nodes"
    assert graph.validate_graph(), "Graph should be valid"
    
    print("✓ Graph loaded: 21 nodes, bidirectional edges")
    print("✓ Graph validation passed")
    return graph


def test_graph_based_routing(graph):
    """Test 2: Verify routing depends on graph edges."""
    print("\n" + "="*60)
    print("TEST 2: Graph-Based Routing (CRITICAL)")
    print("="*60)
    
    dijkstra = Dijkstra(graph)
    
    # Find path before edge removal
    path1, dist1, _ = dijkstra.find_shortest_path(0, 1)
    print(f"Path before edge removal: {path1} ({dist1:.3f}km)")
    
    # Remove edge
    graph.remove_edge(0, 1)
    
    # Find path after edge removal
    path2, dist2, _ = dijkstra.find_shortest_path(0, 1)
    print(f"Path after edge removal:  {path2} ({dist2:.3f}km)")
    
    assert path1 != path2, "Paths must differ when edge removed!"
    assert dist2 > dist1, "Distance must increase with detour!"
    
    print("✓ Route changed when edge removed")
    print("✓ Routing depends on graph edges VERIFIED")


def test_node_snapping(graph):
    """Test 3: Verify entities snap to road nodes."""
    print("\n" + "="*60)
    print("TEST 3: Node Snapping")
    print("="*60)
    
    # Test snapping arbitrary coordinates
    test_lat, test_lon = -6.1626, 39.1924
    node_id = graph.snap_to_nearest_node(test_lat, test_lon)
    
    assert isinstance(node_id, int), "Should return node ID"
    assert node_id in graph.nodes, "Should return valid node"
    
    node = graph.get_node(node_id)
    print(f"Coordinates ({test_lat}, {test_lon})")
    print(f"Snapped to: Node {node_id} - {node['name']}")
    print("✓ Snapping works correctly")


def test_dijkstra(graph):
    """Test 4: Dijkstra's algorithm."""
    print("\n" + "="*60)
    print("TEST 4: Dijkstra's Algorithm")
    print("="*60)
    
    dijkstra = Dijkstra(graph)
    path, distance, stats = dijkstra.find_shortest_path(0, 13)
    
    assert len(path) > 0, "Should find a path"
    assert path[0] == 0 and path[-1] == 13, "Path should start and end correctly"
    assert distance > 0, "Distance should be positive"
    
    print(f"Path: {' -> '.join(map(str, path))}")
    print(f"Distance: {distance:.3f}km")
    print(f"Nodes explored: {stats['nodes_explored']}")
    print("✓ Dijkstra working correctly")


def test_astar(graph):
    """Test 5: A* algorithm."""
    print("\n" + "="*60)
    print("TEST 5: A* Search Algorithm")
    print("="*60)
    
    astar = AStar(graph)
    path, distance, stats = astar.find_shortest_path(0, 13)
    
    assert len(path) > 0, "Should find a path"
    assert distance > 0, "Distance should be positive"
    
    print(f"Path: {' -> '.join(map(str, path))}")
    print(f"Distance: {distance:.3f}km")
    print(f"Nodes explored: {stats['nodes_explored']}")
    print("✓ A* working correctly")


def test_modified_dijkstra(graph):
    """Test 6: Modified Dijkstra."""
    print("\n" + "="*60)
    print("TEST 6: Modified Dijkstra (Traffic-Aware)")
    print("="*60)
    
    mod_dijkstra = ModifiedDijkstra(graph, vehicle_type='boda')
    path, cost, stats = mod_dijkstra.find_optimal_path(0, 13)
    
    assert len(path) > 0, "Should find a path"
    assert cost > 0, "Cost should be positive"
    
    print(f"Path: {' -> '.join(map(str, path))}")
    print(f"Weighted cost: {cost:.3f}")
    print(f"Base distance: {stats['cost_breakdown']['base_distance']:.3f}km")
    print(f"Penalty ratio: {stats['cost_breakdown']['penalty_ratio']:.2f}x")
    print("✓ Modified Dijkstra working correctly")


def test_engine1(graph):
    """Test 7: Restaurant ranking engine."""
    print("\n" + "="*60)
    print("TEST 7: Engine 1 - Restaurant Ranking")
    print("="*60)
    
    engine = RestaurantRankingEngine(graph, 'data/restaurants.json')
    
    restaurants = engine.rank_restaurants(
        -6.1626, 39.1924,
        preferred_cuisine=['seafood'],
        top_k=3
    )
    
    assert len(restaurants) > 0, "Should return restaurants"
    assert all(r.score > 0 for r in restaurants), "All should have positive scores"
    assert restaurants[0].score >= restaurants[-1].score, "Should be sorted by score"
    
    print(f"Top 3 restaurants:")
    for i, r in enumerate(restaurants):
        print(f"  {i+1}. {r.name} - Score: {r.score:.3f}, Distance: {r.distance_km:.2f}km")
    print("✓ Engine 1 working correctly")


def test_engine2(graph):
    """Test 8: Driver assignment engine."""
    print("\n" + "="*60)
    print("TEST 8: Engine 2 - Driver Assignment")
    print("="*60)
    
    engine = DriverAssignmentEngine(graph, 'data/drivers.json')
    
    best, backups, rejected = engine.assign_driver(
        -6.1628, 39.1922,
        order_size='medium',
        num_backups=2
    )
    
    assert best is not None, "Should assign a driver"
    assert best.cost_score > 0, "Should have positive cost"
    assert len(backups) > 0, "Should have backup drivers"
    
    print(f"Selected: {best.name} ({best.vehicle_type})")
    print(f"Cost score: {best.cost_score:.3f}")
    print(f"Backups: {len(backups)}")
    print(f"Rejected: {len(rejected)}")
    print("✓ Engine 2 working correctly")


def test_engine3(graph):
    """Test 9: Route optimization engine."""
    print("\n" + "="*60)
    print("TEST 9: Engine 3 - Route Optimization")
    print("="*60)
    
    engine = RouteOptimizationEngine(graph)
    
    route = engine.optimize_route(
        -6.1624, 39.1923,  # Driver
        -6.1628, 39.1922,  # Restaurant
        -6.1642, 39.1916,  # User
        vehicle_type='boda'
    )
    
    assert route['total_distance'] > 0, "Should have positive distance"
    assert len(route['pickup']['selected']['path']) > 0, "Should have pickup path"
    assert len(route['delivery']['selected']['path']) > 0, "Should have delivery path"
    
    print(f"Total distance: {route['total_distance']:.3f}km")
    print(f"Pickup: {route['pickup']['selected']['name']}")
    print(f"Delivery: {route['delivery']['selected']['name']}")
    print("✓ Engine 3 working correctly")


def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█  FOOD DELIVERY SYSTEM - TEST SUITE" + " "*21 + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    try:
        # Core tests
        graph = test_graph_loading()
        test_graph_based_routing(RoadGraph('data/roads.json'))  # Use fresh graph
        test_node_snapping(graph)
        
        # Algorithm tests
        test_dijkstra(graph)
        test_astar(graph)
        test_modified_dijkstra(graph)
        
        # Engine tests
        test_engine1(graph)
        test_engine2(graph)
        test_engine3(graph)
        
        # Summary
        print("\n" + "█"*60)
        print("█" + " "*58 + "█")
        print("█  ✓✓✓ ALL TESTS PASSED ✓✓✓" + " "*30 + "█")
        print("█" + " "*58 + "█")
        print("█  Graph-based routing VERIFIED" + " "*27 + "█")
        print("█  All algorithms working correctly" + " "*24 + "█")
        print("█  All engines functioning properly" + " "*24 + "█")
        print("█" + " "*58 + "█")
        print("█"*60)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
