import time
import requests
import networkx as nx

class EvacuationEngine:
    def __init__(self, server_url='http://127.0.0.1:5000'):
        self.server_url = server_url
        self.graph = nx.Graph()
        self.exits = ["Exit_1", "Exit_2", "Exit_3"]
        self.zones = [f"Room_{i}" for i in range(1, 16)] + [f"Hallway_{i}" for i in range(1, 8)]
        self.init_building_map()

    def init_building_map(self):
        self.graph.add_edge("Room_1", "Hallway_1", base_dist=2.0)
        self.graph.add_edge("Room_2", "Hallway_1", base_dist=2.0)
        self.graph.add_edge("Room_3", "Hallway_2", base_dist=2.0)
        self.graph.add_edge("Room_4", "Hallway_3", base_dist=2.0)
        self.graph.add_edge("Room_5", "Hallway_4", base_dist=2.0)
        self.graph.add_edge("Room_6", "Hallway_4", base_dist=2.0)
        self.graph.add_edge("Room_7", "Hallway_1", base_dist=2.0)
        self.graph.add_edge("Room_8", "Hallway_2", base_dist=2.0)
        self.graph.add_edge("Room_9", "Hallway_5", base_dist=2.0)
        self.graph.add_edge("Room_10", "Hallway_3", base_dist=2.0)
        self.graph.add_edge("Room_11", "Hallway_6", base_dist=1.5)
        self.graph.add_edge("Room_12", "Hallway_7", base_dist=1.5)
        self.graph.add_edge("Room_13", "Room_10", base_dist=1.5)
        self.graph.add_edge("Room_15", "Hallway_6", base_dist=2.0)
        self.graph.add_edge("Room_14", "Hallway_7", base_dist=2.0)
        self.graph.add_edge("Hallway_1", "Hallway_2", base_dist=3.0)
        self.graph.add_edge("Hallway_2", "Hallway_3", base_dist=3.0)
        self.graph.add_edge("Hallway_3", "Hallway_4", base_dist=3.0)
        self.graph.add_edge("Hallway_2", "Hallway_5", base_dist=3.0)
        self.graph.add_edge("Hallway_3", "Hallway_6", base_dist=3.0)
        self.graph.add_edge("Hallway_4", "Hallway_7", base_dist=3.0)
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
            if data.get(u, {}).get('fire_detected', False) or data.get(v, {}).get('fire_detected', False):
                edges_to_remove.append((u, v))
                continue
            u_count = data.get(u, {}).get('figure_count', 0)
            v_count = data.get(v, {}).get('figure_count', 0)
            figure_penalty = 1.0 + ((u_count + v_count) * 0.2)
            working_graph[u][v]['weight'] = base_dist * figure_penalty
        working_graph.remove_edges_from(edges_to_remove)
        return working_graph

    def find_evacuation_routes(self, current_graph):
        routes = {}
        for zone in self.zones:
            best_route = None
            min_cost = float('inf')
            for exit_node in self.exits:
                try:
                    path = nx.dijkstra_path(current_graph, source=zone, target=exit_node, weight='weight')
                    cost = nx.dijkstra_path_length(current_graph, source=zone, target=exit_node, weight='weight')
                    if cost < min_cost:
                        min_cost = cost
                        best_route = path
                except nx.NetworkXNoPath:
                    continue
            if best_route:
                kor_text = " -> ".join([n.replace("Room_", "방 ").replace("Hallway_", "복도 ").replace("Exit_", "출구 ") for n in best_route])
                routes[zone] = {"text": kor_text, "path": best_route}
            else:
                routes[zone] = {"text": "고립됨 (대피 경로 없음)", "path": []}
        try:
            requests.post(f"{self.server_url}/update-routes", json=routes, timeout=1.0)
        except:
            pass

    def start_engine(self):
        while True:
            data = self.fetch_sensor_data()
            if data:
                updated_graph = self.calculate_dynamic_weights(data)
                self.find_evacuation_routes(updated_graph)
            time.sleep(1)

if __name__ == "__main__":
    engine = EvacuationEngine()
    engine.start_engine()