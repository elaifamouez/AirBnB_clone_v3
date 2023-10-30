#!/usr/bin/python3
'''This module Retrieves the list of all place objects,
deletes, updates, creates and gets information of a place '''
from flask import jsonify, request, abort
from models import storage
from models.place import Place
from models.city import City
from models.state import State
from api.v1.views import app_views


@app_views.route('/cities/<city_id>/places', strict_slashes=False)
def get_all_place(city_id):
    ''' retreive all place associated with the city id '''
    city_objs = storage.all('City')
    key = 'City.{}'.format(city_id)

    if key in city_objs:
        city = city_objs.get(key)
        return jsonify([obj.to_dict() for obj in city.places])

    abort(404)


@app_views.route('/places/<place_id>/', strict_slashes=False)
def get_a_place(place_id):
    '''return the place with matching id'''
    place_objs = storage.all('Place')
    key = 'Place.{}'.format(place_id)

    if key in place_objs:
        place = place_objs.get(key)
        return jsonify(place.to_dict())

    abort(404)


@app_views.route('/places/<place_id>/', methods=['DELETE'],
                 strict_slashes=False)
def delete_place(place_id):
    ''' delete place matching the id'''
    place_objs = storage.all('Place')
    key = 'Place.{}'.format(place_id)

    if key in place_objs:
        obj = place_objs.get(key)
        storage.delete(obj)
        storage.save()
        return jsonify({}), 200

    abort(404)


@app_views.route('/cities/<city_id>/places/', methods=['POST'],
                 strict_slashes=False)
def create_place(city_id):
    ''' create a place '''

    data = request.get_json()
    city_objs = storage.all('City')
    key = 'City.{}'.format(city_id)

    if key not in city_objs:
        abort(404)
    if data is None:
        abort(400, "Not a JSON")
    if data.get('user_id') is None:
        abort(400, "Missing user_id")

    user_objs = storage.all('User')
    user_id = data.get('user_id')
    if 'User.{}'.format(user_id) not in user_objs:
        abort(404)
    if data.get('name') is None:
        abort(400, "Missing name")

    data["city_id"] = city_id
    place_obj = Place(**data)
    place_obj.save()
    return jsonify(place_obj.to_dict()), 201


@app_views.route('/places/<place_id>', methods=['PUT'],
                 strict_slashes=False)
def update_place(place_id):
    ''' update place  whose id is passed'''

    data = request.get_json()
    place_objs = storage.all('Place')
    key = 'Place.{}'.format(place_id)

    if key not in place_objs:
        abort(404)

    if data is None:
        abort(400, "Not a JSON")

    place = place_objs.get(key)
    for k, v in data.items():
        setattr(place, k, v)
    place.save()
    return jsonify(place.to_dict()), 200


@app_views.route('/places_search', methods=['POST'])
def places_search_enhanced():
    """endpoint to retrieves all PlaceObj using passed JSON"""
    abortMSG = "Not a JSON"
    if request.get_json() is None:
        abort(400, description=abortMSG)
    data = request.get_json()
    if data and len(data):
        states = data.get('states', None)
        cities = data.get('cities', None)
        amenities = data.get('amenities', None)
    if not data or not len(data) or (
            not states and
            not cities and
            not amenities):
        places = storage.all(Place).values()
        placesList = []
        placesList = [place.to_dict() for place in places]
        res = json.dumps(placesList)
        response = make_response(res, 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    placesList = []
    if states:
        statesObj = [storage.get(State, s_id) for s_id in states]
        for state in statesObj:
            if state:
                for city in state.cities:
                    if city:
                        placesList.extend(place for place in city.places)
    if cities:
        city_obj = [storage.get(City, c_id) for c_id in cities]
        for city in city_obj:
            if city:
                for place in city.places:
                    if place not in placesList:
                        placesList.append(place)
    if amenities:
        if not placesList:
            placesList = storage.all(Place).values()
        amenities_obj = [storage.get(Amenity, a_id) for a_id in amenities]
        placesList = [place for place in placesList
                      if all([am in place.amenities
                             for am in amenities_obj])]
    places = []
    for aPlace in placesList:
        filtered = aPlace.to_dict()
        filtered.pop('amenities', None)
        places.append(filtered)
    res = json.dumps(places)
    response = make_response(res, 200)
    response.headers['Content-Type'] = 'application/json'
    return response
