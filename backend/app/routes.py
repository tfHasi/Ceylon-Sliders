from flask import Blueprint, jsonify, request
from app.models import SurfSpot
from app import db
import math

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return jsonify({"message": "Welcome to the Surf App Backend!"})

# Haversine formula to calculate distance between two lat-lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return distance

# Route to find the closest surf spot
@bp.route("/closest-surf-spot", methods=["GET"])
def closest_surf_spot():
    # Get current location of user from query parameters
    user_lat = request.args.get("latitude", type=float)
    user_lon = request.args.get("longitude", type=float)

    if user_lat is None or user_lon is None:
        return jsonify({"error": "Please provide latitude and longitude"}), 400

    # Fetch all surf spots from the database
    surf_spots = SurfSpot.query.all()

    closest_spot = None
    min_distance = float("inf")  # Start with a very large value for distance

    # Calculate the distance to each surf spot using the Haversine formula
    for spot in surf_spots:
        # Latitude and longitude are stored as separate columns in the database
        distance = haversine(user_lat, user_lon, float(spot.latitude), float(spot.longitude))

        if distance < min_distance:
            min_distance = distance
            closest_spot = spot

    if closest_spot:
        return jsonify({
            "name": closest_spot.name,
            "latitude": closest_spot.latitude,
            "longitude": closest_spot.longitude,
            "distance_km": min_distance
        })
    else:
        return jsonify({"error": "No surf spots found"}), 404