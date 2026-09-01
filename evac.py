import time
import requests
import networkx as nx

class Evac:
    def __init__(self, server_url='http://127.0.0.1:5000'):
        self.server_url = server_url
        self.graph = nx.Graph()
        self.exits = ["Exit_1", "Exit_2", "Exit_3"]
        self.zones = [f"Room_{i}" for i in range(1, 16)] + [f"Hallway_{i}" for i in range(1, 8)]
        
        self.direction_map = {
            ("Hallway_1", "Hallway_2"): "forward",
            ("Hallway_2", "Hallway_1"): "reverse",
            ("Hallway_2", "Hallway_3"): "forward",
            ("Hallway_3", "Hallway_2"): "reverse",
            ("Hallway_3", "Hallway_4"): "forward",
            ("Hallway_4", "Hallway_3"): "forward",
            ("Hallway_4", "Hallway_6"): "forward",
            ("Hallway_6", "Hallway_4"): "reverse",
            ("Hallway_6", "Hallway_7"): "forward",
            ("Hallway_7", "Hallway_6"): "reverse",
            ("Hallway_2", "Hallway_5"): "forward",
            ("Hallway_5", "Hallway_2"): "reverse",
            ("Hallway_3", "Hallway_5"): "reverse",
            ("Hallway_5", "Hallway_3"): "reverse",
            ("Hallway_1", "Exit_1"): "reverse",
            ("Hallway_5", "Exit_2"): "forward",
            ("Hallway_7", "Exit_3"): "forward",
        }
        
        self.init_building_map()

    def init_building_map(self):
        self.graph.add_edge("Room_1", "Hallway_1", base_dist=1.0)
        self.graph.add_edge("Room_2", "Hallway_1", base_dist=1.0)
        self.graph.add_edge("Room_3", "Hallway_2", base_dist=1.0)
        self.graph.add_edge("Room_4", "Hallway_3", base_dist=1.0)
        self.graph.add_edge("Room_5", "Hallway_3", base_dist=1.5)
        self.graph.add_edge("Room_5", "Hallway_4", base_dist=1.5)
        self.graph.add_edge("Room_6", "Hallway_4", base_dist=1.0)
        self.graph.add_edge("Room_7", "Hallway_1", base_dist=1.0)
        self.graph.add_edge("Room_8", "Hallway_2", base_dist=1.0)
        self.graph.add_edge("Room_9", "Hallway_5", base_dist=1.0)
        self.graph.add_edge("Room_10", "Hallway_3", base_dist=1.0)
        self.graph.add_edge("Room_11", "Hallway_6", base_dist=1.0)
        self.graph.add_edge("Room_12", "Hallway_6", base_dist=1.5)
        self.graph.add_edge("Room_12", "Hallway_7", base_dist=1.5)
        self.graph.add_edge("Room_13", "Room_10", base_dist=1.0)
        self.graph.add_edge("Room_14", "Hallway_7", base_dist=1.0)
        self.graph.add_edge("Room_15", "Hallway_4", base_dist=1.5)
        self.graph.add_edge("Room_15", "Hallway_6", base_dist=1.5)

        self.graph.add_edge("Hallway_1", "Hallway_2", base_dist=2.0)
        self.graph.add_edge("Hallway_2", "Hallway_3", base_dist=2.5)
        self.graph.add_edge("Hallway_2", "Hallway_5", base_dist=2.0)
        self.graph.add_edge("Hallway_3", "Hallway_4", base_dist=1.5)
        self.graph.add_edge("Hallway_3", "Hallway_5", base_dist=1.5)
        self.graph.add_edge("Hallway_4", "Hallway_6", base_dist=1.4)
        self.graph.add_edge("Hallway_6", "Hallway_7", base_dist=1.5)

        self.graph.add_edge("Hallway_1", "Exit_1", base_dist=1.0)
        self.graph.add_edge("Hallway_5", "Exit_2", base_dist=1.0)
        self.graph.add_edge("Hallway_7", "Exit_3", base_dist=1.0)

    def fetch_sensor_data(self):
        try:
            response = requests.get(f"{self.server_url}/get-data", timeout=1.0)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def calculate_dynamic_weights(self, data):
        working_graph = self.graph.copy()
        edges_to_remove = []
        
        for u, v in working_graph.edges():
            base_dist = working_graph[u][v]['base_dist']
            u_count = data.get(u, {}).get('figure_count', 0)
            v_count = data.get(v, {}).get('figure_count', 0)
            
            figure_penalty = 1.0 + ((u_count + v_count) * 0.2)
            working_graph[u][v]['weight'] = base_dist * figure_penalty

        for u in list(working_graph.nodes()):
            if data.get(u, {}).get('fire_detected', False):
                for neighbor in list(working_graph.neighbors(u)):
                    edges_to_remove.append((u, neighbor))
                        
        for u, v in edges_to_remove:
            if working_graph.has_edge(u, v):
                working_graph.remove_edge(u, v)
                    
        return working_graph

    def find_evacuation_routes(self, current_graph, data):
        routes = {}
        for zone in self.zones:
            valid_routes = []
            for exit_node in self.exits:
                try:
                    generator = nx.shortest_simple_paths(current_graph, source=zone, target=exit_node, weight='weight')
                    count = 0
                    for path in generator:
                        cost = nx.path_weight(current_graph, path, weight='weight')
                        total_people = sum(data.get(node, {}).get('figure_count', 0) for node in path)
                        
                        valid_routes.append({
                            "cost": cost,
                            "path": path,
                            "people": total_people
                        })
                        count += 1
                        if count >= 2: 
                            break
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            valid_routes.sort(key=lambda x: x['cost'])

            best_route = None
            if len(valid_routes) >= 2:
                st = valid_routes[0]
                nd = valid_routes[1]
                
                if st['people'] - nd['people'] >= 5:
                    best_route = nd['path']
                else:
                    best_route = st['path']
            elif len(valid_routes) == 1:
                best_route = valid_routes[0]['path']

            if best_route:
                kor_text = " -> ".join([n.replace("Room_", "방 ").replace("Hallway_", "복도 ").replace("Exit_", "출구 ") for n in best_route])
                routes[zone] = {"text": kor_text, "path": best_route}
            else:
                routes[zone] = {"text": "no EXIT", "path": []}
                
        forward_list = []
        reverse_list = []
        
        for i in range(1, 8):
            zone_key = f"Hallway_{i}"
            zone_name = f"Hallway{i}"
            
            if data.get(zone_key, {}).get('fire_detected', False):
                continue

            if zone_key in routes:
                path = routes[zone_key].get("path", [])
                if zone_key in path:
                    current_index = path.index(zone_key)
                    if current_index + 1 < len(path):
                        next_node = path[current_index + 1]
                        
                        direction = self.direction_map.get((zone_key, next_node))
                        if direction == "forward":
                            forward_list.append(zone_name)
                        elif direction == "reverse":
                            reverse_list.append(zone_name)
                            
        payload = {
            "routes": routes,
            "directions": {
                "forward": forward_list,
                "reverse": reverse_list
            }
        }
                
        try:
            requests.post(f"{self.server_url}/update-routes", json=payload, timeout=1.0)
        except:
            pass

    def start_engine(self):
        while True:
            data = self.fetch_sensor_data()
            if data:
                updated_graph = self.calculate_dynamic_weights(data)
                self.find_evacuation_routes(updated_graph, data)
            time.sleep(1)

if __name__ == "__main__":
    engine = Evac()
    engine.start_engine()
    