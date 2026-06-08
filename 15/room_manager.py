import random
import string
from typing import Optional, List, Dict
from models import db, Room, Vote


def generate_room_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not Room.query.filter_by(code=code).first():
            return code


def create_room(title: str, options: List[str], host_session_id: str) -> Room:
    code = generate_room_code()
    room = Room(
        code=code,
        title=title,
        options=options,
        host_session_id=host_session_id
    )
    db.session.add(room)
    db.session.commit()
    return room


def get_room(code: str) -> Optional[Room]:
    return Room.query.filter_by(code=code.upper()).first()


def end_room(code: str) -> Optional[Room]:
    room = get_room(code)
    if room:
        room.is_ended = True
        db.session.commit()
    return room


def has_voted(room_code: str, ip_address: str, session_id: str) -> bool:
    return Vote.query.filter(
        Vote.room_code == room_code,
        ((Vote.ip_address == ip_address) | (Vote.session_id == session_id))
    ).first() is not None


def cast_vote(room_code: str, option_index: int, ip_address: str, session_id: str) -> Optional[Vote]:
    room = get_room(room_code)
    if not room or room.is_ended:
        return None
    if option_index < 0 or option_index >= len(room.options):
        return None
    if has_voted(room_code, ip_address, session_id):
        return None

    vote = Vote(
        room_code=room_code,
        option_index=option_index,
        ip_address=ip_address,
        session_id=session_id
    )
    db.session.add(vote)
    db.session.commit()
    return vote


def get_vote_results(room_code: str) -> Dict:
    room = get_room(room_code)
    if not room:
        return {}

    options = room.options
    counts = [0] * len(options)
    total = 0

    votes = Vote.query.filter_by(room_code=room_code).all()
    for vote in votes:
        if 0 <= vote.option_index < len(counts):
            counts[vote.option_index] += 1
            total += 1

    percentages = []
    for c in counts:
        if total > 0:
            percentages.append(round(c / total * 100, 1))
        else:
            percentages.append(0.0)

    return {
        'room_code': room_code,
        'title': room.title,
        'options': options,
        'counts': counts,
        'percentages': percentages,
        'total': total,
        'is_ended': room.is_ended
    }
