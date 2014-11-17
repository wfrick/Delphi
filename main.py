#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import datetime
import webapp2
import re
import jinja2
import json
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from webapp2_extras import sessions

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

def characters(headline):
	return "-".join(re.findall("[a-zA-Z]+", headline))

class Game(db.Model):
	name = db.StringProperty(required = True)
	rounds = db.IntegerProperty(required = True)
	players = db.IntegerProperty(required = True)
	path = db.StringProperty(required = True)

class Result(db.Model):
	#path is the unique identifier tying it to a Game
	path = db.StringProperty(required = True)
	round_number = db.IntegerProperty(required = True)
	forecast = db.FloatProperty(required = True)
	justification = db.TextProperty(required = True)


class MainHandler(webapp2.RequestHandler):
    def get(self):
    	newlink_template = jinja_env.get_template('helloworld.html')
    	self.response.write(newlink_template.render())
    def post(self):
		name = self.request.get('name')
		rounds = self.request.get('rounds')
		players = self.request.get('players')
		path = characters(str(name)).lower()
		game = Game(name = name, rounds = int(rounds), players = int(players), 
			path = path)
		game.put()
		path1 = path + "/1"
		self.redirect(path1)

class GamePage(webapp2.RequestHandler):
	def get(self, path, round):
		newlink_template = jinja_env.get_template('delphi.html')
		qry = db.Query(Game)
		qry.filter("path =", path)
		current_game = qry[0]
		template_variables = {'current_game' : current_game, 'round' : round}
		self.response.write(newlink_template.render(template_variables))

	def post(self, path, round):
		forecast = self.request.get('forecast')
		justification = self.request.get('justification')
		qry = db.Query(Game)
		qry.filter("path =", path)
		current_game = qry[0]
		result = Result(path = str(path), forecast = float(forecast), 
			justification = str(justification), round_number = int(round))
		result.put()
		results_path = '/' + path + '/' + str(round) + '/results'
		self.redirect(results_path)

class ResultPage(webapp2.RequestHandler):
	def get(self, path, round, tk):
		newlink_template = jinja_env.get_template('results.html')
		qry = db.Query(Game)
		qry.filter("path =", path)
		current_game = qry[0]
		if current_game.rounds <= int(round):
			final_path = "/" + path + "/final"
			self.redirect(final_path)
		else:
			qry2 = db.Query(Result)
			results = qry2.filter("path =", path)
			results = results.filter("round_number =", int(round))
			number_of_results = results.count()
			next_round = int(round) + 1
			template_variables = {'current_game' : current_game, 'round' : round, 
			'results' : results, 'number_of_results' : number_of_results, 'path' : path,
			'next_round' : next_round}
			self.response.write(newlink_template.render(template_variables))
	def post(self, path, round, tk):
		self.response.out.write('sorry. you have reached this page in error.')

class FinalPage(webapp2.RequestHandler):
	def get(self, path):
		newlink_template = jinja_env.get_template('final.html')
		qry = db.Query(Game)
		qry.filter("path =", path)
		current_game = qry[0]
		qry2 = db.Query(Result)
		results = qry2.filter("path =", path)
		results = results.filter("round_number =", current_game.rounds)
		result_sum = 0
		count = 1
		for a in results:
			result_sum = result_sum + a.forecast
			count = count + 1
		average_forecast = result_sum / (count - 1)
		template_variables = {'current_game' : current_game, 
		'average_forecast' : average_forecast,}
		self.response.write(newlink_template.render(template_variables))


app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/([0-9a-zA-Z_\-]+)/([0-9])', GamePage),
    ('/([0-9a-zA-Z_\-]+)/([0-9])/([0-9a-zA-Z_\-]+)', ResultPage),
    ('/([0-9a-zA-Z_\-]+)/final', FinalPage)
], debug=True)
