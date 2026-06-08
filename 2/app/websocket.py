from flask_socketio import SocketIO, emit, join_room, leave_room
from app.room_manager import room_manager
from app.quiz_logic import quiz_logic

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

room_connections = {}


@socketio.on('join')
def on_join(data):
    room_id = data.get('room_id')
    user_type = data.get('user_type', 'player')
    player_name = data.get('player_name', '')
    player_id = data.get('player_id', '')

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    join_room(room_id)

    if room_id not in room_connections:
        room_connections[room_id] = 0
    room_connections[room_id] += 1

    state = room_manager.get_room_state(room_id)

    emit('joined', {
        'room_id': room_id,
        'user_type': user_type,
        'player_name': player_name,
        'player_id': player_id,
        'state': state
    }, room=room_id)

    emit('player_joined', {
        'player_name': player_name,
        'player_id': player_id,
        'state': state
    }, room=room_id)

    if user_type == 'host':
        emit('host_connected', {
            'message': f'主持人 {player_name} 已加入'
        }, room=room_id)


@socketio.on('leave')
def on_leave(data):
    room_id = data.get('room_id')
    player_name = data.get('player_name', '')
    player_id = data.get('player_id', '')

    if room_id and room_manager.room_exists(room_id):
        leave_room(room_id)

        if player_id:
            room_manager.remove_player(room_id, player_id)

        if room_id in room_connections and room_connections[room_id] > 0:
            room_connections[room_id] -= 1

        state = room_manager.get_room_state(room_id)
        emit('player_left', {
            'player_name': player_name,
            'player_id': player_id,
            'state': state
        }, room=room_id)


@socketio.on('start_question')
def on_start_question(data):
    room_id = data.get('room_id')
    question = data.get('question', '')

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    result = room_manager.start_question(room_id, question)
    if result:
        state = room_manager.get_room_state(room_id)
        emit('question_started', {
            'question': question,
            'question_id': result['question_id'],
            'round': result['round'],
            'state': state
        }, room=room_id)


@socketio.on('end_question')
def on_end_question(data):
    room_id = data.get('room_id')
    correct = data.get('correct', True)

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    result = room_manager.end_question(room_id, correct)
    if result:
        state = room_manager.get_room_state(room_id)
        emit('question_ended', {
            'result': result['result'],
            'leaderboard': result['leaderboard'],
            'correct': correct,
            'state': state
        }, room=room_id)


@socketio.on('buzz')
def on_buzz(data):
    room_id = data.get('room_id')
    player_id = data.get('player_id', '')
    player_name = data.get('player_name', '')

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    room = room_manager.get_room(room_id)
    if not room or room.get('status') != 'active':
        emit('buzz_result', {
            'success': False,
            'message': '当前没有可抢答的题目',
            'player_id': player_id,
            'player_name': player_name
        })
        return

    question_id = room.get('current_question_id', '')
    if not question_id:
        emit('buzz_result', {
            'success': False,
            'message': '当前没有可抢答的题目',
            'player_id': player_id,
            'player_name': player_name
        })
        return

    result = quiz_logic.try_buzz(room_id, question_id, player_id, player_name)

    emit('buzz_result', result)

    if result.get('is_first'):
        state = room_manager.get_room_state(room_id)
        emit('buzz_winner', {
            'winner': result,
            'state': state
        }, room=room_id)


@socketio.on('get_state')
def on_get_state(data):
    room_id = data.get('room_id')

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    state = room_manager.get_room_state(room_id)
    emit('state_update', {'state': state})


@socketio.on('reset_room')
def on_reset_room(data):
    room_id = data.get('room_id')

    if not room_id or not room_manager.room_exists(room_id):
        emit('error', {'message': '房间不存在'})
        return

    room_manager.reset_room(room_id)
    state = room_manager.get_room_state(room_id)
    emit('room_reset', {'state': state}, room=room_id)


@socketio.on('chat_message')
def on_chat_message(data):
    room_id = data.get('room_id')
    player_name = data.get('player_name', '')
    message = data.get('message', '')

    if not room_id or not room_manager.room_exists(room_id):
        return

    emit('chat_message', {
        'player_name': player_name,
        'message': message
    }, room=room_id)


@socketio.on('disconnect')
def on_disconnect():
    pass


def broadcast_leaderboard(room_id):
    leaderboard = quiz_logic.get_leaderboard(room_id)
    socketio.emit('leaderboard_update', {
        'leaderboard': leaderboard
    }, room=room_id)


def broadcast_state(room_id):
    state = room_manager.get_room_state(room_id)
    if state:
        socketio.emit('state_update', {
            'state': state
        }, room=room_id)
