import unittest

from Queue import Queue
from Tkinter import *

from .. import levelui

class TestLevelUI(unittest.TestCase):
	def setUp(self):
		self.in_queue = Queue()
		self.out_queue = Queue()

		self.ui = levelui.LevelUI(2, self.out_queue, self.in_queue)

	def test_mouseclick(self):
		# UGLY HACK peruse at your own risk
		while True:
			if hasattr(self.ui, "completed"):
				break

		e = Event()
		e.widget = self.ui.canvas
		e.type = "<Button-1>"
		e.x = 200
		e.y = 200
		self.ui.launch_send(e)

		outside_event = self.in_queue.get()
		self.assertEqual(outside_event, "launch 200,200")

if __name__ == '__main__':
	unittest.main()
