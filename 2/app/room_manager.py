import uuid
import time
from app.config import Config
from app.redis_client import redis_client
from app.quiz_logic import quiz_logic


class RoomManager:
    @staticmethod
    def create_room(host_name, room_name=None):
        room_id = str(uuid.uuid4())[:6]
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"

        if not room_name:
            room_name = f"抢答房间 {room_id}"

        room_data = {
            'room_id': room_id,
            'room_name': room_name,
            'host_name': host_name,
            'status': 'waiting',
            'current_question_id': '',
            'current_question': '',
            'round': 0,
            'created_at': time.time()
        }

        redis_client.hset(room_key, mapping=room_data)
        return room_data

    @staticmethod
    def get_room(room_id):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        room_data = redis_client.hgetall(room_key)
        if not room_data:
            return None
        return room_data

    @staticmethod
    def room_exists(room_id):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        return redis_client.exists(room_key) > 0

    @staticmethod
    def add_player(room_id, player_id, player_name):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        player_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}"

        if not RoomManager.room_exists(room_id):
            return None

        redis_client.hset(room_key, mapping={
            f'player_{player_id}': player_name
        })
        redis_client.sadd(player_key, player_id)

        player_data_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}:{player_id}"
        redis_client.hset(player_data_key, mapping={
            'player_id': player_id,
            'player_name': player_name,
            'joined_at': time.time()
        })

        return {
            'player_id': player_id,
            'player_name': player_name
        }

    @staticmethod
    def remove_player(room_id, player_id):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        player_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}"
        player_data_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}:{player_id}"

        redis_client.hdel(room_key, f'player_{player_id}')
        redis_client.srem(player_key, player_id)
        redis_client.delete(player_data_key)
        return True

    @staticmethod
    def get_players(room_id):
        player_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}"
        player_ids = redis_client.smembers(player_key)
        players = []
        for player_id in player_ids:
            player_data_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}:{player_id}"
            player_data = redis_client.hgetall(player_data_key)
            if player_data:
                players.append({
                    'player_id': player_data.get('player_id', player_id),
                    'player_name': player_data.get('player_name', player_id)
                })
        return players

    @staticmethod
    def start_question(room_id, question):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"

        if not RoomManager.room_exists(room_id):
            return None

        question_id = quiz_logic.generate_question_id()
        round_num = int(redis_client.hget(room_key, 'round') or 0) + 1

        quiz_logic.clear_buzz(room_id, question_id)

        redis_client.hset(room_key, mapping={
            'status': 'active',
            'current_question_id': question_id,
            'current_question': question,
            'round': round_num
        })

        question_key = f"{Config.QUESTION_KEY_PREFIX}{room_id}:{question_id}"
        redis_client.hset(question_key, mapping={
            'question_id': question_id,
            'question': question,
            'round': round_num,
            'created_at': time.time(),
            'status': 'active'
        })

        return {
            'room_id': room_id,
            'question_id': question_id,
            'question': question,
            'round': round_num
        }

    @staticmethod
    def end_question(room_id, correct=True):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"

        if not RoomManager.room_exists(room_id):
            return None

        room_data = redis_client.hgetall(room_key)
        question_id = room_data.get('current_question_id', '')

        result = None
        if question_id:
            result = quiz_logic.get_buzz_result(room_id, question_id)

            if result and correct:
                quiz_logic.add_score(
                    room_id,
                    result['player_id'],
                    result['player_name'],
                    1
                )

            question_key = f"{Config.QUESTION_KEY_PREFIX}{room_id}:{question_id}"
            redis_client.hset(question_key, mapping={
                'status': 'ended',
                'winner_id': result['player_id'] if result else '',
                'winner_name': result['player_name'] if result else ''
            })

        redis_client.hset(room_key, mapping={
            'status': 'waiting',
            'current_question_id': '',
            'current_question': ''
        })

        leaderboard = quiz_logic.get_leaderboard(room_id)

        return {
            'result': result,
            'leaderboard': leaderboard
        }

    @staticmethod
    def reset_room(room_id):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        if not RoomManager.room_exists(room_id):
            return None

        redis_client.hset(room_key, mapping={
            'status': 'waiting',
            'current_question_id': '',
            'current_question': '',
            'round': 0
        })

        quiz_logic.reset_scores(room_id)

        return True

    @staticmethod
    def delete_room(room_id):
        room_key = f"{Config.ROOM_KEY_PREFIX}{room_id}"
        player_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}"
        score_key = f"{Config.SCORE_KEY_PREFIX}{room_id}"

        player_ids = redis_client.smembers(player_key)
        for player_id in player_ids:
            player_data_key = f"{Config.PLAYER_KEY_PREFIX}{room_id}:{player_id}"
            redis_client.delete(player_data_key)

        redis_client.delete(room_key)
        redis_client.delete(player_key)
        redis_client.delete(score_key)

        return True

    @staticmethod
    def get_room_state(room_id):
        room = RoomManager.get_room(room_id)
        if not room:
            return None

        players = RoomManager.get_players(room_id)
        leaderboard = quiz_logic.get_leaderboard(room_id)

        return {
            'room': room,
            'players': players,
            'leaderboard': leaderboard
        }


room_manager = RoomManager()
