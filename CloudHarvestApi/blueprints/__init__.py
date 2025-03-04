"""
This file loads all the blueprints for the application. Each blueprint is a collection of routes that are related to a
specific part of the application. For example, the `users` blueprint contains routes that are related to users, such as
listing users or looking up a user by token.
"""

from CloudHarvestApi.blueprints.agents import agents_blueprint
from CloudHarvestApi.blueprints.home import home_blueprint
from CloudHarvestApi.blueprints.plugins import plugins_blueprint
from CloudHarvestApi.blueprints.silos import silos_blueprint
from CloudHarvestApi.blueprints.tasks import tasks_blueprint
from CloudHarvestApi.blueprints.users import users_blueprint
