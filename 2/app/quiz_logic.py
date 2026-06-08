import time
import uuid
from app.config import Config
from app.redis_client import redis_client


class QuizLogic:
    @staticmethod
    def create_buzz_lock(room_id, question_id):
        buzz_key = f"{Config.BUZZ_KEY_PREFIX}{room_id}:{question_id}"
        lock_key = f"{Config.LOCK_KEY_PREFIX}{room_id}:{question_id}"
        redis_client.delete(buzz_key)
        redis_client.delete(lock_key)
        return True

    @staticmethod
    def try_buzz(room_id, question_id, player_id, player_name):
        buzz_key = f"{Config.BUZZ_KEY_PREFIX}{room_id}:{question_id}"

        player_data = f"{player_id}:{player_name}:{time.time()}"

        result = redis_client.setnx(buzz_key, player_data, ex=Config.BUZZ_TIMEOUT)

        if result:
            return {
                'success': True,
                'player_id': player_id,
                'player_name': player_name,
                'timestamp': time.time(),
                'is_first': True
            }

        existing = redis_client.get(buzz_key)
        if existing:
            parts = existing.split(':')
            first_player_id = parts[0]
            first_player_name = parts[1]
            first_timestamp = float(parts[2])

            return {
                'success': False,
                'player_id': player_id,
                'player_name': player_name,
                'first_player_id': first_player_id,
                'first_player_name': first_player_name,
                'first_timestamp': first_timestamp,
                'timestamp': time.time(),
                'is_first': False
            }

        return {
            'success': False,
            'player_id': player_id,
            'player_name': player_name,
            'is_first': False
        }

    @staticmethod
    def get_buzz_result(room_id, question_id):
        buzz_key = f"{Config.BUZZ_KEY_PREFIX}{room_id}:{question_id}"
        existing = redis_client.get(buzz_key)
        if existing:
            parts = existing.split(':')
            return {
                'player_id': parts[0],
                'player_name': parts[1],
                'timestamp': float(parts[2])
            }
        return None

    @staticmethod
    def add_score(room_id, player_id, player_name, points=1):
        score_key = f"{Config.SCORE_KEY_PREFIX}{room_id}"
        member = f"{player_id}:{player_name}"
        redis_client.zincrby(score_key, points, member)
        return QuizLogic.get_leaderboard(room_id)

    @staticmethod
    def get_leaderboard(room_id):
        score_key = f"{Config.SCORE_KEY_PREFIX}{room_id}"
        results = redis_client.zrange(score_key, 0, -1, desc=True, withscores=True)

        leaderboard = []
        for rank, (member, score) in enumerate(results, start=1):
            parts = member.split(':')
            player_id = parts[0]
            player_name = parts[1] if len(parts) > 1 else parts[0]
            leaderboard.append({
                'rank': rank,
                'player_id': player_id,
                'player_name': player_name,
                'score': int(score)
            })
        return leaderboard

    @staticmethod
    def reset_scores(room_id):
        score_key = f"{Config.SCORE_KEY_PREFIX}{room_id}"
        redis_client.delete(score_key)
        return True

    @staticmethod
    def clear_buzz(room_id, question_id):
        buzz_key = f"{Config.BUZZ_KEY_PREFIX}{room_id}:{question_id}"
        lock_key = f"{Config.LOCK_KEY_PREFIX}{room_id}:{question_id}"
        redis_client.delete(buzz_key)
        redis_client.delete(lock_key)
        return True

    @staticmethod
    def generate_question_id():
        return str(uuid.uuid4())[:8]


quiz_logic = QuizLogic()
