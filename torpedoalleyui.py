try:
	from Tkinter import *
except ImportError:
	from tkinter import *

import tkMessageBox

import threading
import operator

class TorpedoAlleyUI(threading.Thread):
	def __init__(self, queue):
		threading.Thread.__init__(self)
		self.queue = queue
		self.start()
	def run(self):
		self.root=Tk()
		self.root.protocol("WM_DELETE_WINDOW", self.destroy_confirm)

		self.canvas = Canvas(self.root, width=800, height=600)
		self.canvas.bind("<KeyPress>", self.keyPressed)
		self.canvas.bind("<KeyRelease>", self.keyReleased)
		self.canvas.bind("<Button-1>", self.launch)
		self.canvas.focus_set()
		self.canvas.pack()

		# create the sea
		sea = self.canvas.create_rectangle(0, 200, 800, 600, fill="blue")
		# and the sky
		sky = self.canvas.create_rectangle(0, 0, 800, 200, fill="cyan")

		# create submarine and keep it
		self.submarine = self.canvas.create_rectangle(350, 383, 450, 412, fill="green")
		self.torpedoes = []

		self.directions = {
			"Right": operator.add,
			"Left": operator.sub,
			"Down": operator.add,
			"Up": operator.sub
		}
		
		self.stopped = True

		self.root.mainloop()

	def destroy_confirm(self):
		if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
			self.queue.put("quit")
			self.root.destroy()

	def keyPressed(self, event):
		if event.keysym in self.directions:
			if self.stopped:
				self.stopped = False
				self.steer(event.keysym)

		self.queue.put(event.keysym)

	def keyReleased(self, event):
		if event.keysym in self.directions:
			self.stop_submarine()

	def move_object(self, object, newx_topleft, newy_topleft, newx_bottomright, newy_bottomright):
		self.canvas.coords(object, newx_topleft, newy_topleft, newx_bottomright, newy_bottomright)

	def stop_submarine(self):
		self.stopped = True

	def steer(self, direction, speed=2):
		current_coords = self.canvas.coords(self.submarine)
		if direction in ["Left", "Right"]:
			current_coords[0] = self.directions[direction](current_coords[0], speed)
			current_coords[2] = self.directions[direction](current_coords[2], speed)
		elif direction in ["Up", "Down"]:
			current_coords[1] = self.directions[direction](current_coords[1], speed)
			current_coords[3] = self.directions[direction](current_coords[3], speed)
		else:
			# panic! Just kidding.
			print "Received", direction,"and don't know how to handle it!"

		self.move_object(self.submarine, *current_coords)

		if not self.stopped:
			self.root.after(30, self.steer, direction, speed)

	def launch(self, event):
		self.torpedoes.append(self.canvas.create_oval(70, 15, 80, 25, fill="black"))


