/**
 * 宝石商人 (Splendor) 完整 90 张卡牌数据库
 * 结构：points(分数), bonus(产出宝石), cost(消耗宝石)
 */
const FULL_CARD_POOL = {
    // 一阶卡池 (Level 1) - 共 40 张
    level1: [
        { points: 0, bonus: 'white', cost: { blue: 1, green: 1, red: 1, black: 1 } },
        { points: 0, bonus: 'white', cost: { blue: 1, green: 2, red: 1, black: 1 } },
        { points: 0, bonus: 'white', cost: { red: 2, black: 1 } },
        { points: 0, bonus: 'white', cost: { blue: 2, green: 2, black: 1 } },
        { points: 0, bonus: 'white', cost: { white: 3, blue: 1, black: 1 } },
        { points: 0, bonus: 'white', cost: { blue: 2, black: 2 } },
        { points: 0, bonus: 'white', cost: { blue: 3 } },
        { points: 1, bonus: 'white', cost: { green: 4 } },

        { points: 0, bonus: 'blue', cost: { white: 1, green: 1, red: 1, black: 1 } },
        { points: 0, bonus: 'blue', cost: { white: 1, green: 1, red: 2, black: 1 } },
        { points: 0, bonus: 'blue', cost: { white: 1, black: 2 } },
        { points: 0, bonus: 'blue', cost: { white: 1, green: 2, red: 2 } },
        { points: 0, bonus: 'blue', cost: { blue: 1, green: 3, red: 1 } },
        { points: 0, bonus: 'blue', cost: { green: 2, black: 2 } },
        { points: 0, bonus: 'blue', cost: { black: 3 } },
        { points: 1, bonus: 'blue', cost: { red: 4 } },

        { points: 0, bonus: 'green', cost: { white: 1, blue: 1, red: 1, black: 1 } },
        { points: 0, bonus: 'green', cost: { white: 1, blue: 1, red: 1, black: 2 } },
        { points: 0, bonus: 'green', cost: { white: 2, blue: 1 } },
        { points: 0, bonus: 'green', cost: { blue: 1, red: 2, black: 2 } },
        { points: 0, bonus: 'green', cost: { white: 1, blue: 3, green: 1 } },
        { points: 0, bonus: 'green', cost: { blue: 2, red: 2 } },
        { points: 0, bonus: 'green', cost: { red: 3 } },
        { points: 1, bonus: 'green', cost: { black: 4 } },

        { points: 0, bonus: 'red', cost: { white: 1, blue: 1, green: 1, black: 1 } },
        { points: 0, bonus: 'red', cost: { white: 2, blue: 1, green: 1, black: 1 } },
        { points: 0, bonus: 'red', cost: { green: 1, blue: 2 } },
        { points: 0, bonus: 'red', cost: { white: 2, green: 1, black: 2 } },
        { points: 0, bonus: 'red', cost: { white: 1, red: 1, black: 3 } },
        { points: 0, bonus: 'red', cost: { white: 2, red: 2 } },
        { points: 0, bonus: 'red', cost: { white: 3 } },
        { points: 1, bonus: 'red', cost: { white: 4 } },

        { points: 0, bonus: 'black', cost: { white: 1, blue: 1, green: 1, red: 1 } },
        { points: 0, bonus: 'black', cost: { white: 1, blue: 2, green: 1, red: 1 } },
        { points: 0, bonus: 'black', cost: { green: 2, red: 1 } },
        { points: 0, bonus: 'black', cost: { white: 2, green: 2 } },
        { points: 0, bonus: 'black', cost: { green: 1, red: 3, black: 1 } },
        { points: 0, bonus: 'black', cost: { white: 2, blue: 2, red: 1 } },
        { points: 0, bonus: 'black', cost: { green: 3 } },
        { points: 1, bonus: 'black', cost: { blue: 4 } }
    ],

    // 二阶卡池 (Level 2) - 共 30 张
    level2: [
        { points: 1, bonus: 'white', cost: { green: 3, red: 2, black: 2 } },
        { points: 1, bonus: 'white', cost: { white: 2, blue: 3, red: 3 } },
        { points: 2, bonus: 'white', cost: { green: 1, red: 4, black: 2 } },
        { points: 2, bonus: 'white', cost: { red: 5} },
        { points: 2, bonus: 'white', cost: { red: 5, black: 3 } },
        { points: 3, bonus: 'white', cost: { white: 6 } },

        { points: 1, bonus: 'blue', cost: { blue: 2, green: 3, black: 3 } },
        { points: 1, bonus: 'blue', cost: { blue: 2, green: 2, red: 3 } },
        { points: 2, bonus: 'blue', cost: { white: 2, red: 1, black: 4 } },
        { points: 2, bonus: 'blue', cost: { blue: 5 } },
        { points: 2, bonus: 'blue', cost: { white: 5, blue: 3 } },
        { points: 3, bonus: 'blue', cost: { blue: 6 } },

        { points: 1, bonus: 'green', cost: { white: 3, blue: 2, red: 3 } },
        { points: 1, bonus: 'green', cost: { white: 2, blue: 3, black: 2 } },
        { points: 2, bonus: 'green', cost: { white: 4, blue: 2, black: 1 } },
        { points: 2, bonus: 'green', cost: { green: 5 } },
        { points: 2, bonus: 'green', cost: { blue: 5, green: 3 } },
        { points: 3, bonus: 'green', cost: { green: 6 } },

        { points: 1, bonus: 'red', cost: { white: 2, red: 2, black: 3 } },
        { points: 1, bonus: 'red', cost: { blue: 3, red: 2, black: 3 } },
        { points: 2, bonus: 'red', cost: { black: 5 } },
        { points: 2, bonus: 'red', cost: { blue: 4, green: 2, white: 1 } },
        { points: 2, bonus: 'red', cost: { black: 5, white: 3 } },
        { points: 3, bonus: 'red', cost: { red: 6 } },

        { points: 1, bonus: 'black', cost: { white: 3, blue: 2, green: 2 } },
        { points: 1, bonus: 'black', cost: { white: 3, green: 3, black: 2 } },
        { points: 2, bonus: 'black', cost: { white: 5 } },
        { points: 2, bonus: 'black', cost: { blue: 1, green: 4, red: 2 } },
        { points: 2, bonus: 'black', cost: { green: 5, red: 3 } },
        { points: 3, bonus: 'black', cost: { black: 6 } },

    ],

    // 三阶卡池 (Level 3) - 共 20 张
    level3: [
        { points: 4, bonus: 'white', cost: { black: 7 } },
        { points: 4, bonus: 'white', cost: { white: 3, red: 3, black: 6 } },
        { points: 5, bonus: 'white', cost: { black: 7, white: 3 } },
        { points: 3, bonus: 'white', cost: { red: 5, blue: 3, green: 3, black: 3 } },

        { points: 4, bonus: 'blue', cost: { white: 7 } },
        { points: 4, bonus: 'blue', cost: { white: 6, blue: 3, black: 3 } },
        { points: 5, bonus: 'blue', cost: { white: 7, blue: 3 } },
        { points: 3, bonus: 'blue', cost: { red: 3, green: 3, white: 3, black: 5 } },

        { points: 4, bonus: 'green', cost: { blue: 7 } },
        { points: 4, bonus: 'green', cost: { white: 3, blue: 6, green: 3 } },
        { points: 5, bonus: 'green', cost: { blue: 7, green: 3 } },
        { points: 3, bonus: 'green', cost: { white: 5, red: 3, black: 3, blue: 3 } },

        { points: 4, bonus: 'red', cost: { green: 7 } },
        { points: 4, bonus: 'red', cost: { blue: 3, green: 6, red: 3 } },
        { points: 5, bonus: 'red', cost: { green: 7, red: 3 } },
        { points: 3, bonus: 'red', cost: { blue: 5, black: 3, green: 3, white: 3 } },

        { points: 4, bonus: 'black', cost: { red: 7 } },
        { points: 4, bonus: 'black', cost: { green: 3, red: 6, black: 3 } },
        { points: 5, bonus: 'black', cost: { red: 7, black: 3 } },
        { points: 3, bonus: 'black', cost: { blue: 3, white: 3, green: 5, red: 3 } }
    ],
    nobles: [
        { points: 3, cost: { red: 3, blue: 3, green: 3 } },
        { points: 3, cost: { black: 3, red: 3, green: 3 } },
        { points: 3, cost: { blue: 3, green: 3, white: 3 } },
        { points: 3, cost: { black: 3, red: 3, white: 3 } },
        { points: 3, cost: { black: 3, blue: 3, white: 3 } },
        { points: 3, cost: { white: 4, blue: 4 } },
        { points: 3, cost: { black: 4, red: 4 } },
        { points: 3, cost: { green: 4, red: 4 } },
        { points: 3, cost: { white: 4, black: 4 } },
        { points: 3, cost: { blue: 4, green: 4 } }
    ]
};
