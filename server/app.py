#!/usr/bin/env python
from flask import request, session,jsonify,make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    
    def post(self):
        json_data = request.get_json()
        
        required_fields = ['username', 'password', 'image_url', 'bio']
        for field in required_fields:
            if field not in json_data:
                return {'error': f'Missing field: {field}'}, 422
        
        if User.query.filter_by(username=json_data['username']).first():
            return {'error': 'Username already exists'}, 422
        
        user = User(
            username=json_data['username'],
            image_url=json_data['image_url'],
            bio=json_data['bio']
        )
        
        user.password_hash = json_data['password']
        
        db.session.add(user)
        db.session.commit()
        
        response_data = {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }
        return response_data, 201
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id is not None:
            user = User.query.filter(User.id == user_id).first()
            if user is not None:
                return user.to_dict(),200
        return {'error': 'Unauthorized'}, 401

class Login(Resource):

    def post(self):
        data = request.get_json()
        username = data['username']
        user = User.query.filter(User.username == username).first()

        if user and user.authenticate(data['password']):
            session['user_id'] = user.id
            response_data = {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }
            return response_data, 200

        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if user_id is not None:
            session.pop('user_id',None)
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not session.get('user_id'):
            return {'message': 'Unauthorized access'}, 401
        
        recipes = [recipe.to_dict() for recipe in Recipe.query.filter(Recipe.user_id== user_id).all()]
        return make_response(jsonify(recipes),200)
        
        
    def post(self):
        # Check if user is logged in
        user_id = session.get('user_id')
        if user_id is None:
            return {'error': 'Unauthorized'}, 401
        
        # Get JSON data from request
        json_data = request.get_json()
        
        # Check if all required fields are present
        required_fields = ['title', 'instructions', 'minutes_to_complete',user_id]
        for field in required_fields:
            if field not in json_data:
                return {'error': f'Missing field: {field}'}, 422
        
        # Retrieve the user from the database
        user = User.query.get(user_id)
        if user is None:
            return {'error': 'User not found'}, 404
        
        # Create a new recipe
        recipe = Recipe(
            title=json_data['title'],
            instructions=json_data['instructions'],
            minutes_to_complete=json_data['minutes_to_complete'],
            user_id=user_id
        )
        
        # Add the recipe to the database
        db.session.add(recipe)
        db.session.commit()
        
        # Construct the response
        response_data = {
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }
        }
        
        return response_data, 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)