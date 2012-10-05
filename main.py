try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty

from levelui import LevelUI

import re
import random
import time
import math
from threading import Timer

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
			"exit": [Exit]
		}

		self._transitions = {
			"menu": {
				"start": "level1",
				"quit": "exit"
			},
			"level1": { "quit": "exit" }
		}

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

				if event in self.current_transitions():
					self.change_state(event)
					self.build_ui()
				else:
					self._current_state.handle(event)

				if event == "quit":
					quit = True
			except Empty:
				pass

# state logic
class Menu:
	pass

class Level:
	def __init__(self, level_number):
		self.level_number = level_number
		self.ship_rate = 1.0/3.0
		self.ship_timer = Timer(-math.log(random.random())/self.ship_rate, self.ship_appearance, ())

	def cleanup(self):
		self.ship_timer.cancel()

	def display(self, in_queue, out_queue):
		self.in_queue = in_queue
		self.out_queue = out_queue
		ui = LevelUI(self.level_number, out_queue, in_queue)

		# schedule random ship appearances
		self.ship_timer.start()

		return ui

	def handle(self, event):
		if re.match(r'launch (\d+),(\d+)', event):
			# torpedo launched, we could throttle number here or somesuch
			# for now, we simply notify the UI to launch it
			self.out_queue.put(event)
		elif re.match(r'hit (\d+)', event):
			# TODO increase score, perhaps delete ship
			self.out_queue.put(event)
		else:
			print event

	def ship_appearance(self):
		self.out_queue.put("ship")

		# calculate next appearance - Poisson process
		U = random.random()
		nextTime = -math.log(U)/self.ship_rate

		self.ship_timer = Timer(nextTime, self.ship_appearance, ())
		self.ship_timer.start()

class Exit:
	# dummy method, will exit
	def display(self, in_queue, out_queue):
		pass

if __name__ == "__main__":
	ta = TorpedoAlley()
	ta.run()
