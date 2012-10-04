try:
	from Queue import Queue, Empty
except ImportError:
	from queue import Queue, Empty

from torpedoalleyui import TorpedoAlleyUI

class TorpedoAlley:
	def __init__(self):
		queue = Queue()
		ui = TorpedoAlleyUI(queue)

		quit = False
		while not quit:
			try:
				event = queue.get_nowait()
				if event == "quit":
					quit = True
			except Empty:
				pass

if __name__ == "__main__":
	ta = TorpedoAlley()
