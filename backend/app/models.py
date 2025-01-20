from app import db

class SurfSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    direction = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.String(100), nullable=False)
    longitude = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
