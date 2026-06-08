from flask import Blueprint, request, jsonify, render_template
import uuid
from app.room_manager import room_manager
from app.quiz_logic import quiz_logic

api_bp = Blueprint('api', __name__)


@api_bp.route('/')
def index():
    return render_template('index.html')


@api_bp.route('/host/<room_id>')
def host_page(room_id):
    return render_template('host.html', room_id=room_id)


@api_bp.route('/player/<room_id>')
def player_page(room_id):
    return render_template('player.html', room_id=room_id)


@api_bp.route('/api/room', methods=['POST'])
def create_room():
    data = request.get_json()
    host_name = data.get('host_name', '主持人')
    room_name = data.get('room_name')

    room = room_manager.create_room(host_name, room_name)
    return jsonify({
        'success': True,
        'data': room
    })


@api_bp.route('/api/room/<room_id>', methods=['GET'])
def get_room(room_id):
    room = room_manager.get_room(room_id)
    if not room:
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    state = room_manager.get_room_state(room_id)
    return jsonify({
        'success': True,
        'data': state
    })


@api_bp.route('/api/room/<room_id>/join', methods=['POST'])
def join_room(room_id):
    data = request.get_json()
    player_name = data.get('player_name', '')

    if not player_name:
        return jsonify({
            'success': False,
            'message': '请输入玩家昵称'
        }), 400

    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    player_id = str(uuid.uuid4())[:8]
    player = room_manager.add_player(room_id, player_id, player_name)

    return jsonify({
        'success': True,
        'data': player
    })


@api_bp.route('/api/room/<room_id>/players', methods=['GET'])
def get_players(room_id):
    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    players = room_manager.get_players(room_id)
    return jsonify({
        'success': True,
        'data': players
    })


@api_bp.route('/api/room/<room_id>/question', methods=['POST'])
def start_question(room_id):
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({
            'success': False,
            'message': '请输入题目'
        }), 400

    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    result = room_manager.start_question(room_id, question)
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/api/room/<room_id>/question/end', methods=['POST'])
def end_question(room_id):
    data = request.get_json() or {}
    correct = data.get('correct', True)

    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    result = room_manager.end_question(room_id, correct)
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/api/room/<room_id>/buzz', methods=['POST'])
def buzz(room_id):
    data = request.get_json()
    player_id = data.get('player_id', '')
    player_name = data.get('player_name', '')

    if not player_id or not player_name:
        return jsonify({
            'success': False,
            'message': '缺少玩家信息'
        }), 400

    room = room_manager.get_room(room_id)
    if not room:
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    if room.get('status') != 'active':
        return jsonify({
            'success': False,
            'message': '当前没有可抢答的题目'
        }), 400

    question_id = room.get('current_question_id', '')
    if not question_id:
        return jsonify({
            'success': False,
            'message': '当前没有可抢答的题目'
        }), 400

    result = quiz_logic.try_buzz(room_id, question_id, player_id, player_name)
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/api/room/<room_id>/buzz/result', methods=['GET'])
def get_buzz_result(room_id):
    room = room_manager.get_room(room_id)
    if not room:
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    question_id = room.get('current_question_id', '')
    if not question_id:
        return jsonify({
            'success': True,
            'data': None
        })

    result = quiz_logic.get_buzz_result(room_id, question_id)
    return jsonify({
        'success': True,
        'data': result
    })


@api_bp.route('/api/room/<room_id>/leaderboard', methods=['GET'])
def get_leaderboard(room_id):
    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    leaderboard = quiz_logic.get_leaderboard(room_id)
    return jsonify({
        'success': True,
        'data': leaderboard
    })


@api_bp.route('/api/room/<room_id>/reset', methods=['POST'])
def reset_room(room_id):
    if not room_manager.room_exists(room_id):
        return jsonify({
            'success': False,
            'message': '房间不存在'
        }), 404

    room_manager.reset_room(room_id)
    return jsonify({
        'success': True,
        'message': '房间已重置'
    })
