# from crypt import methods
import os
import sys
import ssl
import re
from flask import Flask, request, jsonify, abort
from sqlalchemy import desc, exc, func
import json
from flask_cors import CORS
import werkzeug

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def retrieve_drinks():
    try:
        # Fetch all drinks in the long format and return them
        drinks_query = Drink.query.order_by('id').all()

        if len(drinks_query) == 0:
            raise werkzeug.exceptions.NotFound

        data = [drink.short() for drink in drinks_query]

        # Parse response data in the expected json format
        return jsonify({
            'success': True,
            'drinks': data
        })
    except werkzeug.exceptions.NotFound:
            print(sys.exc_info())
            abort(404)
    except:
        print(sys.exc_info())
        abort(500)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drinks}
        where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def retrieve_drinks_details():
    try:
        # Fetch all drinks in the long format and return them
        drinks_query = Drink.query.order_by('id').all()

        if len(drinks_query) == 0:
            raise werkzeug.exceptions.NotFound

        data = [drink.long() for drink in drinks_query]
        # print(data)
        # Parse response data in the expected json format
        return jsonify({
            'success': True,
            'drinks': data
        })
    except werkzeug.exceptions.NotFound:
            print(sys.exc_info())
            abort(404)
    except:
        print(sys.exc_info())
        abort(500)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks():
    try:
        body = request.get_json()
        new_title = body.get('title', None)
        new_recipe = body.get('recipe', None)

        # Validating data on the payload
        if (new_title and new_recipe) is None:
            raise werkzeug.exceptions.BadRequest
        elif len(new_recipe) == 1:
            if len(new_recipe[0]) < 3:
                raise werkzeug.exceptions.BadRequest
        elif len(new_recipe) > 1:
            for rec in new_recipe:
                if len(rec) < 3:
                    raise werkzeug.exceptions.BadRequest

        json_rec = json.dumps(new_recipe)
        # print(json_rec)

        # Persist record to the database
        add_drinks = Drink(
            title=new_title,
            recipe=json_rec
        )
        add_drinks.insert()
        # print(add_drinks)

        data = add_drinks.long()
        # print(data)
        return jsonify({
            "success": True,
            "drinks": data
        })
    except werkzeug.exceptions.BadRequest:
        print(sys.exc_info())
        abort(400)
    except:
        print(sys.exc_info())
        abort(500)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
        returns status code 200 and json {"success": True, "drinks": drink}
        where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def modify_drinks(id):
    try:
        # check if drink with id exists on the database
        drinks_query = Drink.query.filter(Drink.id == id).one_or_none()
        if drinks_query is None:
            raise werkzeug.exceptions.NotFound

        # Extract dat from the json object
        body = request.get_json()
        update_title = body.get('title', None)
        update_recipe = body.get('recipe', None)

        # Validating data on the payload
        if update_recipe is not None:
            if len(update_recipe) == 1:
                if len(update_recipe[0]) < 3:
                    raise werkzeug.exceptions.BadRequest
            else:
                for rec in update_recipe:
                    if len(rec) < 3:
                        raise werkzeug.exceptions.BadRequest

            # Convert list to json object
            json_rec = json.dumps(update_recipe)
            print(type(json_rec))
            # print(json_rec)

            drinks_query.recipe = json_rec

        if update_title is not None:
            drinks_query.title = update_title

        if update_title is None and update_recipe is None:
            raise werkzeug.exceptions.BadRequest

        # Persist changes to the database
        drinks_query.update()

        data = [drinks_query.long()]

        return jsonify({
            "success": True,
            "drinks": data
        })
    except werkzeug.exceptions.BadRequest:
        print(sys.exc_info())
        abort(400)
    except werkzeug.exceptions.NotFound:
        print(sys.exc_info())
        abort(404)
    except:
        print(sys.exc_info())
        abort(500)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
        returns status code 200 and json {"success": True, "delete": id}
        where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    try:
        # check if drink with id exists on the database
        del_query = Drink.query.filter(Drink.id == id).one_or_none()
        if del_query is None:
            raise werkzeug.exceptions.NotFound

        # Persist delete to the database
        del_query.delete()

        return jsonify({
            "success": True,
            "delete": id
        })

    except werkzeug.exceptions.NotFound:
        print(sys.exc_info())
        abort(404)
    except:
        print(sys.exc_info())
        abort(500)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
    jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
        }), 404
'''
"""
This session handles all error to JSON format.
"""


@app.errorhandler(401)
def unauthorize_error(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': "You do not possess the required access"
    }), 401


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': "Forbidden: Access denied"
    }), 403


@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': "The request was invalid"
    }), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': "Server Error has occured"
    }), 500


@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': "Request Method not Allowed"
    }), 405

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': "The request is not found"
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def authorization_header_missing(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), 401
