from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    options_json = db.Column(db.Text, nullable=False)
    is_ended = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    host_session_id = db.Column(db.String(100), nullable=False)

    votes = db.relationship('Vote', backref='room_ref', lazy=True, cascade='all, delete-orphan')

    @property
    def options(self):
        return json.loads(self.options_json)

    @options.setter
    def options(self, opts):
        self.options_json = json.dumps(opts, ensure_ascii=False)

    def to_dict(self):
        return {
            'code': self.code,
            'title': self.title,
            'options': self.options,
            'is_ended': self.is_ended,
            'created_at': self.created_at.isoformat()
        }


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(6), db.ForeignKey('rooms.code'), nullable=False, index=True)
    option_index = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    voted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('room_code', 'ip_address', name='uq_room_ip'),
        db.UniqueConstraint('room_code', 'session_id', name='uq_room_session'),
    )

    def to_dict(self):
        return {
            'room_code': self.room_code,
            'option_index': self.option_index,
            'voted_at': self.voted_at.isoformat()
        }
