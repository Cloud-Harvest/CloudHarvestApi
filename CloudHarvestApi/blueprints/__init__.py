"""
This file loads all the blueprints for the application. Each blueprint is a collection of routes that are related to a
specific part of the application. For example, the `users` blueprint contains routes that are related to users, such as
listing users or looking up a user by token.
"""

from .agents import agents_blueprint
from .home import home_blueprint
from .silos import silos_blueprint
from .tasks import tasks_blueprint
from .users import users_blueprint
