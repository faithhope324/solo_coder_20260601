import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db
from room_manager import (
    create_room, get_room, end_room,
    cast_vote, get_vote_results, has_voted
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vote-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "votes.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

room_connections = {}

with app.app_context():
    db.create_all()


def get_or_create_session_id():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return session['sid']


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def update_participant_count(room_code):
    count = room_connections.get(room_code, 0)
    socketio.emit('participant_count', {'count': count}, room=room_code)


@app.route('/')
def index():
    return render_template('create.html')


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        title = (data.get('title') or '').strip()
        options_raw = (data.get('options') or '').strip()

        if not title:
            return jsonify({'success': False, 'error': '请输入投票标题'}), 400
        if not options_raw:
            return jsonify({'success': False, 'error': '请输入投票选项'}), 400

        options = [opt.strip() for opt in options_raw.split(',') if opt.strip()]
        if len(options) < 2:
            return jsonify({'success': False, 'error': '至少需要2个选项'}), 400
        if len(options) > 10:
            return jsonify({'success': False, 'error': '最多支持10个选项'}), 400

        host_sid = get_or_create_session_id()
        room = create_room(title, options, host_sid)
        return jsonify({'success': True, 'room_code': room.code})

    return render_template('create.html')


@app.route('/join/<room_code>')
def join(room_code):
    room_code = room_code.upper().strip()
    room = get_room(room_code)
    if not room:
        return render_template('error.html', message='房间不存在'), 404

    get_or_create_session_id()
    return render_template('join.html', room_code=room_code)


@app.route('/host/<room_code>')
def host(room_code):
    room_code = room_code.upper().strip()
    room = get_room(room_code)
    if not room:
        return render_template('error.html', message='房间不存在'), 404

    host_sid = get_or_create_session_id()
    if room.host_session_id != host_sid:
        return render_template('error.html', message='无权限访问主持人页面'), 403

    return render_template('host.html', room_code=room_code)


@app.route('/api/room/<room_code>')
def api_room(room_code):
    room = get_room(room_code)
    if not room:
        return jsonify({'success': False, 'error': '房间不存在'}), 404
    result = get_vote_results(room_code)
    sid = get_or_create_session_id()
    ip = get_client_ip()
    already_voted = has_voted(room_code, ip, sid)
    result['already_voted'] = already_voted
    result['is_host'] = (room.host_session_id == sid)
    return jsonify({'success': True, 'data': result})


@socketio.on('join_room')
def on_join_room(data):
    room_code = (data.get('room_code') or '').upper().strip()
    room = get_room(room_code)
    if not room:
        emit('error', {'message': '房间不存在'})
        return

    join_room(room_code)
    room_connections[room_code] = room_connections.get(room_code, 0) + 1
    update_participant_count(room_code)

    result = get_vote_results(room_code)
    emit('vote_results', result)


@socketio.on('leave_room')
def on_leave_room(data):
    room_code = (data.get('room_code') or '').upper().strip()
    leave_room(room_code)
    if room_code in room_connections and room_connections[room_code] > 0:
        room_connections[room_code] -= 1
    update_participant_count(room_code)


@socketio.on('cast_vote')
def on_cast_vote(data):
    room_code = (data.get('room_code') or '').upper().strip()
    option_index = data.get('option_index')
    room = get_room(room_code)

    if not room:
        emit('vote_error', {'message': '房间不存在'})
        return
    if room.is_ended:
        emit('vote_error', {'message': '投票已结束'})
        return

    if option_index is None or not isinstance(option_index, int):
        emit('vote_error', {'message': '无效的选项'})
        return

    ip = request.remote_addr or 'unknown'
    sid = session.get('sid', request.sid)

    if has_voted(room_code, ip, sid):
        emit('vote_error', {'message': '您已经投过票了'})
        return

    vote = cast_vote(room_code, option_index, ip, sid)
    if not vote:
        emit('vote_error', {'message': '投票失败'})
        return

    emit('vote_success', {'option_index': option_index})
    result = get_vote_results(room_code)
    socketio.emit('vote_results', result, room=room_code)


@socketio.on('end_vote')
def on_end_vote(data):
    room_code = (data.get('room_code') or '').upper().strip()
    room = get_room(room_code)
    if not room:
        emit('error', {'message': '房间不存在'})
        return

    host_sid = session.get('sid')
    if room.host_session_id != host_sid:
        emit('error', {'message': '无权限结束投票'})
        return

    end_room(room_code)
    result = get_vote_results(room_code)
    socketio.emit('vote_ended', result, room=room_code)
    socketio.emit('vote_results', result, room=room_code)


@socketio.on('disconnect')
def on_disconnect():
    for room_code in list(room_connections.keys()):
        if room_connections[room_code] > 0:
            room_connections[room_code] -= 1
            update_participant_count(room_code)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
