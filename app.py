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
games = {} 
player_map = {} 

class GameEngine:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = [] 
        self.game_started = False
        
        self.vote_active = False
        self.restart_votes = {} 

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
        self.selections = {} 

    def get_player(self, uid):
        for p in self.players:
            if p.get('uid') == uid: return p
        return None

    def add_player(self, sid, uid, name):
        existing = self.get_player(uid)
        if existing:
            existing['id'] = sid
            existing['name'] = name 
            return True 

        self.players.append({'id': sid, 'uid': uid, 'name': name, 'isReady': False})
        
        self.state['playerTokens'][uid] = {c:0 for c in ['red','green','blue','white','black','gold']}
        self.state['playerBonuses'][uid] = {c:0 for c in ['red','green','blue','white','black']}
        self.state['reservedCards'][uid] = []
        self.state['playerNobles'][uid] = []
        self.state['scores'][uid] = 0
        return False

    def remove_player(self, uid):
        pass

    def get_player_name(self, uid):
        p = self.get_player(uid)
        return p['name'] if p else "Unknown"

    def start_game(self):
        if len(self.players) < 2:
            return False
        
        # 1. 随机顺序
        random.shuffle(self.players)
        
        player_count = len(self.players)
        token_count = 4 if player_count == 2 else (5 if player_count == 3 else 7)
        for c in ['red', 'green', 'blue', 'white', 'black']:
            self.state['bank'][c] = token_count
        self.state['bank']['gold'] = 5

        for lvl in ['level1', 'level2', 'level3']:
            self.state['decks'][lvl] = random.sample(FULL_CARD_POOL[lvl], len(FULL_CARD_POOL[lvl]))
            self.state['board'][lvl] = []
            for _ in range(4):
                if self.state['decks'][lvl]:
                    self.state['board'][lvl].append(self.state['decks'][lvl].pop())

        all_nobles = random.sample(FULL_CARD_POOL['nobles'], len(FULL_CARD_POOL['nobles']))
        self.state['nobles'] = all_nobles[:player_count + 1]

        self.state['turnIndex'] = 0
        self.state['gameOver'] = False
        self.state['isLastRound'] = False
        for p in self.players:
            uid = p['uid']
            self.state['scores'][uid] = 0
            self.state['playerTokens'][uid] = {c:0 for c in ['red','green','blue','white','black','gold']}
            self.state['playerBonuses'][uid] = {c:0 for c in ['red','green','blue','white','black']}
            self.state['reservedCards'][uid] = []
            self.state['playerNobles'][uid] = []

        self.game_started = True
        return True

    def next_turn(self):
        self.state['turnIndex'] = (self.state['turnIndex'] + 1) % len(self.players)
        if self.state['turnIndex'] == 0 and self.state['isLastRound']:
            self.state['gameOver'] = True

    def check_nobles(self, uid):
        bonuses = self.state['playerBonuses'][uid]
        for i in range(len(self.state['nobles']) - 1, -1, -1):
            noble = self.state['nobles'][i]
            satisfy = True
            for color, count in noble['cost'].items():
                if bonuses.get(color, 0) < count:
                    satisfy = False
                    break
            if satisfy:
                self.state['scores'][uid] += noble['points']
                self.state['playerNobles'][uid].append(noble)
                self.state['nobles'].pop(i)
                socketio.emit('ADD_LOG', {'key': 'log_noble', 'args': [self.get_player_name(uid)]}, to=self.room_id)
                break

def broadcast_room_list():
    room_data = []
    for r_id, g in games.items():
        room_data.append({
            'id': r_id,
            'count': len(g.players),
            'status': 'Playing' if g.game_started else 'Waiting'
        })
    socketio.emit('ROOM_LIST_UPDATE', room_data)

def get_game_by_sid(sid):
    room_id = player_map.get(sid)
    if room_id and room_id in games:
        return games[room_id]
    return None

def get_uid_by_sid(sid):
    game = get_game_by_sid(sid)
    if game:
        for p in game.players:
            if p['id'] == sid: return p['uid']
    return None

@app.route('/')
def index():
    return send_from_directory(root_dir, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(root_dir, filename)

# --- Socket Events ---

@socketio.on('connect')
def handle_connect():
    broadcast_room_list()

@socketio.on('JOIN_ROOM')
def handle_join(data):
    room_id = data.get('room', 'default')
    name = data.get('name', 'Player')
    uid = data.get('uid') 

    if not uid: return

    if request.sid in player_map:
        old_room = player_map[request.sid]
        leave_room(old_room)

    join_room(room_id)
    player_map[request.sid] = room_id

    if room_id not in games:
        games[room_id] = GameEngine(room_id)
    
    game = games[room_id]
    reconnected = game.add_player(request.sid, uid, name)
    
    emit('PLAYER_LIST', game.players, to=room_id)
    if game.game_started:
        emit('GAME_START', to=request.sid)
        emit('STATE_SYNC', game.state, to=request.sid)
    
    if reconnected:
        emit('ADD_LOG', {'key': 'log_reconnect', 'args': [name]}, to=room_id)
    else:
        emit('ADD_LOG', {'key': 'log_join', 'args': [name]}, to=room_id)
    
    broadcast_room_list()

@socketio.on('LEAVE_ROOM')
def handle_leave():
    game = get_game_by_sid(request.sid)
    if game:
        uid = get_uid_by_sid(request.sid)
        if uid:
            game.players = [p for p in game.players if p['uid'] != uid]
            emit('PLAYER_LIST', game.players, to=game.room_id)
            if len(game.players) == 0:
                del games[game.room_id]
    
    if request.sid in player_map:
        del player_map[request.sid]
    
    broadcast_room_list()

@socketio.on('UPDATE_READY')
def handle_ready(is_ready):
    game = get_game_by_sid(request.sid)
    if not game: return
    for p in game.players:
        if p['id'] == request.sid:
            p['isReady'] = is_ready
            break
    emit('PLAYER_LIST', game.players, to=game.room_id)
    broadcast_room_list()

@socketio.on('REQUEST_START')
def handle_start():
    game = get_game_by_sid(request.sid)
    if not game: return
    if game.start_game():
        emit('GAME_START', to=game.room_id)
        # 修复点 1：必须在打乱顺序后再次广播玩家列表，否则前端顺序与后端不一致
        emit('PLAYER_LIST', game.players, to=game.room_id) 
        emit('STATE_SYNC', game.state, to=game.room_id)
        emit('ADD_LOG', {'key': 'log_start', 'args': []}, to=game.room_id)
        broadcast_room_list()

@socketio.on('REQUEST_RESTART_VOTE')
def handle_vote_request():
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return
    
    uid = get_uid_by_sid(request.sid)
    requester_name = game.get_player_name(uid)
    
    game.vote_active = True
    game.restart_votes = {} 
    
    game.restart_votes[uid] = True
    
    emit('VOTE_START', {'requester': requester_name}, to=game.room_id)

@socketio.on('SUBMIT_VOTE')
def handle_submit_vote(vote_val):
    game = get_game_by_sid(request.sid)
    if not game or not game.vote_active: return
    
    uid = get_uid_by_sid(request.sid)
    game.restart_votes[uid] = vote_val
    
    if len(game.restart_votes) >= len(game.players):
        all_agree = all(game.restart_votes.values())
        game.vote_active = False
        emit('VOTE_END', {'success': all_agree}, to=game.room_id)
        
        if all_agree:
            game.game_started = False
            game.state['gameOver'] = False
            for p in game.players: p['isReady'] = False
            emit('RESTART_GAME', to=game.room_id)
            emit('PLAYER_LIST', game.players, to=game.room_id)
            broadcast_room_list()
        else:
            emit('ADD_LOG', {'key': 'log_vote_fail', 'args': []}, to=game.room_id)

@socketio.on('ACTION_SELECT_CARD')
def handle_select(payload):
    game = get_game_by_sid(request.sid)
    if not game: return
    uid = get_uid_by_sid(request.sid)
    if payload:
        game.selections[uid] = payload
    else:
        if uid in game.selections:
            del game.selections[uid]
    emit('SELECTION_UPDATE', game.selections, to=game.room_id)

@socketio.on('ACTION_TAKE_TOKENS')
def handle_take(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return
    
    current_uid = game.players[game.state['turnIndex']]['uid']
    request_uid = get_uid_by_sid(request.sid)
    
    if request_uid != current_uid: return

    take = payload.get('take', [])
    discard = payload.get('discard', [])
    
    if 'gold' in take: return
    for c in take:
        if game.state['bank'][c] <= 0: return

    for c in take:
        game.state['bank'][c] -= 1
        game.state['playerTokens'][current_uid][c] += 1
    
    for c in discard:
        game.state['bank'][c] += 1
        game.state['playerTokens'][current_uid][c] -= 1

    p_name = game.get_player_name(current_uid)
    
    # 修复点 3: 日志传递原始数组，而非字符串
    emit('ADD_LOG', {'key': 'log_take', 'args': [p_name, take]}, to=game.room_id)
    
    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

@socketio.on('ACTION_BUY_CARD')
def handle_buy(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return
    
    current_uid = game.players[game.state['turnIndex']]['uid']
    request_uid = get_uid_by_sid(request.sid)
    if request_uid != current_uid: return

    level = payload['level']
    index = payload['index']
    source = payload['source']

    card = None
    if source == 'reserved':
        card = game.state['reservedCards'][current_uid][index]
    else:
        card = game.state['board'][level][index]
    
    if not card: return

    tokens = game.state['playerTokens'][current_uid]
    bonuses = game.state['playerBonuses'][current_uid]
    gold_needed = 0
    pay_back = {}

    for color, cost in card['cost'].items():
        needed = max(0, cost - bonuses.get(color, 0))
        owned = tokens.get(color, 0)
        
        if owned < needed:
            pay_back[color] = owned
            gold_needed += (needed - owned)
        else:
            pay_back[color] = needed
    
    if tokens.get('gold', 0) < gold_needed:
        return

    for c, amt in pay_back.items():
        game.state['playerTokens'][current_uid][c] -= amt
        game.state['bank'][c] += amt
    
    game.state['playerTokens'][current_uid]['gold'] -= gold_needed
    game.state['bank']['gold'] += gold_needed

    game.state['playerBonuses'][current_uid][card['bonus']] += 1
    game.state['scores'][current_uid] += card['points']

    if source == 'reserved':
        game.state['reservedCards'][current_uid].pop(index)
    else:
        if game.state['decks'][level]:
            game.state['board'][level][index] = game.state['decks'][level].pop()
        else:
            game.state['board'][level].pop(index)

    p_name = game.get_player_name(current_uid)
    # 修复点 3: 日志传递卡牌对象
    emit('ADD_LOG', {'key': 'log_buy', 'args': [p_name, card]}, to=game.room_id)
    
    game.check_nobles(current_uid)

    if game.state['scores'][current_uid] >= 15:
        game.state['isLastRound'] = True
        emit('ADD_LOG', {'key': 'log_last_round', 'args': [p_name]}, to=game.room_id)

    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

# @socketio.on('ACTION_RESERVE_CARD')
# def handle_reserve(payload):
#     game = get_game_by_sid(request.sid)
#     if not game or not game.game_started: return

#     current_uid = game.players[game.state['turnIndex']]['uid']
#     request_uid = get_uid_by_sid(request.sid)
#     if request_uid != current_uid: return

#     if len(game.state['reservedCards'][current_uid]) >= 3:
#         return

#     level = payload['level']
#     index = payload['index']
#     discard = payload.get('discard', [])

#     card = None
#     if index == -1:
#         if game.state['decks'][level]:
#             card = game.state['decks'][level].pop()
#     else:
#         card = game.state['board'][level][index]
#         if game.state['decks'][level]:
#             game.state['board'][level][index] = game.state['decks'][level].pop()
#         else:
#             game.state['board'][level].pop(index)
    
#     if card:
#         game.state['reservedCards'][current_uid].append(card)
#         if game.state['bank']['gold'] > 0:
#             game.state['bank']['gold'] -= 1
#             game.state['playerTokens'][current_uid]['gold'] += 1
    
#     for c in discard:
#         game.state['playerTokens'][current_uid][c] -= 1
#         game.state['bank'][c] += 1

#     p_name = game.get_player_name(current_uid)
#     emit('ADD_LOG', {'key': 'log_reserve', 'args': [p_name]}, to=game.room_id)
    
#     game.next_turn()
#     emit('STATE_SYNC', game.state, to=game.room_id)
    
@socketio.on('ACTION_RESERVE_CARD')
def handle_reserve(payload):
    game = get_game_by_sid(request.sid)
    if not game or not game.game_started: return

    current_uid = game.players[game.state['turnIndex']]['uid']
    if get_uid_by_sid(request.sid) != current_uid:
        return

    if len(game.state['reservedCards'][current_uid]) >= 3: 
        return

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
        game.state['reservedCards'][current_uid].append(card)
        if game.state['bank']['gold'] > 0:
            game.state['bank']['gold'] -= 1
            game.state['playerTokens'][current_uid]['gold'] += 1
    
    for c in discard:
        game.state['playerTokens'][current_uid][c] -= 1
        game.state['bank'][c] += 1

    p_name = game.get_player_name(current_uid)
    # 修改处：现在 args[1] 是 card 对象，供前端显示迷你卡牌
    emit('ADD_LOG', {'key': 'log_reserve', 'args': [p_name, card]}, to=game.room_id)
    game.next_turn()
    emit('STATE_SYNC', game.state, to=game.room_id)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True)