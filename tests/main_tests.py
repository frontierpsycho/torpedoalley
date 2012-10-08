import unittest

from .. import main

class TestMain(unittest.TestCase):
	def setUp(self):
		self.ta = main.TorpedoAlley()

	def test_change_state_valid_transition(self):
		self.ta._current_state_name = "level1"
		self.ta.change_state("complete")

		self.assertEqual(self.ta._current_state_name, "level2")

		self.assertIsInstance(self.ta._current_state, self.ta.states[self.ta._current_state_name][0])

		self.assertEqual(self.ta._current_state.level_number, 2)

	def test_change_state_invalid_transition(self):
		self.ta._current_state_name = "level1"
		with self.assertRaises(KeyError):
			self.ta.change_state("bogustransition")

		self.assertEqual(self.ta._current_state_name, "level1")

		self.assertIsInstance(self.ta._current_state, self.ta.states[self.ta._current_state_name][0])
		self.assertEqual(self.ta._current_state.level_number, 1)

if __name__ == '__main__':
	unittest.main()
