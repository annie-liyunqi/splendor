from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import random
from game_data import FULL_CARD_POOL

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*") 

root_dir = os.path.dirname(os.path.abspath(__file__))

# --- Global Storage ---
games = {} # { "room_id": GameEngineInstance }
player_map = {} # { "socket_id": "room_id" }

class GameEngine:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = [] # [{id, name, isReady}]
        self.game_started = False
        self.state = {
            "turnIndex": 0,
            "bank": {"red":0, "green":0, "blue":0, "white":0, "black":0, "gold":0},
            "playerTokens": {},
            "playerBonuses": {},
            "reservedCards": {},
            "playerNobles": {},
            "scores": {},
            "board": {"level1": [], "level2": [], "level3": []},
            "decks": {"level1": [], "level2": [], "level3": []},
            "nobles": [],
            "gameOver": False,
            "isLastRound": False
        }
        self.selections = {} # { peerId: selection }

    def add_player(self, sid, name):
        for p in self.players:
            if p['id'] == sid:
                p['name'] = name
                return
        self.players.append({'id': sid, 'name': name, 'isReady': False})
        # Init empty state
        self.state['playerTokens'][sid] = {c:0 for c in ['red','green','blue','white','black','gold']}
        self.state['playerBonuses'][sid] = {c:0 for c in ['red','green','blue','white','black']}
        self.state['reservedCards'][sid] = []
        self.state['playerNobles'][sid] = []
        self.state['scores'][sid] = 0

    def remove_player(self, sid):
        self.players = [p for p in self.players if p['id'] != sid]
        if sid in self.selections:
            del self.selections[sid]

    def get_player_name(self, sid):
        for p in self.players:
            if p['id'] == sid: return p['name']
        return "Unknown"

    def start_game(self):
        if len(self.players) < 2:
            return False
        
        random.shuffle(self.players)
        
        # Setup Bank
        player_count = len(self.players)
        token_count = 4 if player_count == 2 else (5 if player_count == 3 else 7)
        for c in ['red', 'green', 'blue', 'white', 'black']:
            self.state['bank'][c] = token_count
        self.state['bank']['gold'] = 5

        # Setup Decks & Board
        for lvl in ['level1', 'level2', 'level3']:
            self.state['decks'][lvl] = random.sample(FULL_CARD_POOL[lvl], len(FULL_CARD_POOL[lvl]))
            self.state['board'][lvl] = []
            for _ in range(4):
                if self.state['decks'][lvl]:
                    self.state['board'][lvl].append(self.state['decks'][lvl].pop())

        # Setup Nobles
        all_nobles = random.sample(FULL_CARD_POOL['nobles'], len(FULL_CARD_POOL['nobles']))
        self.state['nobles'] = all_nobles[:player_count + 1]

        # Reset Player Vars
        self.state['turnIndex'] = 0
        self.state['gameOver'] = False
        self.state['isLastRound'] = False
        for p in self.players:
            pid = p['id']
            self.state['scores'][pid] = 0
            self.state['playerTokens'][pid] = {c:0 for c in ['red','green','blue','white','black','gold']}
            self.state['playerBonuses'][pid] = {c:0 for c in ['red','green','blue','white','black']}
            self.state['reservedCards'][pid] = []
            self.state['playerNobles'][pid] = []

        self.game_started = True
        return True

    def next_turn(self):
        self.state['turnIndex'] = (self.state['turnIndex'] + 1) % len(self.players)
        if self.state['turnIndex'] == 0 and self.state['isLastRound']:
            self.state['gameOver'] = True

    def check_nobles(self, pid):
        bonuses = self.state['playerBonuses'][pid]
        for i in range(len(self.state['nobles']) - 1, -1, -1):
            noble = self.state['nobles'][i]
            satisfy = True
            for color, count in noble['cost'].items():
                if bonuses.get(color, 0) < count:
                    satisfy = False
                    break
            if satisfy:
                self.state['scores'][pid] += noble['points']
                self.state['playerNobles'][pid].append(noble)
                self.state['nobles'].pop(i)
                socketio.emit('ADD_LOG', {'key': 'log_noble', 'args': [self.get_player_name(pid)]}, to=self.room_id)
                break

def get_game_by_sid(sid):
    room_id = player_map.get(sid)
    if room_id and room_id in games:
        return games[room_id]
    return None

@app.route('/')
def index():
    return send_from_directory(root_dir, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(root_dir, filename)

# --- Socket Events ---

@socketio.on('JOIN_ROOM')
def handle_join(data):
    room_id = data.get('room', 'default')
    name = data.get('name', 'Player')
    
    if request.sid in player_map:
        old_room = player_map[request.sid]
        leave_room(old_room)
        if old_room in games:
            games[old_room].remove_player(request.sid)
            emit('PLAYER_LIST', games[old_room].players, to=old_room)

    join_room(room_id)
    player_map[request.sid] = room_id

    if room_id not in games:
        games[room_id] = GameEngine(room_id)
    
    game = games[room_id]
    game.add_player(request.sid, name)
    
    emit('PLAYER_LIST', game.players, to=room_id)
    if game.game_started:
        emit('GAME_START', to=request.sid)
        emit('STATE_SYNC', game.state, to=request.sid)
    
    emit('ADD_LOG', {'key': 'log_join', 'args': [name]}, to=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    game = get_game_by_sid(request.sid)
    if game:
        game.remove_player(request.sid)
        emit('PLAYER_LIST', game.players, to=game.room_id)
    if request.sid in player_map:
        del player_map[request.sid]

@socketio.on('UPDATE_READY')
def handle_ready(is_ready):
    game = get_game_by_sid(request.sid)
    if not game: return
    for p in game.players:
        if p['id'] == request.sid:
            p['isReady'] = is_ready
            break
    emit('PLAYER_LIST', game.players, to=game.room_id)

@socketio.on('REQUEST_START')
def handle_start():
    game = get_game_by_sid(request.sid)
    if not game: return
    if game.start_game():
        emit('GAME_START', to=game.room_id)
        emit('STATE_SYNC', game.state, to=game.room_id)
        emit('ADD_LOG', {'key': 'log_start', 'args': []}, to=game.room_id)

@socketio.on('REQUEST_RESTART')
def handle_restart():
    game = get_game_by_sid(request.sid)
    if not game: return
    game.game_started = False
    game.state['gameOver'] = False
    for p in game.players: p['isReady'] = False
    emit('RESTART_GAME', to=game.room_id)
    emit('PLAYER_LIST', game.players, to=game.room_id)

@socketio.on('ACTION_SELECT_CARD')
def handle_select(payload):
    game = get_game_by_sid(request.sid)
    if not game: return
    if payload:
        game.selections[request.sid] = payload
    else:
        if request.sid in game.selections:
            del game.selections[request.sid]
    emit('SELECTION_UPDATE', game.selections, to=game.room_id)

@socketio.on('ACTION_TAKE_TOKENS')
def handle_take(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return
    
    current_pid = game.players[game.state['turnIndex']]['id']
    if request.sid != current_pid: return

    take = payload.get('take', [])
    discard = payload.get('discard', [])
    
    # 简单的服务端验证（防止直接发包攻击）
    # 1. 验证是否拿了黄金
    if 'gold' in take: return
    # 2. 验证银行是否有足够宝石
    for c in take:
        if game.state['bank'][c] <= 0: return

    for c in take:
        game.state['bank'][c] -= 1
        game.state['playerTokens'][current_pid][c] += 1
    
    for c in discard:
        game.state['bank'][c] += 1
        game.state['playerTokens'][current_pid][c] -= 1

    p_name = game.get_player_name(current_pid)
    emit('ADD_LOG', {'key': 'log_take', 'args': [p_name, ','.join(take)]}, to=game.room_id)
    
    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

@socketio.on('ACTION_BUY_CARD')
def handle_buy(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return
    
    current_pid = game.players[game.state['turnIndex']]['id']
    if request.sid != current_pid: return

    level = payload['level']
    index = payload['index']
    source = payload['source']

    card = None
    if source == 'reserved':
        card = game.state['reservedCards'][current_pid][index]
    else:
        card = game.state['board'][level][index]
    
    if not card: return

    tokens = game.state['playerTokens'][current_pid]
    bonuses = game.state['playerBonuses'][current_pid]
    gold_needed = 0
    pay_back = {}

    # 1. 计算需要支付多少实体宝石和黄金
    for color, cost in card['cost'].items():
        # 实际需要支付 = 费用 - 永久卡加成
        needed = max(0, cost - bonuses.get(color, 0))
        
        # 拥有的实体宝石
        owned = tokens.get(color, 0)
        
        if owned < needed:
            # 宝石不够，全部支付，差额用黄金补
            pay_back[color] = owned
            gold_needed += (needed - owned)
        else:
            # 宝石够，只支付需要的
            pay_back[color] = needed
    
    # 2. 【关键修复】检查玩家是否有足够的黄金支付差额
    if tokens.get('gold', 0) < gold_needed:
        # 可选：发送一个仅对自己可见的错误日志
        # emit('ADD_LOG', {'key': 'log_error', 'args': ['Not enough tokens!']}, to=request.sid)
        print(f"Purchase failed: Needs {gold_needed} gold, has {tokens.get('gold', 0)}")
        return

    # 3. 执行支付
    for c, amt in pay_back.items():
        game.state['playerTokens'][current_pid][c] -= amt
        game.state['bank'][c] += amt
    
    game.state['playerTokens'][current_pid]['gold'] -= gold_needed
    game.state['bank']['gold'] += gold_needed

    # 4. 获得卡牌
    game.state['playerBonuses'][current_pid][card['bonus']] += 1
    game.state['scores'][current_pid] += card['points']

    # 5. 移除卡牌
    if source == 'reserved':
        game.state['reservedCards'][current_pid].pop(index)
    else:
        if game.state['decks'][level]:
            game.state['board'][level][index] = game.state['decks'][level].pop()
        else:
            game.state['board'][level].pop(index)

    p_name = game.get_player_name(current_pid)
    emit('ADD_LOG', {'key': 'log_buy', 'args': [p_name, card['points']]}, to=game.room_id)
    
    game.check_nobles(current_pid)

    if game.state['scores'][current_pid] >= 15:
        game.state['isLastRound'] = True
        emit('ADD_LOG', {'key': 'log_last_round', 'args': [p_name]}, to=game.room_id)

    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

@socketio.on('ACTION_RESERVE_CARD')
def handle_reserve(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return

    current_pid = game.players[game.state['turnIndex']]['id']
    if request.sid != current_pid: return

    level = payload['level']
    index = payload['index']
    discard = payload.get('discard', [])

    card = None
    if index == -1:
        if game.state['decks'][level]:
            card = game.state['decks'][level].pop()
    else:
        card = game.state['board'][level][index]
        if game.state['decks'][level]:
            game.state['board'][level][index] = game.state['decks'][level].pop()
        else:
            game.state['board'][level].pop(index)
    
    if card:
        game.state['reservedCards'][current_pid].append(card)
        if game.state['bank']['gold'] > 0:
            game.state['bank']['gold'] -= 1
            game.state['playerTokens'][current_pid]['gold'] += 1
    
    for c in discard:
        game.state['playerTokens'][current_pid][c] -= 1
        game.state['bank'][c] += 1

    p_name = game.get_player_name(current_pid)
    emit('ADD_LOG', {'key': 'log_reserve', 'args': [p_name]}, to=game.room_id)
    
    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True)