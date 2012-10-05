try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty

from levelui import LevelUI

import re
import random
import time
import math
import logging
import logging.config
from threading import Timer

logging.config.fileConfig('logs/logging.conf')
logger = logging.getLogger('main')

class TorpedoAlley:
	def __init__(self):
		self.in_queue = Queue()
		self.out_queue = Queue()
		
		# application states and transitions
		self._current_state_name = "level1"
		self._current_state = Level(1)

		self.states = {
			"menu": [Menu],
			"level1": [Level, 1],
			"level2": [Level, 2],
			"exit": [Exit]
		}

		self._transitions = {
			"menu": {
				"start": "level1",
				"quit": "exit"
			},
			"level1": {
				"complete": "level2",
				"quit": "exit" 
			},
			"level2": {
				"quit": "exit" 
			}
		}

		self.total_score = 0

		logger.debug("TorpedoAlley created")

	def change_state(self, transition):
		self._current_state.cleanup()
		self._current_state_name = self.current_transitions()[transition]
		self._current_state = self.states[self._current_state_name][0](*self.states[self._current_state_name][1:])

	def current_transitions(self):
		return self._transitions[self._current_state_name]

	def build_ui(self):
		self.ui = self._current_state.display(self.in_queue, self.out_queue)

	def run(self):
		quit = False

		# creates a Tk instance that displays the current screen
		self.build_ui()

		while not quit:
			try:
				event = self.in_queue.get_nowait()
				logger.debug("Received event: %s" % str(event))

				if event in self.current_transitions():
					self.out_queue.put("close")
					self.total_score += self._current_state.score
					self.change_state(event)
					self.build_ui()
					logger.debug("Transitioned to state %s" % self._current_state_name)
				else:
					self._current_state.handle(event)

				if event == "quit":
					quit = True
			except Empty:
				pass

		logger.debug("TorpedoAlley terminated.")

# state logic
class Menu:
	pass

class Level:
	def __init__(self, level_number):
		self.level_number = level_number
		self.ship_rate = 1.0/3.0
		self.ship_timer = Timer(-math.log(random.random())/self.ship_rate, self.ship_appearance, ())
		self.number_of_ships = 0
		self.max_number_of_ships = 30
		self.score = 0
		self.score_per_ship = 50*self.level_number

		logger.debug("Level %d created." % level_number)

	def cleanup(self):
		logger.debug("Cleaning up level %d" % self.level_number)
		self.ship_timer.cancel()

	def display(self, in_queue, out_queue):
		self.in_queue = in_queue
		self.out_queue = out_queue
		ui = LevelUI(self.level_number, out_queue, in_queue)

		# schedule random ship appearances
		self.ship_timer.start()

		logger.debug("UI built for level %d" % self.level_number)

		return ui

	def handle(self, event):
		if re.match(r'launch (\d+),(\d+)', event):
			logger.debug("Torpedo launched")

			# torpedo launched, we could throttle number here or somesuch
			# for now, we simply notify the UI to launch it
			self.out_queue.put(event)
		elif re.match(r'hit (\d+)', event):
			self.increase_score()
			logger.debug("Hit! Score is %d" % self.score)

			self.out_queue.put(event)
		else:
			logger.debug("Received unhandled event: %s" % str(event))

	def increase_score(self):
		self.score += self.score_per_ship
		self.out_queue.put("score %d" % self.score)


	def ship_appearance(self):
		logger.debug("A new ship appears.")
		self.out_queue.put("ship")

		self.number_of_ships += 1
		if not self.number_of_ships >= self.max_number_of_ships:
			# calculate next appearance - Poisson process
			U = random.random()
			nextTime = -math.log(U)/self.ship_rate

			self.ship_timer = Timer(nextTime, self.ship_appearance, ())
			self.ship_timer.start()
		else:
			logger.debug("All ships arrived")
			self.level_complete()

	def level_complete(self):
		logger.debug("Level complete")
		self.out_queue.put("complete")

class Exit:
	# dummy method, will exit
	def display(self, in_queue, out_queue):
		pass

if __name__ == "__main__":
	ta = TorpedoAlley()
	ta.run()
