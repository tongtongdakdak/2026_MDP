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
            if (nextCorridor === "Room_10") {
                return { inside: {x: 440, y: 395}, hallway: {x: 390, y: 395} };
            } else {
                return { inside: {x: 510, y: 405}, hallway: {x: corridorAxes.Hallway_6, y: 405} };
            }
        case "Room_14": return { inside: {x: 595, y: 390}, hallway: {x: 595, y: corridorAxes.Hallway_7} };
        case "Room_15": return { inside: {x: 590, y: 260}, hallway: {x: corridorAxes.Hallway_6, y: 260} };
        default: return null;
    }
}

function getExitPoint(exitName) {
    switch(exitName) {
        case "Exit_1": return {x: 0, y: corridorAxes.horizontalMain};
        case "Exit_2": return {x: corridorAxes.Hallway_5, y: 440};
        case "Exit_3": return {x: 660, y: corridorAxes.Hallway_7};
        default: return null;
    }
}

function getCorridorIntersection(current, next) {
    const mainHoriz = ["Hallway_1", "Hallway_2", "Hallway_3", "Hallway_4"];
    if (mainHoriz.includes(current) && next === "Hallway_5" || current === "Hallway_5" && mainHoriz.includes(next)) {
        return {x: corridorAxes.Hallway_5, y: corridorAxes.horizontalMain};
    }
    if (mainHoriz.includes(current) && next === "Hallway_6" || current === "Hallway_6" && mainHoriz.includes(next)) {
        return {x: corridorAxes.Hallway_6, y: corridorAxes.horizontalMain};
    }
    if (mainHoriz.includes(current) && next === "Hallway_7" || current === "Hallway_7" && mainHoriz.includes(next)) {
        return {x: corridorAxes.Hallway_7, y: corridorAxes.horizontalMain};
    }
    return null;
}

const zoneCenters = {
    "Hallway_1": {x: 105, y: corridorAxes.horizontalMain},
    "Hallway_2": {x: 200, y: corridorAxes.horizontalMain},
    "Hallway_3": {x: 425, y: corridorAxes.horizontalMain},
    "Hallway_4": {x: 600, y: corridorAxes.horizontalMain},
    "Hallway_5": {x: corridorAxes.Hallway_5, y: 350},
    "Hallway_6": {x: corridorAxes.Hallway_6, y: 350},
    "Hallway_7": {x: corridorAxes.Hallway_7, y: 250}
};

let currentRouteData = {};

function showRoute(zone) {
    const routeTextContainer = document.getElementById('route-container');
    const routeCanvas = document.getElementById('route-line');
    const routeInfo = currentRouteData[zone];
    
    if (!routeInfo || !routeInfo.path || routeInfo.path.length === 0) {
        let koZone = zone.replace("Room_", "방 ").replace("Hallway_", "복도 ");
        routeTextContainer.innerText = `${koZone}: 고립됨 (대피 경로 없음)`;
        routeTextContainer.style.color = "#dc3545";
        routeCanvas.setAttribute("points", "");
        return;
    }

    routeTextContainer.innerText = `최적 대피 경로: ${routeInfo.text}`;
    routeTextContainer.style.color = "#1e40af";

    let points = [];
    let lastPos = null;
    const path = routeInfo.path;

    for(let i=0; i<path.length; i++) {
        const node = path[i];
        if (node.startsWith("Room_")) {
            const nextNode = path[i+1];
            const waypoints = getRoomDoorWaypoints(node, nextNode);
            if (waypoints) {
                points.push(`${waypoints.inside.x},${waypoints.inside.y}`);
                points.push(`${waypoints.hallway.x},${waypoints.hallway.y}`);
                lastPos = waypoints.hallway;
            }
        } else if (node.startsWith("Hallway_")) {
            const center = zoneCenters[node];
            if (lastPos && lastPos.x !== center.x && lastPos.y !== center.y) {
                const inter = getCorridorIntersection(path[i-1], node);
                if (inter) points.push(`${inter.x},${inter.y}`);
            }
            if (center) {
                points.push(`${center.x},${center.y}`);
                lastPos = center;
            }
        } else if (node.startsWith("Exit_")) {
            const exitPoint = getExitPoint(node);
            if (exitPoint) {
                if (lastPos && lastPos.x !== exitPoint.x && lastPos.y !== exitPoint.y) {
                    points.push(`${exitPoint.x},${lastPos.y}`);
                }
                points.push(`${exitPoint.x},${exitPoint.y}`);
            }
        }
    }
    routeCanvas.setAttribute("points", points.join(" "));
}

setInterval(() => {
    fetch('/get-routes')
        .then(res => res.json())
        .then(data => {
            currentRouteData = data;
        })
        .catch(() => {});
}, 1000);

function fetchData() {
    fetch('/get-data')
        .then(response => response.json())
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
}

setInterval(fetchData, 1000);
fetchData();