"""
ENGINE 1: Restaurant Ranking Engine
====================================
Intelligent restaurant recommendation using multiple DSA techniques:

1. Greedy Pruning: Early elimination of infeasible restaurants
2. Priority Queue: Top-K selection using min-heap
3. Dynamic Scoring: Multi-factor weighted ranking
4. HashMap Caching: Distance calculations

Ranking factors:
- Rating (quality)
- Popularity (demand)
- Distance via road graph (not straight-line!)
- Cuisine match
- Preparation time

This is NOT simple sorting - it's algorithmic optimization.
"""

import heapq
import json
from typing import List, Dict, Tuple
from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra


class Restaurant:
    """Restaurant data structure."""
    def __init__(self, data: Dict):
        self.id = data['id']
        self.name = data['name']
        self.lat = data['lat']
        self.lon = data['lon']
        self.cuisine = data['cuisine']
        self.rating = data['rating']
        self.popularity = data['popularity']
        self.avg_prep_time = data['avg_prep_time']
        self.price_range = data['price_range']
        self.road_node = None  # Will be set by snapping
        self.score = 0.0
        self.distance_km = 0.0
        self.explanation = ""


class RestaurantRankingEngine:
    """
    Intelligent restaurant ranking using DSA.
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'rating': 0.25,
        'popularity': 0.20,
        'distance': 0.30,  # Inverse - closer is better
        'prep_time': 0.15,  # Inverse - faster is better
        'cuisine_match': 0.10
    }
    
    # Greedy pruning thresholds
    MAX_DISTANCE_KM = 3.0  # Maximum acceptable distance
    MIN_RATING = 3.5       # Minimum acceptable rating
    
    def __init__(self, graph: RoadGraph, restaurants_file: str):
        """
        Initialize ranking engine.
        
        Args:
            graph: RoadGraph instance
            restaurants_file: Path to restaurants.json
        """
        self.graph = graph
        self.dijkstra = Dijkstra(graph)
        self.distance_cache = {}  # HashMap for caching
        
        # Load restaurants
        with open(restaurants_file, 'r') as f:
            data = json.load(f)
        
        self.restaurants = [Restaurant(r) for r in data['restaurants']]
        
        # Snap all restaurants to road nodes
        print(f"[Engine1] Snapping {len(self.restaurants)} restaurants to road network...")
        for restaurant in self.restaurants:
            restaurant.road_node = self.graph.snap_to_nearest_node(
                restaurant.lat, restaurant.lon
            )
        
        print(f"[Engine1] Initialized with {len(self.restaurants)} restaurants")
    
    def rank_restaurants(self, user_lat: float, user_lon: float, 
                        preferred_cuisine: List[str] = None,
                        top_k: int = 5) -> List[Restaurant]:
        """
        Rank restaurants intelligently using DSA.
        
        Algorithm:
        1. GREEDY PRUNING: Remove impossible restaurants
        2. DISTANCE CALCULATION: Use Dijkstra on road graph (cached)
        3. DYNAMIC SCORING: Weighted multi-factor score
        4. PRIORITY QUEUE: Top-K selection using heap
        
        Args:
            user_lat: User latitude
            user_lon: User longitude
            preferred_cuisine: List of preferred cuisines (optional)
            top_k: Number of restaurants to return
            
        Returns:
            List of top-K ranked Restaurant objects
        """
        print(f"\n[Engine1] === Restaurant Ranking Started ===")
        
        # Step 1: Snap user to road node
        user_node = self.graph.snap_to_nearest_node(user_lat, user_lon)
        print(f"[Engine1] User snapped to node {user_node}")
        
        # Step 2: GREEDY PRUNING - Remove low-quality restaurants
        candidates = []
        pruned_count = 0
        
        for restaurant in self.restaurants:
            # Prune by rating
            if restaurant.rating < self.MIN_RATING:
                pruned_count += 1
                continue
            
            candidates.append(restaurant)
        
        print(f"[Engine1] Pruned {pruned_count} low-rated restaurants")
        print(f"[Engine1] {len(candidates)} candidates remaining")
        
        # Step 3: Calculate distances and scores
        print(f"[Engine1] Calculating road distances...")
        
        for restaurant in candidates:
            # Get cached distance or calculate
            cache_key = (user_node, restaurant.road_node)
            
            if cache_key in self.distance_cache:
                distance_km = self.distance_cache[cache_key]
            else:
                _, distance_km, _ = self.dijkstra.find_shortest_path(
                    user_node, restaurant.road_node
                )
                self.distance_cache[cache_key] = distance_km
            
            restaurant.distance_km = distance_km
            
            # GREEDY PRUNING: Remove restaurants too far
            if distance_km > self.MAX_DISTANCE_KM:
                pruned_count += 1
                continue
            
            # Calculate weighted score
            restaurant.score = self._calculate_score(restaurant, preferred_cuisine)
            restaurant.explanation = self._generate_explanation(restaurant, preferred_cuisine)
        
        # Remove restaurants that are too far
        candidates = [r for r in candidates if r.distance_km <= self.MAX_DISTANCE_KM]
        
        print(f"[Engine1] After distance pruning: {len(candidates)} candidates")
        
        # Step 4: PRIORITY QUEUE - Top-K selection
        # Use max-heap (negate scores) to keep top K
        if len(candidates) <= top_k:
            result = sorted(candidates, key=lambda r: r.score, reverse=True)
        else:
            # Use heap for efficient Top-K
            result = heapq.nlargest(top_k, candidates, key=lambda r: r.score)
        
        print(f"[Engine1] Top {len(result)} restaurants selected")
        
        # Generate detailed explanations
        for i, restaurant in enumerate(result):
            print(f"\n  {i+1}. {restaurant.name}")
            print(f"     Score: {restaurant.score:.3f} | Distance: {restaurant.distance_km:.2f}km")
            print(f"     {restaurant.explanation}")
        
        return result
    
    def _calculate_score(self, restaurant: Restaurant, preferred_cuisine: List[str]) -> float:
        """
        Calculate weighted score for restaurant.
        
        Score components:
        - Rating: 0-5 scale, normalized
        - Popularity: relative to max
        - Distance: inverse (closer = better)
        - Prep time: inverse (faster = better)
        - Cuisine match: binary bonus
        """
        # Normalize rating (0-5 -> 0-1)
        rating_score = restaurant.rating / 5.0
        
        # Normalize popularity
        max_popularity = 1500  # From data
        popularity_score = min(restaurant.popularity / max_popularity, 1.0)
        
        # Inverse distance score (closer is better)
        # Use 1 / (1 + distance) to handle distance=0
        distance_score = 1.0 / (1.0 + restaurant.distance_km)
        
        # Inverse prep time score
        # Normalize by max prep time (35 min from data)
        prep_score = 1.0 - (restaurant.avg_prep_time / 35.0)
        
        # Cuisine match bonus
        cuisine_score = 0.0
        if preferred_cuisine:
            for cuisine in restaurant.cuisine:
                if cuisine in preferred_cuisine:
                    cuisine_score = 1.0
                    break
        
        # Weighted combination
        total_score = (
            self.WEIGHTS['rating'] * rating_score +
            self.WEIGHTS['popularity'] * popularity_score +
            self.WEIGHTS['distance'] * distance_score +
            self.WEIGHTS['prep_time'] * prep_score +
            self.WEIGHTS['cuisine_match'] * cuisine_score
        )
        
        return total_score
    
    def _generate_explanation(self, restaurant: Restaurant, preferred_cuisine: List[str]) -> str:
        """Generate human-readable ranking explanation."""
        reasons = []
        
        if restaurant.rating >= 4.5:
            reasons.append(f"Excellent rating ({restaurant.rating}★)")
        
        if restaurant.distance_km < 0.5:
            reasons.append(f"Very close ({restaurant.distance_km:.2f}km via roads)")
        elif restaurant.distance_km < 1.0:
            reasons.append(f"Nearby ({restaurant.distance_km:.2f}km via roads)")
        
        if restaurant.avg_prep_time <= 15:
            reasons.append(f"Quick prep ({restaurant.avg_prep_time}min)")
        
        if restaurant.popularity > 800:
            reasons.append("Popular choice")
        
        if preferred_cuisine:
            matches = [c for c in restaurant.cuisine if c in preferred_cuisine]
            if matches:
                reasons.append(f"Matches preference: {', '.join(matches)}")
        
        return " | ".join(reasons) if reasons else "Solid option"


if __name__ == "__main__":
    # Test Engine 1
    graph = RoadGraph('../data/roads.json')
    engine = RestaurantRankingEngine(graph, '../data/restaurants.json')
    
    # Test ranking
    user_lat, user_lon = -6.1626, 39.1924
    preferred_cuisine = ['seafood', 'swahili']
    
    top_restaurants = engine.rank_restaurants(
        user_lat, user_lon,
        preferred_cuisine=preferred_cuisine,
        top_k=5
    )
    
    print("\n=== FINAL RANKINGS ===")
    for i, r in enumerate(top_restaurants):
        print(f"{i+1}. {r.name} - Score: {r.score:.3f}")
