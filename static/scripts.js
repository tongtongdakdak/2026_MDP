// 📍 도면 복도 중앙선 정밀 좌표 인덱스
const corridorAxes = {
    horizontalMain: 220, // 복도 1, 2, 3, 4의 공통 가로 중심선 (Y축)
    복도_5: 315,         // 복도 5 세로 중심선 (X축)
    복도_6: 550,         // 복도 6 세로 중심선 (X축)
    복도_7: 355          // 복도 7 가로 중심선 (Y축)
};

// 📍 방 내부에서 문을 거쳐 복도로 수직/수평 탈출하는 유도 포인트 세트
function getRoomDoorWaypoints(room, nextCorridor) {
    switch(room) {
        case "방_1":  return { inside: {x: 55, y: 130}, hallway: {x: 55, y: corridorAxes.horizontalMain} };
        case "방_2":  return { inside: {x: 150, y: 130}, hallway: {x: 150, y: corridorAxes.horizontalMain} };
        case "방_3":  return { inside: {x: 255, y: 170}, hallway: {x: 255, y: corridorAxes.horizontalMain} };
        case "방_4":  return { inside: {x: 365, y: 170}, hallway: {x: 365, y: corridorAxes.horizontalMain} };
        case "방_5":  return { inside: {x: 460, y: 170}, hallway: {x: 460, y: corridorAxes.horizontalMain} };
        case "방_6":  return { inside: {x: 540, y: 170}, hallway: {x: 540, y: corridorAxes.horizontalMain} };
        case "방_7":  return { inside: {x: 160, y: 270}, hallway: {x: 160, y: corridorAxes.horizontalMain} };
        case "방_8":  return { inside: {x: 240, y: 270}, hallway: {x: 240, y: corridorAxes.horizontalMain} };
        case "방_9":  return { inside: {x: 270, y: 395}, hallway: {x: corridorAxes.복도_5, y: 395} };
        case "방_10": 
            if (nextCorridor === "복도_5") {
                return { inside: {x: 360, y: 395}, hallway: {x: corridorAxes.복도_5, y: 395} };
            } else {
                return { inside: {x: 390, y: 270}, hallway: {x: 390, y: corridorAxes.horizontalMain} };
            }
        case "방_11": return { inside: {x: 510, y: 270}, hallway: {x: corridorAxes.복도_6, y: 270} };
        case "방_12": return { inside: {x: 510, y: 330}, hallway: {x: corridorAxes.복도_6, y: 330} };
        case "방_13": return { inside: {x: 510, y: 405}, hallway: {x: corridorAxes.복도_6, y: 405} };
        case "방_14": return { inside: {x: 595, y: 390}, hallway: {x: 595, y: corridorAxes.복도_7} };
        case "방_15": return { inside: {x: 590, y: 260}, hallway: {x: corridorAxes.복도_6, y: 260} };
        default: return null;
    }
}

// 📍 최종 탈출구 터미널 포인트
function getExitPoint(exitName) {
    switch(exitName) {
        case "출구_1": return {x: 0, y: corridorAxes.horizontalMain};
        case "출구_2": return {x: corridorAxes.복도_5, y: 440};
        case "출구_3": return {x: 660, y: corridorAxes.복도_7};
        default: return null;
    }
}

// 📍 복도와 복도가 교차하여 회전할 때 생성되는 90도 직각 노드 산출 엔진
function getCorridorIntersection(current, next) {
    const mainHoriz = ["복도_1", "복도_2", "복도_3", "복도_4"];
    
    if (mainHoriz.includes(current) && next === "복도_5") return {x: corridorAxes.복도_5, y: corridorAxes.horizontalMain};
    if (mainHoriz.includes(current) && next === "복도_6") return {x: corridorAxes.복도_6, y: corridorAxes.horizontalMain};
    if (current === "복도_5" && mainHoriz.includes(next)) return {x: corridorAxes.복도_5, y: corridorAxes.horizontalMain};
    if (current === "복도_6" && mainHoriz.includes(next)) return {x: corridorAxes.복도_6, y: corridorAxes.horizontalMain};
    if (current === "복도_6" && next === "복도_7") return {x: corridorAxes.복도_6, y: corridorAxes.복도_7};
    if (current === "복도_7" && next === "복도_6") return {x: corridorAxes.복도_6, y: corridorAxes.복도_7};
    
    return null;
}

// 📍 정밀 직각 선 렌더링 함수
function drawOrthogonalRoute(routeText) {
    const polyline = document.getElementById('route-line');
    if (!routeText || routeText.includes("고립됨")) {
        polyline.setAttribute("points", "");
        return;
    }

    // "방 13 -> 복도 6 -> 복도 7 -> 출구 3" 공백 제거 및 토큰화
    const tokens = routeText.split("->").map(t => t.trim().replace(" ", "_"));
    let points = [];

    // 1. 출발지 노드 처리
    if (tokens[0].startsWith("방")) {
        const waypoints = getRoomDoorWaypoints(tokens[0], tokens[1]);
        if (waypoints) {
            points.push(waypoints.inside);   // 방 내부 시작
            points.push(waypoints.hallway);  // 복도 축 안착
        }
    } else if (tokens[0].startsWith("복도")) {
        // 복도에서 직접 시작할 경우 텍스트 라벨 좌표 추정 매핑
        const labelPositions = { "복도_1": 90, "복도_2": 230, "복도_3": 370, "복도_4": 500 };
        if (labelPositions[tokens[0]]) {
            points.push({x: labelPositions[tokens[0]], y: corridorAxes.horizontalMain});
        } else if (tokens[0] === "복도_5") {
            points.push({x: corridorAxes.복도_5, y: 320});
        } else if (tokens[0] === "복도_6") {
            points.push({x: corridorAxes.복도_6, y: 250});
        } else if (tokens[0] === "복도_7") {
            points.push({x: 585, y: corridorAxes.복도_7});
        }
    }

    // 2. 복도 교차 구간 90도 회전점 추적
    for (let i = 1; i < tokens.length - 1; i++) {
        const curr = tokens[i];
        const next = tokens[i+1];
        if (curr.startsWith("복도")) {
            const turnPoint = getCorridorIntersection(curr, next);
            if (turnPoint) {
                points.push(turnPoint);
            }
        }
    }

    // 3. 목적지 탈출구 매핑
    const lastToken = tokens[tokens.length - 1];
    if (lastToken.startsWith("출구")) {
        const exitPoint = getExitPoint(lastToken);
        if (exitPoint) points.push(exitPoint);
    }

    // 4. SVG Polyline 요소에 좌표 문자열 주입 ("x,y x,y ...")
    const pointsString = points.map(p => `${p.x},${p.y}`).join(" ");
    polyline.setAttribute("points", pointsString);
}

// 📍 클릭 시 라우팅 정보 표시 연동
function showRoute(zone) {
    fetch('/get-routes')
        .then(response => response.json())
        .then(routes => {
            const container = document.getElementById('route-container');
            let displayZone = zone.replace("_", " ");
            if (routes && routes[zone]) {
                container.innerText = displayZone + " 대피 경로: " + routes[zone];
                drawOrthogonalRoute(routes[zone]); // 직각 경로 그리기 실행
            } else {
                container.innerText = "경로 정보를 가져오는 중이거나 경로가 없습니다.";
                document.getElementById('route-line').setAttribute("points", "");
            }
        })
        .catch(error => console.error("Route Fetch Error:", error));
}

// 📍 센서 모니터링 주기 데이터 수신 전송
function fetchData() {
    fetch('/get-data?_=' + Date.now())
        .then(response => {
            if (!response.ok) throw new Error('Data Error');
            return response.json();
        })
        .then(data => {
            let totalFigureCount = 0;
            let isAnyFireDetected = false;
            Object.keys(data).forEach(zone => {
                const zoneData = data[zone];
                totalFigureCount += zoneData.figure_count;
                const countEl = document.getElementById(`count-${zone}`);
                if (countEl) countEl.innerText = zoneData.figure_count;
                
                const cardEl = document.getElementById(`card-${zone}`);
                if (cardEl) {
                    if (zoneData.fire_detected) {
                        isAnyFireDetected = true;
                        if (zone.startsWith("복도")) {
                            cardEl.classList.add('hallway-fire');
                        } else {
                            cardEl.classList.add('zone-fire');
                        }
                    } else {
                        cardEl.classList.remove('zone-fire', 'hallway-fire');
                    }
                }
            });
            document.getElementById('total-count').innerText = totalFigureCount;
            const totalStatusEl = document.getElementById('total-status');
            if (isAnyFireDetected) {
                totalStatusEl.innerText = "화재 발생!";
                totalStatusEl.style.color = "#dc3545";
            } else {
                totalStatusEl.innerText = "안전";
                totalStatusEl.style.color = "#16a34a";
            }
        })
        .catch(error => console.error("Data Fetch Error:", error));
}

// 초기 로드 루프 가동
setInterval(fetchData, 1000);
fetchData();