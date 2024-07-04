"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict()for user in users])

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if person: 
        return jsonify(person.to_dict())
    return jsonify({'message': 'person not found'}),404

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    return jsonify([person.to_dict()for person in people])

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([planet.to_dict()for planet in planets])

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet: 
        return jsonify(planet.to_dict())
    return jsonify({'message': 'planet not found'}),404

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)
    if user:
        favorites = Favorite.query.filter_by(user_id=user_id).all() 
        return jsonify([favorite.to_dict()for favorite in favorites])
    return jsonify({'message': 'planet not found'}),404


@app.route('/favorite/planets/<int:planet_id>', methods=['POST'])
def post_favorites_planet(planet_id):
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)
    planet = Planet.query.get(planet_id)
    if planet and user:
        favorite = Favorite(user_id=user_id, planet_id=planet_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify(favorite.to_dict()), 201
    return jsonify({'message':'User and PLanet not found'}),404
    

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.args.get('user_id')
    favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'message':'Favorite deleted'}),200
    return jsonify({'message':'Favorite not found'}), 404

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def post_favorites_people(people_id):
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)
    people = People.query.get(people_id)
    if people and user:
        favorite = Favorite(user_id=user_id, people_id=people_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify(favorite.to_dict()), 201
    return jsonify({'message':'User and person not found'}),404

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    user_id = request.args.get('user_id')
    favorite = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'message':'Favorite deleted'}),200
    return jsonify({'message':'Favorite not found'}), 404

# **Planet Endpoints**

# Create a new planet (POST)
@app.route('/planets', methods=['POST'])
def create_planet():
    try:
        # Get planet data from request body
        request_data = request.get_json()
        name = request_data.get('name')
        climate = request_data.get('climate')
        terrain = request_data.get('terrain')

        # Validate required fields
        if not all([name, climate, terrain]):
            return jsonify({'message': 'Missing required fields'}), 400

        # Create and save new planet
        new_planet = Planet(name=name, climate=climate, terrain=terrain)
        db.session.add(new_planet)
        db.session.commit()

        return jsonify(new_planet.to_dict()), 201  # Created
    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error
    
# Update an existing planet (PUT)
@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    try:
        # Get planet data from request body
        request_data = request.get_json()
        name = request_data.get('name')
        climate = request_data.get('climate')
        terrain = request_data.get('terrain')

        # Check if planet exists
        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({'message': 'Planet not found'}), 404  # Not Found

        # Update planet fields (if provided)
        if name:
            planet.name = name
        if climate:
            planet.climate = climate
        if terrain:
            planet.terrain = terrain
        
        db.session.commit()

        return jsonify(planet.to_dict()), 200  # OK

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error
    
# Delete a planet (DELETE)
@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    try:
        # Check if planet exists
        planet = Planet.query.get(planet_id)
        if not planet:
            return jsonify({'message': 'Planet not found'}), 404  # Not Found

        # Delete planet
        db.session.delete(planet)
        db.session.commit()

        return jsonify({'message': 'Planet deleted'}), 200  # OK

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error
    
# **People Endpoints**

# Create a new person (POST)
@app.route('/people', methods=['POST'])
def create_person():
    try:
        # Get person data from request body
        request_data = request.get_json()
        name = request_data.get('name')
        birth_year = request_data.get('birth_year')
        gender = request_data.get('gender')

        # Validate required fields
        if not all([name, birth_year, gender,]):
            return jsonify({'message': 'Missing required fields'}), 400

        # Create and save new person
        new_person = People(name=name, birth_year=birth_year, gender=gender)
        db.session.add(new_person)
        db.session.commit()

        return jsonify(new_person.to_dict()), 201  # Created

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error
    
# Update an existing person (PUT)
@app.route('/people/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    try:
        # Get person data from request body
        request_data = request.get_json()
        name = request_data.get('name')
        birth_year = request_data.get('birth_year')
        gender = request_data.get('gender')

        # Check if person exists
        person = People.query.get(person_id)
        if not person:
            return jsonify({'message': 'Person not found'}), 404  # Not Found

        # Update person fields (if provided)
        if name:
            person.name = name
        if birth_year:
            person.birth_year = birth_year
        if gender:
            person.gender = gender

        db.session.commit()

        return jsonify(person.to_dict()), 200  # OK

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error
    
# Delete a person (DELETE)
@app.route('/people/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    try:
        # Check if person exists
        person = People.query.get(person_id)
        if not person:
            return jsonify({'message': 'Person not found'}), 404  # Not Found

        # Delete person
        db.session.delete(person)
        db.session.commit()

        return jsonify({'message': 'Person deleted'}), 200  # OK

    except Exception as e:
        # Handle unexpected errors
        return jsonify({'message': str(e)}), 500  # Internal Server Error

   
# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)