from datetime import datetime
from app import db

class Token(db.Model):
    """Token model for API authentication"""
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), index=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='tokens')
    
    def __repr__(self):
        return f'<Token {self.token[:8]}... - User {self.user_id}>'
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at 