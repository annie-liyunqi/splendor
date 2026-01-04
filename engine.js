// engine.js - 动态状态管理
let gameState = {
    started: false,
    nobles: [],
    market: { tier1: [], tier2: [], tier3: [] },
    decks: { tier1: [], tier2: [], tier3: [] },
    bank: { white: 0, blue: 0, green: 0, red: 0, black: 0, gold: 5 },
    players: [],
    turn: 0,
    gemsTaken: 0
};

function getGemLimit(playerCount) {
    if (playerCount === 2) return 4;
    if (playerCount === 3) return 5;
    if (playerCount === 4) return 7;
    if (playerCount === 5) return 8;
    return 0;
}

function checkNobles(player) {
    let earnedIdx = -1;
    gameState.nobles.forEach((n, idx) => {
        if (earnedIdx !== -1) return;
        let match = true;
        for (let color in n.cost) {
            if ((player.bonus[color] || 0) < n.cost[color]) match = false;
        }
        if (match) earnedIdx = idx;
    });

    if (earnedIdx !== -1) {
        const noble = gameState.nobles.splice(earnedIdx, 1)[0];
        player.score += noble.points;
        return true;
    }
    return false;
}

function canAfford(player, card) {
    for (let color in card.cost) {
        const need = card.cost[color];
        const have = (player.gems[color] || 0) + (player.bonus[color] || 0);
        if (have < need) return false;
    }
    return true;
}