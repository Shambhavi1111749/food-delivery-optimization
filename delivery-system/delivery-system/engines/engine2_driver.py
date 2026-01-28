"""
ENGINE 2: Driver Assignment Engine
===================================
Intelligent driver selection using DSA techniques:

1. Greedy Feasibility Pruning: Remove unavailable/unsuitable drivers
2. Soft Constraint Penalties: Cost function with multiple factors
3. Priority Queue Selection: Best driver + backups
4. Feedback-Aware Scoring: Historical reliability

Selection factors:
- Distance from restaurant (via road graph)
- Cost per km
- Vehicle suitability (boda vs bajaji)
- Availability status
- Reliability score
- Customer rating

This ensures optimal driver-order matching, not just nearest driver.
"""

import heapq
import json
from typing import List, Dict, Tuple, Optional
from graph.road_graph import RoadGraph
from graph.dijkstra import Dijkstra


class Driver:
    """Driver data structure."""
    def __init__(self, data: Dict):
        self.id = data['id']
        self.name = data['name']
        self.lat = data['lat']
        self.lon = data['lon']
        self.vehicle_type = data['vehicle_type']
        self.cost_per_km = data['cost_per_km']
        self.rating = data['rating']
        self.total_trips = data['total_trips']
        self.availability = data['availability']
        self.reliability_score = data['reliability_score']
        self.road_node = None
        self.cost_score = 0.0
        self.distance_km = 0.0
        self.explanation = ""
        self.rejected_reason = ""


class DriverAssignmentEngine:
    """
    Intelligent driver assignment using DSA.
    """
    
    # Cost weights
    WEIGHTS = {
        'distance': 0.40,
        'cost_rate': 0.25,
        'reliability': 0.20,
        'rating': 0.15
    }
    
    # Penalties
    AVAILABILITY_PENALTY = 2.0  # Multiply cost by this if busy
    VEHICLE_MISMATCH_PENALTY = 1.5  # For unsuitable vehicle
    
    # Hard constraints
    MAX_DISTANCE_KM = 5.0  # Maximum driver distance from restaurant
    MIN_RATING = 4.0       # Minimum acceptable rating
    
    def __init__(self, graph: RoadGraph, drivers_file: str):
        """
        Initialize driver assignment engine.
        
        Args:
            graph: RoadGraph instance
            drivers_file: Path to drivers.json
        """
        self.graph = graph
        self.dijkstra = Dijkstra(graph)
        self.distance_cache = {}
        
        # Load drivers
        with open(drivers_file, 'r') as f:
            data = json.load(f)
        
        self.drivers = [Driver(d) for d in data['drivers']]
        
        # Snap all drivers to road nodes
        print(f"[Engine2] Snapping {len(self.drivers)} drivers to road network...")
        for driver in self.drivers:
            driver.road_node = self.graph.snap_to_nearest_node(
                driver.lat, driver.lon
            )
        
        print(f"[Engine2] Initialized with {len(self.drivers)} drivers")
    
    def assign_driver(self, restaurant_lat: float, restaurant_lon: float,
                     order_size: str = 'medium',
                     num_backups: int = 2) -> Tuple[Optional[Driver], List[Driver], List[Driver]]:
        """
        Assign best driver to restaurant using intelligent algorithms.
        
        Algorithm:
        1. GREEDY FEASIBILITY PRUNING: Remove impossible drivers
           - Too far away
           - Low rating
           - Wrong vehicle for order size
        2. SOFT CONSTRAINT PENALTIES: Calculate weighted cost
        3. PRIORITY QUEUE: Select best + backups
        
        Args:
            restaurant_lat: Restaurant latitude
            restaurant_lon: Restaurant longitude
            order_size: 'small', 'medium', 'large' (affects vehicle choice)
            num_backups: Number of backup drivers to return
            
        Returns:
            Tuple of (best_driver, backup_drivers, rejected_drivers)
        """
        print(f"\n[Engine2] === Driver Assignment Started ===")
        
        # Snap restaurant to road node
        restaurant_node = self.graph.snap_to_nearest_node(restaurant_lat, restaurant_lon)
        print(f"[Engine2] Restaurant snapped to node {restaurant_node}")
        
        # Step 1: GREEDY FEASIBILITY PRUNING
        feasible = []
        rejected = []
        
        for driver in self.drivers:
            # Get distance via road graph
            cache_key = (driver.road_node, restaurant_node)
            
            if cache_key in self.distance_cache:
                distance_km = self.distance_cache[cache_key]
            else:
                _, distance_km, _ = self.dijkstra.find_shortest_path(
                    driver.road_node, restaurant_node
                )
                self.distance_cache[cache_key] = distance_km
            
            driver.distance_km = distance_km
            
            # Hard constraint: Distance
            if distance_km > self.MAX_DISTANCE_KM:
                driver.rejected_reason = f"Too far ({distance_km:.2f}km > {self.MAX_DISTANCE_KM}km)"
                rejected.append(driver)
                continue
            
            # Hard constraint: Rating
            if driver.rating < self.MIN_RATING:
                driver.rejected_reason = f"Rating too low ({driver.rating} < {self.MIN_RATING})"
                rejected.append(driver)
                continue
            
            # Passed hard constraints
            feasible.append(driver)
        
        print(f"[Engine2] Feasibility check: {len(feasible)} passed, {len(rejected)} rejected")
        
        if not feasible:
            print("[Engine2] ERROR: No feasible drivers available!")
            return None, [], rejected
        
        # Step 2: SOFT CONSTRAINT PENALTIES - Calculate cost scores
        for driver in feasible:
            driver.cost_score = self._calculate_cost(driver, order_size)
            driver.explanation = self._generate_explanation(driver)
        
        # Step 3: PRIORITY QUEUE - Select best + backups
        # Sort by cost (lower is better)
        feasible.sort(key=lambda d: d.cost_score)
        
        best_driver = feasible[0]
        backup_drivers = feasible[1:num_backups+1]
        
        print(f"\n[Engine2] SELECTED: {best_driver.name}")
        print(f"  Vehicle: {best_driver.vehicle_type}")
        print(f"  Distance: {best_driver.distance_km:.2f}km")
        print(f"  Cost Score: {best_driver.cost_score:.3f}")
        print(f"  {best_driver.explanation}")
        
        print(f"\n[Engine2] BACKUPS:")
        for i, driver in enumerate(backup_drivers):
            print(f"  {i+1}. {driver.name} (cost: {driver.cost_score:.3f})")
        
        print(f"\n[Engine2] REJECTED:")
        for driver in rejected[:3]:  # Show first 3
            print(f"  ✗ {driver.name}: {driver.rejected_reason}")
        
        return best_driver, backup_drivers, rejected
    
    def _calculate_cost(self, driver: Driver, order_size: str) -> float:
        """
        Calculate weighted cost score for driver.
        Lower cost = better driver.
        
        Cost components:
        - Distance: Actual road distance
        - Cost rate: Driver's per-km charge
        - Reliability: Historical performance (inverted - higher is better)
        - Rating: Customer rating (inverted - higher is better)
        - Availability penalty: Busy drivers cost more
        - Vehicle mismatch: Wrong vehicle type for order
        """
        # Base distance cost
        distance_cost = driver.distance_km
        
        # Cost rate factor
        cost_rate = driver.cost_per_km
        
        # Reliability factor (invert - higher reliability = lower cost)
        reliability_cost = 1.0 - driver.reliability_score
        
        # Rating factor (invert - higher rating = lower cost)
        rating_cost = 1.0 - (driver.rating / 5.0)
        
        # Calculate base cost
        base_cost = (
            self.WEIGHTS['distance'] * distance_cost +
            self.WEIGHTS['cost_rate'] * cost_rate +
            self.WEIGHTS['reliability'] * reliability_cost +
            self.WEIGHTS['rating'] * rating_cost
        )
        
        # Apply penalties
        penalty_multiplier = 1.0
        
        # Availability penalty
        if driver.availability == 'busy':
            penalty_multiplier *= self.AVAILABILITY_PENALTY
        
        # Vehicle mismatch penalty
        if not self._is_vehicle_suitable(driver.vehicle_type, order_size):
            penalty_multiplier *= self.VEHICLE_MISMATCH_PENALTY
        
        total_cost = base_cost * penalty_multiplier
        
        return total_cost
    
    def _is_vehicle_suitable(self, vehicle_type: str, order_size: str) -> bool:
        """Check if vehicle type is suitable for order size."""
        if order_size == 'large':
            return vehicle_type == 'bajaji'  # Need larger vehicle
        elif order_size == 'small':
            return vehicle_type == 'boda'    # Motorcycle is fine
        else:  # medium
            return True  # Both are acceptable
    
    def _generate_explanation(self, driver: Driver) -> str:
        """Generate human-readable selection explanation."""
        reasons = []
        
        if driver.distance_km < 1.0:
            reasons.append(f"Very close ({driver.distance_km:.2f}km)")
        elif driver.distance_km < 2.0:
            reasons.append(f"Nearby ({driver.distance_km:.2f}km)")
        
        if driver.rating >= 4.7:
            reasons.append(f"Excellent rating ({driver.rating}★)")
        
        if driver.reliability_score >= 0.95:
            reasons.append(f"Highly reliable ({driver.reliability_score:.0%})")
        
        if driver.cost_per_km <= 1.2:
            reasons.append("Economical")
        
        if driver.availability == 'available':
            reasons.append("Ready now")
        else:
            reasons.append("Finishing current delivery")
        
        if driver.total_trips > 500:
            reasons.append(f"Experienced ({driver.total_trips} trips)")
        
        return " | ".join(reasons) if reasons else "Qualified driver"


if __name__ == "__main__":
    # Test Engine 2
    graph = RoadGraph('../data/roads.json')
    engine = DriverAssignmentEngine(graph, '../data/drivers.json')
    
    # Test assignment
    restaurant_lat, restaurant_lon = -6.1628, 39.1922
    
    best, backups, rejected = engine.assign_driver(
        restaurant_lat, restaurant_lon,
        order_size='medium',
        num_backups=2
    )
    
    print("\n=== ASSIGNMENT COMPLETE ===")
    if best:
        print(f"Primary: {best.name} ({best.vehicle_type})")
        print(f"Backups: {', '.join([d.name for d in backups])}")
