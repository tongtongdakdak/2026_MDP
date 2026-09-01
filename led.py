# -*- coding: utf-8 -*-
"""
led_routing.py
================
화재 발생 시, 각 복도/방의 LED 스트립을 어느 방향(출구 쪽)으로 흘려줘야 하는지
계산해서 STM32로 보낼 "start,end" 범위 메시지 리스트를 만들어주는 모듈.

설계 요약
---------
- 건물 LED 배선은 하나의 연속된 트리(나무) 구조라고 가정한다.
    출구1 -(복도1: 1~7)- B1 -(복도2: 8~11)- J(=LED12, 분기점)
                                                    |-(복도3: 13~16)- B2 -(복도4: 17~20)- B3 -(복도6: 21~25)- B4 -(복도7: 26~28)- 출구3
                                                    |-(복도5: 29~35, J쪽=35, 출구2쪽=29)- 출구2
- 각 복도(zone)는 "고정된 기본 출구(home exit)"를 가진다.
    복도1, 복도2        -> 출구1
    복도3,4,6,7         -> 출구3
    복도5                -> 출구2
    방(room)은 자신이 붙어있는 복도(host)의 기본 출구를 그대로 물려받는다.
- 화재가 나면:
    1) 화재 zone 자체는 출력하지 않음(안에서 안전한 방향이 없음).
    2) 화재 zone이 없어도(그래프에서 제거해도) 자신의 기본 출구까지 가는 경로가
       안 끊기면 -> 기본 방향 그대로 사용.
    3) 화재 때문에 기본 출구로 가는 길이 끊겼으면 -> 정션(J)을 거쳐 도달 가능한
       가장 가까운 다른 출구로 재라우팅.
    4) 방향이 같고 LED 번호가 서로 이어지는(contiguous) zone들은 하나의 메시지로
       병합한다. (예: 복도2가 8~11로 흐르고 복도1이 7~1로 흐르면 -> "11,1"로 병합)

이 모듈은 zones_config.json 과는 별개로, LED 번호/토폴로지 전용 설정을 갖는다.
방-복도 매핑, LED 범위는 실제 배선에 맞게 ROOMS / CORRIDORS 딱 이 두 딕셔너리만
수정하면 된다.
"""

from collections import deque

# ---------------------------------------------------------------------------
# 1. 토폴로지 정의 (여기만 실측값에 맞게 고치면 됨)
# ---------------------------------------------------------------------------

EXIT_NODES = {"EXIT1", "EXIT2", "EXIT3"}

# 복도(zone) 정의: nodeA/nodeB = 이 복도가 잇는 두 노드
# ledA/ledB = 각각 nodeA쪽 끝 LED번호 / nodeB쪽 끝 LED번호
# home_exit = 화재가 없을 때 기본적으로 향하는 출구
CORRIDORS = {
    "Hallway_1": dict(nodeA="EXIT1", nodeB="B1", ledA=1,  ledB=7,  home_exit="EXIT1"),
    "Hallway_2": dict(nodeA="B1",    nodeB="J",  ledA=8,  ledB=11, home_exit="EXIT1"),
    "Hallway_3": dict(nodeA="J",     nodeB="B2", ledA=13, ledB=16, home_exit="EXIT3"),
    "Hallway_4": dict(nodeA="B2",    nodeB="B3", ledA=17, ledB=20, home_exit="EXIT3"),
    "Hallway_6": dict(nodeA="B3",    nodeB="B4", ledA=21, ledB=25, home_exit="EXIT3"),
    "Hallway_7": dict(nodeA="B4",    nodeB="EXIT3", ledA=26, ledB=28, home_exit="EXIT3"),
    "Hallway_5": dict(nodeA="J",     nodeB="EXIT2", ledA=35, ledB=29, home_exit="EXIT2"),
}

# 방(room) 정의: host = 붙어있는 복도 zone 이름, led_lo/led_hi = 방 LED 범위(작은값,큰값)
# 방향은 host 복도가 흐르는 방향을 그대로 따른다 (host가 ledA->ledB 방향이면 방도
# led_lo->led_hi, host가 ledB->ledA 방향이면 방도 led_hi->led_lo).
ROOMS = {
    "Room_1":  dict(host="Hallway_1", led_lo=2,  led_hi=4),
    "Room_2":  dict(host="Hallway_1", led_lo=4,  led_hi=6),
    "Room_7":  dict(host="Hallway_1", led_lo=5,  led_hi=7),
    "Room_3":  dict(host="Hallway_2", led_lo=10, led_hi=12),
    "Room_10": dict(host="Hallway_3", led_lo=13, led_hi=15),
    "Room_13": dict(host="Hallway_3", led_lo=13, led_hi=15),
    "Room_4":  dict(host="Hallway_3", led_lo=14, led_hi=16),
    "Room_5":  dict(host="Hallway_4", led_lo=18, led_hi=20),
    "Room_6":  dict(host="Hallway_4", led_lo=20, led_hi=21),
    "Room_11": dict(host="Hallway_6", led_lo=21, led_hi=23),
    "Room_15": dict(host="Hallway_6", led_lo=23, led_hi=25),
    "Room_12": dict(host="Hallway_6", led_lo=25, led_hi=26),
    "Room_14": dict(host="Hallway_6", led_lo=25, led_hi=26),
    "Room_8":  dict(host="Hallway_5", led_lo=32, led_hi=34),
    "Room_9":  dict(host="Hallway_5", led_lo=30, led_hi=31),
}

ALL_ZONE_NAMES = set(CORRIDORS.keys()) | set(ROOMS.keys())


# ---------------------------------------------------------------------------
# 2. 그래프 유틸
# ---------------------------------------------------------------------------

def _build_adjacency(exclude_zones):
    """exclude_zones(화재 zone들)를 제외한 복도들로 노드 인접리스트를 만든다."""
    adj = {}
    for name, z in CORRIDORS.items():
        if name in exclude_zones:
            continue
        adj.setdefault(z["nodeA"], []).append((z["nodeB"], name))
        adj.setdefault(z["nodeB"], []).append((z["nodeA"], name))
    return adj


def _bfs_distances(adj, start):
    """start 노드에서 다른 모든 노드까지의 최소 hop 수. 도달 불가면 dist에 없음."""
    dist = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nxt, _zone in adj.get(cur, []):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def _shortest_path_zones(adj, start, goal):
    """start->goal 로 가는 최단 경로의 zone 이름 리스트(순서대로)."""
    prev = {start: (None, None)}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt, zone in adj.get(cur, []):
            if nxt not in prev:
                prev[nxt] = (cur, zone)
                q.append(nxt)
    if goal not in prev:
        return None
    path = []
    node = goal
    while node != start:
        pnode, zone = prev[node]
        path.append((zone, pnode, node))  # zone이 pnode->node 방향으로 쓰였음
        node = pnode
    path.reverse()
    return path  # [(zone, fromNode, toNode), ...]


# ---------------------------------------------------------------------------
# 3. 메인 계산 함수
# ---------------------------------------------------------------------------

def compute_led_routes(fire_zones):
    """
    fire_zones: 현재 화재로 감지된 zone 이름들의 iterable (예: {"Hallway_2"} 또는
                {"Room_5"} 등, latest_data의 키와 동일한 이름 사용)

    반환값: [{"zones": [...], "start_led": int, "end_led": int}, ...]
            start_led -> end_led 방향으로 LED가 흐르도록(추격 애니메이션 등) STM에 보낼 값.
    """
    fire_zones = set(fire_zones)

    adj = _build_adjacency(fire_zones)  # 화재 복도는 그래프에서 완전히 제거

    # 노드별로 각 출구까지 도달 가능한지 + 거리
    exit_dist_from = {}
    for ex in EXIT_NODES:
        if ex in adj or ex in (z["nodeA"] for z in CORRIDORS.values()) or ex in (z["nodeB"] for z in CORRIDORS.values()):
            exit_dist_from[ex] = _bfs_distances(adj, ex)
        else:
            exit_dist_from[ex] = {}

    def reachable_exits(node):
        return [ex for ex, dmap in exit_dist_from.items() if node in dmap]

    def nearest_exit(node, prefer=None):
        exits = reachable_exits(node)
        if not exits:
            return None
        if prefer and prefer in exits:
            # 선호 출구가 여전히 도달 가능하면 우선 사용 (기본 방향 유지)
            return prefer
        return min(exits, key=lambda ex: exit_dist_from[ex][node])

    # 각 (화재가 아닌) 복도 zone에 대해: 최종적으로 향할 출구와, 그 출구쪽으로
    # 향하는 다음 hop(zone)이 자기 자신의 nodeA/nodeB 중 어느 쪽인지 결정
    zone_direction = {}  # zone_name -> ("far_end_led", "near_end_led")  (near = 출구쪽)

    for name, z in CORRIDORS.items():
        if name in fire_zones:
            continue
        a, b = z["nodeA"], z["nodeB"]
        home = z["home_exit"]

        # 기본 출구(home)까지 이 zone을 거쳐 가는 경로가 아직 열려있는지 확인
        home_open = (home in exit_dist_from and a in exit_dist_from[home] and b in exit_dist_from[home])

        if home_open:
            chosen_exit = home
        else:
            # 막혔으면 a, b 각각에서 도달 가능한 가장 가까운 출구를 보고 결정
            exits_a = reachable_exits(a)
            exits_b = reachable_exits(b)
            common = set(exits_a) & set(exits_b)
            if common:
                chosen_exit = min(common, key=lambda ex: exit_dist_from[ex][a] + exit_dist_from[ex][b])
            else:
                # a, b가 서로 다른 출구쪽으로만 연결된 특수한 경우 -> 이 zone은
                # 통행 불가로 처리 (스킵)
                continue

        if chosen_exit not in exit_dist_from or a not in exit_dist_from[chosen_exit] or b not in exit_dist_from[chosen_exit]:
            continue

        da = exit_dist_from[chosen_exit][a]
        db = exit_dist_from[chosen_exit][b]
        if da < db:
            # a가 출구에 더 가까움 -> b(far)에서 a(near)로 흐름
            zone_direction[name] = dict(exit=chosen_exit, far_node=b, near_node=a,
                                         start_led=z["ledB"], end_led=z["ledA"])
        else:
            zone_direction[name] = dict(exit=chosen_exit, far_node=a, near_node=b,
                                         start_led=z["ledA"], end_led=z["ledB"])

    # ---- 방(room) 방향은 host 복도를 그대로 따른다 ----
    room_direction = {}
    for rname, r in ROOMS.items():
        if rname in fire_zones:
            continue
        host = r["host"]
        if host in fire_zones or host not in zone_direction:
            continue  # host 복도 자체가 통행 불가면 방도 출력하지 않음
        hd = zone_direction[host]
        # host가 ledA->ledB 방향(작->큰)으로 흐르면 방도 lo->hi, 반대면 hi->lo
        host_increasing = hd["start_led"] < hd["end_led"]
        if host_increasing:
            room_direction[rname] = dict(start_led=r["led_lo"], end_led=r["led_hi"])
        else:
            room_direction[rname] = dict(start_led=r["led_hi"], end_led=r["led_lo"])

    # ---- 인접하고 방향이 이어지는(번호가 연속인) 복도들을 하나의 메시지로 병합 ----
    # LED 번호가 물리적으로 이어져 있으므로, "end_led" 바로 다음(진행방향으로 +-1)이
    # 다른 zone의 "start_led"와 일치하고 진행 방향이 같으면 하나의 흐름으로 병합한다.
    merged = []
    used = set()
    corridor_names = list(zone_direction.keys())

    by_start_led = {}
    for name in corridor_names:
        by_start_led[zone_direction[name]["start_led"]] = name

    def extend_forward(name):
        chain = [name]
        used.add(name)
        cur = name
        while True:
            hd = zone_direction[cur]
            increasing = hd["end_led"] > hd["start_led"]
            step = 1 if increasing else -1
            next_start = hd["end_led"] + step
            nxt = by_start_led.get(next_start)
            if nxt is None or nxt in used or nxt not in zone_direction:
                break
            nhd = zone_direction[nxt]
            n_increasing = nhd["end_led"] > nhd["start_led"]
            if n_increasing != increasing:
                break
            chain.append(nxt)
            used.add(nxt)
            cur = nxt
        return chain

    has_predecessor = set()
    for name in corridor_names:
        hd = zone_direction[name]
        increasing = hd["end_led"] > hd["start_led"]
        step = 1 if increasing else -1
        prev_end = hd["start_led"] - step
        for other in corridor_names:
            if other == name:
                continue
            ohd = zone_direction[other]
            if ohd["end_led"] == prev_end:
                o_increasing = ohd["end_led"] > ohd["start_led"]
                if o_increasing == increasing:
                    has_predecessor.add(name)
                    break

    chain_starts = [n for n in corridor_names if n not in has_predecessor]
    for name in chain_starts:
        if name in used:
            continue
        chain = extend_forward(name)
        start_led = zone_direction[chain[0]]["start_led"]
        end_led = zone_direction[chain[-1]]["end_led"]
        merged.append({"zones": chain, "start_led": start_led, "end_led": end_led})

    for name in corridor_names:
        if name not in used:
            hd = zone_direction[name]
            merged.append({"zones": [name], "start_led": hd["start_led"], "end_led": hd["end_led"]})

    # 방은 각자 독립적인 메시지로 출력 (필요하면 여기서도 병합 로직 추가 가능)
    for rname, rd in room_direction.items():
        merged.append({"zones": [rname], "start_led": rd["start_led"], "end_led": rd["end_led"]})

    return merged


def format_serial_messages(routes):
    """STM으로 보낼 문자열 리스트로 변환. 필요에 맞게 포맷 수정.
    형식: "ZONE1+ZONE2,start,end\\n"
    """
    lines = []
    for r in routes:
        zone_str = "+".join(r["zones"])
        lines.append(f"{zone_str},{r['start_led']},{r['end_led']}\n")
    return lines

if __name__ == "__main__":
    import requests
    import time

    SERVER_URL = "http://127.0.0.1:5000"
    print("[LED Engine] 최단 경로 연산 엔진이 시작되었습니다.")

    while True:
        try:
            # 1. 서버로부터 실시간 센서/인원 데이터 가져오기
            response = requests.get(f"{SERVER_URL}/get-data", timeout=1.0)
            if response.status_code == 200:
                sensor_data = response.json()
                
                # 2. 화재가 감지된 구역(zone) 리스트 추출
                fire_zones = [zone for zone, status in sensor_data.items() if status.get("fire_detected", False)]
                
                # 3. 화재 구역을 우회하는 LED 경로 계산
                routes = compute_led_routes(fire_zones)
                
                # 4. 계산된 경로 결과를 서버에 업데이트
                requests.post(f"{SERVER_URL}/update-routes", json=routes, timeout=1.0)
        except Exception as e:
            # 서버가 아직 켜지지 않았거나 통신 에러가 발생했을 때 프로세스가 죽지 않도록 예외 처리
            pass
        
        # 1초 간격으로 반복 수행
        time.sleep(1)