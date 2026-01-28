"""
Food Delivery System - Main Flask Application
==============================================
Professional DSA-based food delivery system with three intelligent engines.

Routes:
- / : Home page
- /engine1 : Restaurant ranking
- /engine2 : Driver assignment
- /engine3 : Route optimization
- /api/* : JSON API endpoints
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.road_graph import RoadGraph
from engines.engine1_restaurant import RestaurantRankingEngine
from engines.engine2_driver import DriverAssignmentEngine
from engines.engine3_route import RouteOptimizationEngine

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize road graph
print("Initializing road graph...")
graph = RoadGraph('data/roads.json')
graph.validate_graph()

# Initialize engines
print("Initializing Engine 1 (Restaurant Ranking)...")
engine1 = RestaurantRankingEngine(graph, 'data/restaurants.json')

print("Initializing Engine 2 (Driver Assignment)...")
engine2 = DriverAssignmentEngine(graph, 'data/drivers.json')

print("Initializing Engine 3 (Route Optimization)...")
engine3 = RouteOptimizationEngine(graph)

print("\n✓ All engines initialized successfully!")
print("=" * 60)


# ============================================================================
# WEB PAGES
# ============================================================================

@app.route('/')
def index():
    """Home page with system overview."""
    return render_template('index.html')


@app.route('/engine1')
def engine1_page():
    """Engine 1: Restaurant Ranking Interface."""
    # Load user data for selection
    with open('data/users.json', 'r') as f:
        users = json.load(f)['users']
    return render_template('engine1.html', users=users)


@app.route('/engine2')
def engine2_page():
    """Engine 2: Driver Assignment Interface."""
    return render_template('engine2.html')


@app.route('/engine3')
def engine3_page():
    """Engine 3: Route Optimization Interface."""
    return render_template('engine3.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/graph/info')
def api_graph_info():
    """Get road graph information."""
    return jsonify({
        'total_nodes': len(graph.nodes),
        'total_edges': sum(len(neighbors) for neighbors in graph.adj_list.values()) // 2,
        'nodes': [
            {
                'id': node_id,
                'name': node['name'],
                'lat': node['lat'],
                'lon': node['lon']
            }
            for node_id, node in graph.nodes.items()
        ],
        'edges': [
            {
                'from': from_node,
                'to': to_node,
                'distance': dist,
                'road_name': meta['road_name']
            }
            for from_node, neighbors in graph.adj_list.items()
            for to_node, dist, meta in neighbors
            if from_node < to_node  # Avoid duplicates
        ]
    })


@app.route('/api/engine1/rank', methods=['POST'])
def api_engine1_rank():
    """
    Rank restaurants for a user.
    
    POST data:
    - user_lat, user_lon: User coordinates
    - preferred_cuisine: List of cuisines (optional)
    - top_k: Number of results (default: 5)
    """
    data = request.json
    
    user_lat = float(data['user_lat'])
    user_lon = float(data['user_lon'])
    preferred_cuisine = data.get('preferred_cuisine', [])
    top_k = int(data.get('top_k', 5))
    
    # Run Engine 1
    restaurants = engine1.rank_restaurants(
        user_lat, user_lon,
        preferred_cuisine=preferred_cuisine,
        top_k=top_k
    )
    
    # Format response
    result = []
    for i, restaurant in enumerate(restaurants):
        result.append({
            'rank': i + 1,
            'id': restaurant.id,
            'name': restaurant.name,
            'lat': restaurant.lat,
            'lon': restaurant.lon,
            'road_node': restaurant.road_node,
            'cuisine': restaurant.cuisine,
            'rating': restaurant.rating,
            'popularity': restaurant.popularity,
            'avg_prep_time': restaurant.avg_prep_time,
            'price_range': restaurant.price_range,
            'distance_km': round(restaurant.distance_km, 3),
            'score': round(restaurant.score, 3),
            'explanation': restaurant.explanation
        })
    
    return jsonify({
        'success': True,
        'restaurants': result,
        'user_node': graph.snap_to_nearest_node(user_lat, user_lon)
    })


@app.route('/api/engine2/assign', methods=['POST'])
def api_engine2_assign():
    """
    Assign driver to restaurant.
    
    POST data:
    - restaurant_lat, restaurant_lon: Restaurant coordinates
    - order_size: small/medium/large
    - num_backups: Number of backup drivers (default: 2)
    """
    data = request.json
    
    restaurant_lat = float(data['restaurant_lat'])
    restaurant_lon = float(data['restaurant_lon'])
    order_size = data.get('order_size', 'medium')
    num_backups = int(data.get('num_backups', 2))
    
    # Run Engine 2
    best_driver, backup_drivers, rejected_drivers = engine2.assign_driver(
        restaurant_lat, restaurant_lon,
        order_size=order_size,
        num_backups=num_backups
    )
    
    if not best_driver:
        return jsonify({
            'success': False,
            'error': 'No available drivers'
        })
    
    def format_driver(driver):
        return {
            'id': driver.id,
            'name': driver.name,
            'lat': driver.lat,
            'lon': driver.lon,
            'road_node': driver.road_node,
            'vehicle_type': driver.vehicle_type,
            'cost_per_km': driver.cost_per_km,
            'rating': driver.rating,
            'total_trips': driver.total_trips,
            'availability': driver.availability,
            'reliability_score': driver.reliability_score,
            'distance_km': round(driver.distance_km, 3),
            'cost_score': round(driver.cost_score, 3),
            'explanation': driver.explanation,
            'rejected_reason': driver.rejected_reason
        }
    
    return jsonify({
        'success': True,
        'selected_driver': format_driver(best_driver),
        'backup_drivers': [format_driver(d) for d in backup_drivers],
        'rejected_drivers': [format_driver(d) for d in rejected_drivers]
    })


@app.route('/api/engine3/optimize', methods=['POST'])
def api_engine3_optimize():
    """
    Optimize complete delivery route.
    
    POST data:
    - driver_lat, driver_lon: Driver coordinates
    - restaurant_lat, restaurant_lon: Restaurant coordinates
    - user_lat, user_lon: User coordinates
    - vehicle_type: boda/bajaji
    """
    data = request.json
    
    driver_lat = float(data['driver_lat'])
    driver_lon = float(data['driver_lon'])
    restaurant_lat = float(data['restaurant_lat'])
    restaurant_lon = float(data['restaurant_lon'])
    user_lat = float(data['user_lat'])
    user_lon = float(data['user_lon'])
    vehicle_type = data.get('vehicle_type', 'boda')
    
    # Run Engine 3
    route = engine3.optimize_route(
        driver_lat, driver_lon,
        restaurant_lat, restaurant_lon,
        user_lat, user_lon,
        vehicle_type=vehicle_type
    )
    
    # Get visualization data
    viz_data = engine3.get_visualization_data(route)
    
    return jsonify({
        'success': True,
        'route': {
            'pickup': {
                'algorithm': route['pickup']['selected']['name'],
                'distance': round(route['pickup']['selected']['distance'], 3),
                'path': route['pickup']['selected']['path'],
                'stats': route['pickup']['selected']['stats']
            },
            'delivery': {
                'algorithm': route['delivery']['selected']['name'],
                'distance': round(route['delivery']['selected']['distance'], 3),
                'path': route['delivery']['selected']['path'],
                'stats': route['delivery']['selected']['stats']
            },
            'total_distance': round(route['total_distance'], 3),
            'total_nodes': route['total_nodes'],
            'vehicle_type': route['vehicle_type'],
            'explanation': route['explanation']
        },
        'visualization': viz_data,
        'algorithms_comparison': {
            'pickup': {
                algo: {
                    'name': result['name'],
                    'distance': round(result['distance'], 3),
                    'nodes_explored': result['stats']['nodes_explored'],
                    'description': result['description']
                }
                for algo, result in route['pickup']['algorithms'].items()
            },
            'delivery': {
                algo: {
                    'name': result['name'],
                    'distance': round(result['distance'], 3),
                    'nodes_explored': result['stats']['nodes_explored'],
                    'description': result['description']
                }
                for algo, result in route['delivery']['algorithms'].items()
            }
        }
    })


@app.route('/api/test/remove-edge', methods=['POST'])
def api_test_remove_edge():
    """
    TEST ENDPOINT: Remove a road edge and verify routing changes.
    This demonstrates that routing truly depends on graph edges.
    """
    data = request.json
    from_node = int(data['from_node'])
    to_node = int(data['to_node'])
    
    # Find a path before removal
    _, dist_before, _ = engine3.dijkstra.find_shortest_path(from_node, to_node)
    
    # Remove edge
    graph.remove_edge(from_node, to_node)
    
    # Find path after removal
    path_after, dist_after, _ = engine3.dijkstra.find_shortest_path(from_node, to_node)
    
    # Restore edge (for continued testing)
    # Note: Would need to store edge data to properly restore
    
    return jsonify({
        'success': True,
        'edge_removed': f"{from_node} <-> {to_node}",
        'distance_before': round(dist_before, 3),
        'distance_after': round(dist_after, 3) if path_after else 'NO PATH',
        'routing_changed': dist_before != dist_after
    })


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 Food Delivery System Starting...")
    print("=" * 60)
    print("\nAccess the application at: http://localhost:5000")
    print("\nEngines:")
    print("  Engine 1: http://localhost:5000/engine1")
    print("  Engine 2: http://localhost:5000/engine2")
    print("  Engine 3: http://localhost:5000/engine3")
    print("\n" + "=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
