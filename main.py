try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty

from levelui import LevelUI

class TorpedoAlley:
	def __init__(self):
		self.in_queue = Queue()
		self.out_queue = Queue()
		
		# application states and transitions
		self._current_state = "level1"
		self.states = {
			"menu": Menu(),
			"level1": Level(1)
		}
		self._transitions = {
			"menu": {
				"start": "level1"
			},
			"level1": { }
		}

	def current_state(self):
		return self.states[self._current_state]

	def current_transitions(self):
		return self._transitions[self._current_state]

	def build_ui(self):
		self.ui = self.states[self._current_state].display(self.in_queue, self.out_queue)

	def run(self):
		quit = False

		# creates a Tk instance that displays the current screen
		self.build_ui()

		while not quit:
			try:
				event = self.in_queue.get_nowait()

				if event == "quit":
					quit = True
				elif event in self.current_transitions():
					self._current_state = self.current_transitions()[event]
					self.build_ui()
				else:
					self.current_state().handle(event)
			except Empty:
				pass

# state logic
class Menu:
	pass

class Level:
	def __init__(self, level_number):
		self.level_number = level_number

	def display(self, in_queue, out_queue):
		return LevelUI(self.level_number, out_queue, in_queue)

	def handle(self, event):
		pass

class Exit:
	# dummy method, will exit
	def display(self, in_queue, out_queue):
		pass

if __name__ == "__main__":
	ta = TorpedoAlley()
	ta.run()
