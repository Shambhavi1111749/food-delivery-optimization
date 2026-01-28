# 🚀 Food Delivery System - Data Structures & Algorithms Project

A **professional-grade food delivery optimization system** demonstrating advanced graph algorithms, intelligent ranking systems, and multi-factor optimization techniques.

## ⚠️ CRITICAL: Graph-Based Routing

**This is NOT a toy demonstration. This is a professional DSA implementation.**

### Absolute Rules:
1. **ALL routing happens ONLY on existing roads (graph edges)**
2. **NO straight-line routing between arbitrary coordinates**
3. **Coordinates used ONLY for visualization and snapping to nodes**
4. **If an edge doesn't exist, travel is IMPOSSIBLE**
5. **All algorithms operate on the road graph, not raw points**

---

## 🎯 System Overview

The system consists of three intelligent engines:

### Engine 1: Restaurant Ranking
**Algorithms Used:**
- Greedy Pruning (early elimination)
- Priority Queue (Top-K selection)
- Dynamic Weighted Scoring
- HashMap Caching

**Ranking Factors:**
- Rating (25%)
- Popularity (20%)
- Distance via road graph (30%)
- Preparation time (15%)
- Cuisine match (10%)

### Engine 2: Driver Assignment
**Algorithms Used:**
- Greedy Feasibility Pruning
- Soft Constraint Penalties
- Priority Queue Selection
- Feedback-Aware Scoring

**Selection Factors:**
- Distance from restaurant (40%)
- Cost per km (25%)
- Reliability score (20%)
- Customer rating (15%)

### Engine 3: Route Optimization
**Algorithms Compared:**
1. **Standard Dijkstra** - Baseline shortest path
2. **Modified Dijkstra** - Traffic + road quality + vehicle aware
3. **A* Search** - Heuristic-guided pathfinding
4. **Fallback Paths** - Alternative routes (K-shortest paths)

**Route Factors:**
- Road distance
- Traffic congestion
- Road quality
- Vehicle type suitability

---

## 📊 Data Structures Used

### Core Structures:
- **Adjacency List** - Graph representation
- **Priority Queue (Min-Heap)** - Path finding & Top-K selection
- **HashMap** - Distance caching & lookups
- **Parent Pointers** - Path reconstruction
- **Visited Set** - Cycle prevention

### Graph Representation:
```python
# Nodes: Road intersections
nodes = {
    0: {'id': 0, 'lat': -6.1620, 'lon': 39.1920, 'name': 'Creek Road Junction'},
    ...
}

# Edges: Actual roads with metadata
adj_list = {
    0: [(1, 0.08, {'road_name': 'Creek Road', 'traffic': 1.0, 'quality': 0.9})],
    ...
}
```

---

## 🏗️ Project Structure

```
delivery-system/
├── app.py                      # Flask application
├── graph/
│   ├── road_graph.py          # Core graph data structure
│   ├── dijkstra.py            # Standard Dijkstra's algorithm
│   ├── modified_dijkstra.py   # Traffic-aware Dijkstra
│   ├── astar.py               # A* search algorithm
│   └── fallback_path.py       # K-shortest paths
├── engines/
│   ├── engine1_restaurant.py  # Restaurant ranking
│   ├── engine2_driver.py      # Driver assignment
│   └── engine3_route.py       # Route optimization
├── data/
│   ├── roads.json             # Road network graph
│   ├── restaurants.json       # Restaurant data
│   ├── drivers.json           # Driver data
│   └── users.json             # User data
├── templates/
│   ├── index.html            # Home page
│   ├── engine1.html          # Restaurant ranking UI
│   ├── engine2.html          # Driver assignment UI
│   └── engine3.html          # Route optimization UI
└── static/
    ├── css/style.css         # Professional styling
    └── js/                   # JavaScript files
```

---

## 🚀 Installation & Setup

### Prerequisites:
- Python 3.8+
- pip

### Install Dependencies:
```bash
cd delivery-system
pip install flask --break-system-packages
```

### Run the Application:
```bash
python app.py
```

The system will start at `http://localhost:5000`

---

## 🎮 Usage Guide

### 1. Access the Home Page
Navigate to `http://localhost:5000` to see system overview and statistics.

### 2. Engine 1: Rank Restaurants
**URL:** `http://localhost:5000/engine1`

**Steps:**
1. Select a user from the dropdown
2. Choose preferred cuisine (optional)
3. Click "Rank Restaurants"
4. View ranked results with explanations
5. See restaurants marked on map

**Algorithm Process:**
- User snapped to nearest road node
- Greedy pruning removes low-rated/distant restaurants
- Distances calculated via Dijkstra on road graph
- Weighted scoring applied
- Top-K selected using priority queue

### 3. Engine 2: Assign Driver
**URL:** `http://localhost:5000/engine2`

**Steps:**
1. Enter restaurant coordinates
2. Select order size (affects vehicle choice)
3. Click "Assign Driver"
4. View selected driver, backups, and rejected candidates
5. See algorithm timeline

**Algorithm Process:**
- All drivers snapped to road nodes
- Feasibility pruning (distance, rating)
- Soft constraints applied (availability, vehicle match)
- Cost scores calculated
- Best driver + backups selected

### 4. Engine 3: Optimize Route
**URL:** `http://localhost:5000/engine3`

**Steps:**
1. Enter driver, restaurant, and user coordinates
2. Select vehicle type
3. Click "Optimize Route"
4. View complete route visualization
5. Compare algorithm performance

**Algorithm Process:**
- All locations snapped to road nodes
- Multiple algorithms run on road graph:
  - Standard Dijkstra
  - Modified Dijkstra (traffic-aware)
  - A* Search
- Best routes selected for pickup and delivery
- Complete path visualized

---

## 🧪 Testing the System

### Test 1: Verify Graph-Based Routing
```python
# Test that removing an edge changes routing
from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra

graph = RoadGraph('data/roads.json')
dijkstra = Dijkstra(graph)

# Find path
path1, dist1, _ = dijkstra.find_shortest_path(0, 13)
print(f"Path before: {path1}, Distance: {dist1}")

# Remove edge
graph.remove_edge(0, 1)

# Find path again
path2, dist2, _ = dijkstra.find_shortest_path(0, 13)
print(f"Path after: {path2}, Distance: {dist2}")

# Verify routing changed
assert path1 != path2, "Route must change when edge removed!"
```

### Test 2: Verify No Straight-Line Routing
All algorithms output paths as **node sequences** (e.g., `[0, 1, 2, 5, 7]`), not coordinates.
Distances are calculated by **summing edge weights**, not Euclidean distance.

### Test 3: API Endpoint Test
```bash
# Test Engine 1 API
curl -X POST http://localhost:5000/api/engine1/rank \
  -H "Content-Type: application/json" \
  -d '{"user_lat": -6.1626, "user_lon": 39.1924, "preferred_cuisine": ["seafood"], "top_k": 5}'

# Test Engine 2 API
curl -X POST http://localhost:5000/api/engine2/assign \
  -H "Content-Type: application/json" \
  -d '{"restaurant_lat": -6.1628, "restaurant_lon": 39.1922, "order_size": "medium"}'

# Test Engine 3 API
curl -X POST http://localhost:5000/api/engine3/optimize \
  -H "Content-Type: application/json" \
  -d '{"driver_lat": -6.1624, "driver_lon": 39.1923, "restaurant_lat": -6.1628, "restaurant_lon": 39.1922, "user_lat": -6.1642, "user_lon": 39.1916, "vehicle_type": "boda"}'
```

---

## 📈 Algorithm Complexity

### Dijkstra's Algorithm:
- **Time:** O((V + E) log V) with priority queue
- **Space:** O(V) for distances and parents
- Used in: All three engines

### A* Search:
- **Time:** O((V + E) log V) average case (better with good heuristic)
- **Space:** O(V)
- Used in: Engine 3

### Modified Dijkstra:
- **Time:** O((V + E) log V) - same as standard
- **Space:** O(V)
- **Enhancement:** Weighted edge costs (traffic, quality, vehicle)

### Greedy Pruning:
- **Time:** O(N) where N = number of candidates
- **Space:** O(1)
- Used in: Engine 1 and Engine 2

### Priority Queue Selection:
- **Time:** O(N log K) for Top-K selection
- **Space:** O(K)
- Used in: Engine 1 and Engine 2

---

## 🎨 Design Decisions

### Why Graph-Based Routing?
Real-world delivery systems must follow roads. Straight-line distance is **meaningless** for:
- Urban navigation
- Traffic considerations
- Road quality factors
- Legal road restrictions

### Why Multiple Algorithms?
Different scenarios require different optimizations:
- **Dijkstra:** Guaranteed shortest path
- **Modified Dijkstra:** Real-world factors (traffic, quality)
- **A*:** Faster for long distances
- **Fallback:** Alternative routes for road closures

### Why Three Engines?
Each engine demonstrates different DSA concepts:
- **Engine 1:** Ranking, scoring, pruning
- **Engine 2:** Constraint optimization, penalty functions
- **Engine 3:** Graph algorithms, path comparison

---

## 🔍 Key Features

✅ **Professional road network graph** (21 nodes, 34 edges)  
✅ **Real Zanzibar Stone Town locations**  
✅ **Graph validation and integrity checks**  
✅ **Distance caching for performance**  
✅ **Multi-algorithm comparison**  
✅ **Interactive map visualization**  
✅ **Complete algorithm explanations**  
✅ **Professional UI with animations**  
✅ **RESTful API endpoints**  
✅ **Comprehensive error handling**

---

## 📚 Educational Value

This project demonstrates:
1. **Graph Theory** - Adjacency lists, weighted graphs
2. **Shortest Path Algorithms** - Dijkstra, A*
3. **Priority Queues** - Min-heaps for efficiency
4. **Greedy Algorithms** - Pruning and selection
5. **Dynamic Programming** - Weighted scoring
6. **Hash Maps** - Caching and lookups
7. **Algorithm Analysis** - Time/space complexity
8. **Real-World Applications** - Delivery optimization

---

## 🚨 Common Pitfalls Avoided

❌ **Don't:** Use Euclidean distance for routing  
✅ **Do:** Use graph edges only

❌ **Don't:** Route between arbitrary coordinates  
✅ **Do:** Snap to nearest road node first

❌ **Don't:** Assume direct paths exist  
✅ **Do:** Check if path exists in graph

❌ **Don't:** Ignore traffic and road quality  
✅ **Do:** Use Modified Dijkstra for real-world factors

---

## 🎓 Academic Context

**Course:** Data Structures & Algorithms  
**Level:** TOP-1 University (Advanced)  
**Focus:** Graph algorithms, optimization, system design  
**Difficulty:** Professional/Industry-Grade

This is **not a toy project**. This demonstrates:
- Production-level code organization
- Professional algorithm implementation
- Real-world problem solving
- System architecture design

---

## 📝 License

This project is for educational purposes.

---

## 👨‍💻 Author

Created as a comprehensive DSA project demonstrating professional-grade software engineering and algorithmic problem-solving.

---

## 🙏 Acknowledgments

- OpenStreetMap for map tiles
- Leaflet.js for map visualization
- Flask for web framework
- Python standard library for heapq

---

**Remember:** This system represents **real algorithmic thinking**, not shortcuts. Every route follows actual roads, every distance calculation uses the graph, and every algorithm operates on proper data structures.
