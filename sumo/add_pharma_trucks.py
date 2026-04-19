"""
add_pharma_trucks.py
--------------------
SUMO vehicle type definitions and route generation for pharmaceutical trucks.

Pharma trucks have:
  - Type: pharma_truck (slower acceleration, longer vehicle)
  - Color: white (RGB 255 255 255) — visual distinction from regular traffic
  - Length: 12m (vs standard 5m)
  - Max acceleration: 1.2 m/s² (vs standard 2.6 m/s²)
  - Used by cold-chain RL agent for priority signal control

Usage:
  - Add vType definitions to routes.rou.xml
  - Add 2-3 pharma_truck-typed vehicles to the route file
"""

PHARMA_VTYPE_XML = """
  <!-- Pharmaceutical delivery truck (cold-chain) -->
  <vType id="pharma_truck" 
         length="12.0" 
         maxSpeed="20.0"
         accel="1.2"
         decel="4.5"
         color="255,255,255"
         vClass="delivery"
         guiShape="delivery">
  </vType>
"""

PHARMA_ROUTE_XML = """
  <!-- Pharmaceutical truck routes -->
  <route id="pharma_route_0" edges="e1 e2 e3 e4 e5"/>
  <route id="pharma_route_1" edges="e5 e4 e3 e2 e1"/>
  
  <!-- Vehicle: Pharma Truck 1 (depart 300s, corridor northbound) -->
  <vehicle id="pharma_truck_1" 
           type="pharma_truck" 
           route="pharma_route_0" 
           depart="300.0">
  </vehicle>
  
  <!-- Vehicle: Pharma Truck 2 (depart 400s, corridor southbound) -->
  <vehicle id="pharma_truck_2" 
           type="pharma_truck" 
           route="pharma_route_1" 
           depart="400.0">
  </vehicle>
  
  <!-- Vehicle: Pharma Truck 3 (depart 500s, corridor northbound) -->
  <vehicle id="pharma_truck_3" 
           type="pharma_truck" 
           route="pharma_route_0" 
           depart="500.0">
  </vehicle>
"""


def inject_pharma_trucks_into_route_file(route_file_path: str) -> None:
    """
    Inject pharma truck vType and vehicle definitions into an existing SUMO route file.
    
    Args:
        route_file_path: Path to routes.rou.xml
    """
    try:
        with open(route_file_path, 'r') as f:
            content = f.read()
        
        # Insert vType before first <route> tag
        if '<route' in content and '<vType id="pharma_truck"' not in content:
            insert_pos = content.find('<route')
            content = content[:insert_pos] + PHARMA_VTYPE_XML + '\n' + content[insert_pos:]
        
        # Append pharma vehicles before closing </routes>
        if '</routes>' in content:
            insert_pos = content.rfind('</routes>')
            content = content[:insert_pos] + PHARMA_ROUTE_XML + '\n' + content[insert_pos:]
        
        with open(route_file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Injected pharma trucks into {route_file_path}")
    
    except Exception as e:
        print(f"✗ Failed to inject pharma trucks: {e}")


if __name__ == '__main__':
    # Example: inject into sumo/routes.rou.xml
    import os
    sumo_dir = os.path.dirname(os.path.abspath(__file__))
    route_file = os.path.join(sumo_dir, 'routes.rou.xml')
    
    if os.path.exists(route_file):
        inject_pharma_trucks_into_route_file(route_file)
    else:
        print(f"Route file not found: {route_file}")
        print("\nPharma vType definition:")
        print(PHARMA_VTYPE_XML)
        print("\nPharma vehicle routes:")
        print(PHARMA_ROUTE_XML)
