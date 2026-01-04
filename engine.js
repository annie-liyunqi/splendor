// engine.js - 逻辑核心
let gameState = {
    started: false,
    nobles: [],
    market: { tier1: [], tier2: [], tier3: [] },
    decks: { tier1: [], tier2: [], tier3: [] },
    bank: { white: 0, blue: 0, green: 0, red: 0, black: 0, gold: 5 },
    players: [], // 存储玩家实时数据
    playerNames: {}, // 格式 { peerId: customName }
    turn: 0,
    gemsTaken: 0
};

function getGemLimit(playerCount) {
    if (playerCount === 2) return 4;
    if (playerCount === 3) return 5;
    return 7; // 4人
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

// engine.js 核心逻辑补充
function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

// 检查是否有人达到15分
function checkGameEndCondition() {
    return gameState.players.some(p => p.score >= 15);
}

// 计算排名逻辑
function getFinalRankings() {
    return [...gameState.players].sort((a, b) => {
        if (b.score !== a.score) {
            return b.score - a.score; // 分数高者在前
        }
        // 如果分数相同，后手排名靠前
        // 逻辑：在 players 数组中索引（index）较大的人是后手
        const indexA = gameState.players.findIndex(p => p.id === a.id);
        const indexB = gameState.players.findIndex(p => p.id === b.id);
        return indexB - indexA; 
    });
}