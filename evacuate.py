import time
import requests
import networkx as nx

class EvacuationEngine:
    def __init__(self, server_url='http://127.0.0.1:5000'):
        self.server_url = server_url
        self.graph = nx.Graph()
        self.exits = ["출구_1", "출구_2", "출구_3"]
        self.zones = [f"방_{i}" for i in range(1, 16)] + [f"복도_{i}" for i in range(1, 8)]
        self.init_building_map()

    def init_building_map(self):
        self.graph.add_edge("방_1", "복도_1", base_dist=2.0)
        self.graph.add_edge("방_2", "복도_1", base_dist=2.0)
        self.graph.add_edge("방_3", "복도_2", base_dist=2.0)
        self.graph.add_edge("방_4", "복도_3", base_dist=2.0)
        self.graph.add_edge("방_5", "복도_4", base_dist=2.0)
        self.graph.add_edge("방_6", "복도_4", base_dist=2.0)
        
        self.graph.add_edge("방_7", "복도_1", base_dist=2.0)
        self.graph.add_edge("방_8", "복도_2", base_dist=2.0)
        self.graph.add_edge("방_9", "복도_5", base_dist=2.0)
        
        self.graph.add_edge("방_10", "복도_3", base_dist=2.0)
        
        self.graph.add_edge("방_11", "복도_6", base_dist=1.5)
        self.graph.add_edge("방_12", "복도_7", base_dist=1.5)
        self.graph.add_edge("방_13", "방_10", base_dist=1.5)
        self.graph.add_edge("방_15", "복도_6", base_dist=2.0)
        
        self.graph.add_edge("방_14", "복도_7", base_dist=2.0)
        
        #Hall to Hall
        self.graph.add_edge("복도_1", "복도_2", base_dist=2.5)
        self.graph.add_edge("복도_2", "복도_3", base_dist=2.5)
        self.graph.add_edge("복도_3", "복도_4", base_dist=2.5)
        self.graph.add_edge("복도_2", "복도_5", base_dist=2.5)
        self.graph.add_edge("복도_3", "복도_5", base_dist=2.5)
        self.graph.add_edge("복도_4", "복도_6", base_dist=2.5)
        self.graph.add_edge("복도_6", "복도_7", base_dist=2.5)
        
        # Hall to Gate
        self.graph.add_edge("복도_1", "출구_1", base_dist=2.0)
        self.graph.add_edge("복도_5", "출구_2", base_dist=2.0)
        self.graph.add_edge("복도_7", "출구_3", base_dist=2.0)
        
    def fetch_sensor_data(self):
        try:
            response = requests.get(f"{self.server_url}/get-data", timeout=1.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            return None
        return None

    def calculate_dynamic_weights(self, server_data):
        working_graph = self.graph.copy()
        edges_to_remove = []
        
        for u, v in working_graph.edges():
            u_fire = server_data.get(u, {}).get('fire_detected', False) if u in server_data else False
            v_fire = server_data.get(v, {}).get('fire_detected', False) if v in server_data else False
            
            if u_fire or v_fire:
                edges_to_remove.append((u, v))
                continue
                
            base_dist = working_graph[u][v]['base_dist']
            u_figure = server_data.get(u, {}).get('figure_count', 0) if u in server_data else 0
            v_figure = server_data.get(v, {}).get('figure_count', 0) if v in server_data else 0
            figure_penalty = 1.0 + (0.4 * max(u_figure, v_figure))
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
                routes[zone] = " -> ".join(best_route).replace("_", " ")
            else:
                routes[zone] = "고립됨 (대피 경로 없음)"
        try:
            requests.post(f"{self.server_url}/update-routes", json=routes, timeout=1.0)
        except Exception:
            pass

    def start_engine(self):
        while True:
            data = self.fetch_sensor_data()
            if data:
                updated_graph = self.calculate_dynamic_weights(data)
                self.find_evacuation_routes(updated_graph)
            time.sleep(0.5)

if __name__ == "__main__":
    engine = EvacuationEngine()
    engine.start_engine()