#!/usr/bin/env python3
from flask_sqlalchemy import SQLAlchemy
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_restful import Api
import os
import logging

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    app.logger.debug("GET /restaurants route accessed")
    restaurants = Restaurant.query.all()
    restaurants_data = [{"id": r.id, "name": r.name, "address": r.address} for r in restaurants]
    return jsonify(restaurants_data), 200

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    app.logger.debug(f"GET /restaurants/{id} route accessed")
    restaurant = Restaurant.query.get(id)
    if restaurant:
        restaurant_data = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [{"id": rp.id, "price": rp.price, "pizza_id": rp.pizza_id, "restaurant_id": rp.restaurant_id} for rp in restaurant.restaurant_pizzas]
        }
        return jsonify(restaurant_data), 200
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    app.logger.debug(f"DELETE /restaurants/{id} route accessed")
    restaurant = Restaurant.query.get(id)
    if restaurant:
        db.session.delete(restaurant)
        db.session.commit()
        return '', 204
    else:
        return jsonify({"error": "Restaurant not found"}), 404

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    app.logger.debug("GET /pizzas route accessed")
    pizzas = Pizza.query.all()
    pizzas_data = [{"id": p.id, "name": p.name, "ingredients": p.ingredients} for p in pizzas]
    return jsonify(pizzas_data), 200

@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    app.logger.debug("POST /restaurant_pizzas route accessed")
    data = request.get_json()
    try:
        price = data["price"]
        pizza_id = data["pizza_id"]
        restaurant_id = data["restaurant_id"]

        pizza = Pizza.query.get(pizza_id)
        restaurant = Restaurant.query.get(restaurant_id)

        if not pizza or not restaurant:
            return jsonify({"error": "Pizza or Restaurant not found"}), 404

        # Price range
        if not (1 <= price <= 30):
            return jsonify({"error": "Price must be between 1 and 30"}), 400

        # RestaurantPizza object creation
        restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(restaurant_pizza)
        db.session.commit()

        response_data = {
            "id": restaurant_pizza.id,
            "price": restaurant_pizza.price,
            "pizza_id": restaurant_pizza.pizza_id,
            "restaurant_id": restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }

        return jsonify(response_data), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except KeyError:
        return jsonify({"error": "Invalid request data"}), 400

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        db.session.rollback()
        return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    app.run(port=5555, debug=True)

