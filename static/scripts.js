const corridorAxes = {
    horizontalMain: 220,
    Hallway_5: 315,
    Hallway_6: 550,
    Hallway_7: 355
};

function getRoomDoorWaypoints(room, nextCorridor) {
    switch(room) {
        case "Room_1": return { inside: {x: 55, y: 130}, hallway: {x: 55, y: corridorAxes.horizontalMain} };
        case "Room_2": return { inside: {x: 150, y: 130}, hallway: {x: 150, y: corridorAxes.horizontalMain} };
        case "Room_3": return { inside: {x: 255, y: 170}, hallway: {x: 255, y: corridorAxes.horizontalMain} };
        case "Room_4": return { inside: {x: 365, y: 170}, hallway: {x: 365, y: corridorAxes.horizontalMain} };
        case "Room_5": return { inside: {x: 460, y: 170}, hallway: {x: 460, y: corridorAxes.horizontalMain} };
        case "Room_6": return { inside: {x: 540, y: 170}, hallway: {x: 540, y: corridorAxes.horizontalMain} };
        case "Room_7": return { inside: {x: 160, y: 270}, hallway: {x: 160, y: corridorAxes.horizontalMain} };
        case "Room_8": return { inside: {x: 240, y: 270}, hallway: {x: 240, y: corridorAxes.horizontalMain} };
        case "Room_9": return { inside: {x: 270, y: 395}, hallway: {x: corridorAxes.Hallway_5, y: 395} };
        case "Room_10": 
            if (nextCorridor === "Hallway_5") {
                return { inside: {x: 360, y: 395}, hallway: {x: corridorAxes.Hallway_5, y: 395} };
            } else {
                return { inside: {x: 390, y: 270}, hallway: {x: 390, y: corridorAxes.horizontalMain} };
            }
        case "Room_11": return { inside: {x: 510, y: 270}, hallway: {x: corridorAxes.Hallway_6, y: 270} };
        case "Room_12": return { inside: {x: 510, y: 330}, hallway: {x: corridorAxes.Hallway_6, y: 330} };
        case "Room_13": 
            return { 
                inside: {x: 485, y: 405}, 
                hallway: {x: 360, y: 405} 
            };
        case "Room_14": return { inside: {x: 595, y: 390}, hallway: {x: 595, y: corridorAxes.Hallway_7} };
        case "Room_15": return { inside: {x: 590, y: 260}, hallway: {x: corridorAxes.Hallway_6, y: 260} };
        default: return null;
    }
}

function getCorridorWaypoint(corridor) {
    switch(corridor) {
        case "Hallway_1": return { x: 140, y: corridorAxes.horizontalMain };
        case "Hallway_2": return { x: 255, y: corridorAxes.horizontalMain };
        case "Hallway_3": return { x: 365, y: corridorAxes.horizontalMain };
        case "Hallway_4": return { x: 485, y: corridorAxes.horizontalMain };
        case "Hallway_5": return { x: corridorAxes.Hallway_5, y: 300 };
        case "Hallway_6": return { x: corridorAxes.Hallway_6, y: 310 };
        case "Hallway_7": return { x: 440, y: corridorAxes.Hallway_7 };
        default: return null;
    }
}

function getExitWaypoint(exitNode) {
    switch(exitNode) {
        case "Exit_1": return { x: -5, y: 215 };
        case "Exit_2": return { x: 310, y: 436 };
        case "Exit_3": return { x: 655, y: 405 };
        default: return null;
    }
}

let currentRoutesData = {};

function showRoute(zone) {
    const routeContainer = document.getElementById('route-container');
    const routeLine = document.getElementById('route-line');
    
    if (!currentRoutesData[zone] || !currentRoutesData[zone].path || currentRoutesData[zone].path.length === 0) {
        routeContainer.innerText = `${zone.replace("Room_", "방 ").replace("Hallway_", "복도 ")}: 현재 대피 경로가 유효하지 않거나 고립되었습니다.`;
        routeLine.setAttribute('points', '');
        return;
    }
    
    const info = currentRoutesData[zone];
    routeContainer.innerText = `[대피 유도] ${info.text}`;
    
    const path = info.path;
    let points = [];
    
    if (zone.startsWith("Room_")) {
        const nextNode = path[1];
        const waypoints = getRoomDoorWaypoints(zone, nextNode);
        if (waypoints) {
            points.push(waypoints.inside);
            points.push(waypoints.hallway);
        }
    } else if (zone.startsWith("Hallway_")) {
        const pt = getCorridorWaypoint(zone);
        if (pt) points.push(pt);
    }
    
    for (let i = 1; i < path.length - 1; i++) {
        const curr = path[i];
        if (curr.startsWith("Hallway_")) {
            const pt = getCorridorWaypoint(curr);
            if (pt) points.push(pt);
        } else if (curr.startsWith("Room_")) {
            const prevNode = path[i-1];
            const nextNode = path[i+1];
            const waypoints = getRoomDoorWaypoints(curr, nextNode);
            if (waypoints) {
                points.push(waypoints.inside);
            }
        }
    }
    
    const lastNode = path[path.length - 1];
    if (lastNode.startsWith("Exit_")) {
        const pt = getExitWaypoint(lastNode);
        if (pt) points.push(pt);
    }
    
    const pointsStr = points.map(p => `${p.x},${p.y}`).join(' ');
    routeLine.setAttribute('points', pointsStr);
}

function fetchData() {
    fetch('/get-data')
        .then(res => res.json())
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
                        if (zone.startsWith("Hallway_")) {
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
        .catch(() => {});

    fetch('/get-routes')
        .then(res => res.json())
        .then(routes => {
            currentRoutesData = routes;
        })
        .catch(() => {});
}

setInterval(fetchData, 1000);
fetchData();