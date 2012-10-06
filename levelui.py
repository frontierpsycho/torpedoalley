from Tkinter import *
from Queue import Queue, Empty
import tkMessageBox

import os
import threading
import operator
import math
import re
import logging
import logging.config

import graphics_helpers

logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logs") + os.path.sep + "logging.conf")
logger = logging.getLogger('ui')

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

class LevelUI(threading.Thread):
	__metaclass__ = Singleton

	def __init__(self, level_number, in_queue, out_queue, starting_score=0):
		threading.Thread.__init__(self)
		self.in_queue = in_queue
		self.out_queue = out_queue
		self.level_number = level_number
		self.starting_score = starting_score
		self.start()

	def run(self):
		if not hasattr(self, "root"):
			self.root=Tk()

		self.root.protocol("WM_DELETE_WINDOW", self.destroy_confirm)

		self.canvas = Canvas(self.root, width=800, height=600)
		self.canvas.bind("<KeyPress>", self.keyPressed)
		self.canvas.bind("<KeyRelease>", self.keyReleased)
		self.canvas.bind("<Button-1>", self.launch_send)
		self.canvas.focus_set()
		self.canvas.pack()

		# create the status panel
		self.status_panel = Frame(self.root, width=800, height=30)
		self.status_panel.pack()

		if not hasattr(self, "score_text"):
			self.score_text = StringVar()
			self.score_text.set("Score: %d" % self.starting_score)

		score_label = Label(self.status_panel, textvariable=self.score_text)
		score_label.pack(side="right")

		level_label = Label(self.status_panel, text="Level %d" % self.level_number)
		level_label.pack(side="left")

		# create the sea
		self.sea = self.canvas.create_rectangle(0, 200, 800, 600, fill="blue")
		# and the sky
		self.sky = self.canvas.create_rectangle(0, 0, 800, 200, fill="cyan")

		# create submarine and keep it
		self.submarine = self.canvas.create_rectangle(350, 383, 450, 412, fill="green")

		# explosion image
		self.explosion = PhotoImage(file=os.path.join(os.path.dirname(__file__), "data") + os.path.sep + "explosion.gif")

		# these keypresses are forwarded to steer, the rest go to the game loop
		self.directions = ["Left", "Right", "Up", "Down"]

		self.stopped = True # submarine starts stopped
		self.completed = False # level not completed

		logger.debug("UI built, entering loops")

		self.check_input()
		
		self.root.mainloop()

	### custom main loop to receive commands from game logic
	def check_input(self):
		try:
			event = self.in_queue.get_nowait()
			if re.match(r'launch (\d+),(\d+)', event):
				self.launch(event)
			elif re.match(r'ship', event):
				self.ship()
			elif re.match(r'hit (\d+)', event):
				m = re.match(r'hit (\d+)', event)
				try:
					self.destroy_ship(int(m.group(1)))
				except ValueError:
					logger.error("Received hit with invalid id: '%s'" % m.group(1))
			elif re.match(r'score (\d+)', event):
				m = re.match(r'score (\d+)', event)
				try:
					self.set_score(int(m.group(1)))
				except ValueError:
					logger.error("Received new score with invalid value: '%s'" % m.group(1))
			elif re.match(r'start (\d+) (\d+)', event):
				m = re.match(r'start (\d+) (\d+)', event)
				try:
					self.level_number = int(m.group(1))
					self.set_score(int(m.group(2)))
					self.run()
				except ValueError:
					logger.error("Received invalid request to start: '%s'" % event)
			elif event == "complete":
				self.completed = True
		except Empty:
			pass
		self.root.after(5, self.check_input)
	
	def set_score(self, score):
		self.score_text.set("Score: %d" % score)

	def level_complete(self):
		self.canvas.create_text(400,300, text="Level complete!", fill="white", font=("Arial", 16, "bold"))
		self.canvas.bind("<Return>", self.close)
	
	def place_torpedo(self):
		sub_coords = self.canvas.coords(self.submarine)

		sub_height = math.ceil(math.fabs(sub_coords[3]-sub_coords[1]))
		sub_coords[1] -= 10
		sub_coords[3] -= sub_height

		sub_width = math.ceil(math.fabs(sub_coords[0] - sub_coords[2])/2.0)

		sub_coords[0] += sub_width - 5
		sub_coords[2] -= sub_width - 5

		return sub_coords

	### item movement functions ######################################################################################
	def check_underwater(self, object):
		coords = self.canvas.coords(self.sea)
		return (object in self.canvas.find_enclosed(*coords))

	def stop_submarine(self):
		self.stopped = True

	def move_ship(self, ship_id, speed):
		self.canvas.move(ship_id, speed, 0)

		if ship_id not in self.canvas.find_overlapping(*self.canvas.coords(self.sky)):
			self.canvas.delete(ship_id)
			if self.completed and not self.canvas.find_withtag("ship"):
				self.level_complete()
		else:
			self.root.after(30, self.move_ship, ship_id, speed)

	def torpedo_deltas(self, torpedo_coords, dest_coords):
		torpedo_center = graphics_helpers.circle_center_from_bbox(5, torpedo_coords)

		# get difference of destination coordinates from center coordinates
		tx, ty = [float(dest_coords[0]-torpedo_center[0]), float(dest_coords[1]-torpedo_center[1])]
		
		# dx, dy and desired speed form a right triangle
		return graphics_helpers.deltas_for_speed(7, tx, ty)

	def steer(self, direction, speed=2):
		if direction == "Left":
			dx, dy = (-speed, 0)
		elif direction == "Right":
			dx, dy = (speed, 0)
		elif direction == "Up":
			dx, dy = (0, -speed)
		elif direction == "Down":
			dx, dy = (0, speed)
		else:
			# panic! Just kidding.
			logger.error("Received %s and don't know how to handle it!" % direction)
	
		self.canvas.move(self.submarine, dx, dy)
		if not self.check_underwater(self.submarine):
			self.canvas.move(self.submarine, -dx, -dy)
			self.stopped = True
	
		if not self.stopped:
			self.root.after(30, self.steer, direction, speed)

	### member functions that send events to the main loop ###########################################################
	def keyPressed(self, event):
		if event.keysym in self.directions:
			if self.stopped:
				self.stopped = False
				self.steer(event.keysym)

		self.out_queue.put(event.keysym)

	def launch_send(self, mouseclick):
		if mouseclick.y < self.canvas.coords(self.submarine)[1]:
			# only destinations over the sub are valid
			self.out_queue.put("launch %d,%d" % (mouseclick.x, mouseclick.y))

	def destroy_confirm(self):
		if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
			self.out_queue.put("quit")
			self.root.destroy()

	def move_torpedo(self, torpedo_id, dx, dy):
		coords = self.canvas.coords(torpedo_id)

		if self.check_underwater(torpedo_id):
			self.canvas.move(torpedo_id, dx, dy)
			
			# detect if torpedo hit ship
			overlapping_objects = set(self.canvas.find_overlapping(*self.canvas.coords(torpedo_id)))
			ships = set(self.canvas.find_withtag("ship"))
			overlapping_ships = overlapping_objects & ships
			if overlapping_ships:
				self.out_queue.put("hit %d" % overlapping_ships.pop())
				torpedo_center = graphics_helpers.circle_center_from_bbox(5, coords)
				self.canvas.delete(torpedo_id)
				kaboom = self.canvas.create_image(torpedo_center[0], torpedo_center[1], image=self.explosion)
				self.root.after(500, self.canvas.delete, kaboom)


			self.root.after(50, self.move_torpedo, *[torpedo_id, dx, dy])
		else:
			# if torpedo left the sea, delete it
			self.canvas.delete(torpedo_id)

	def close(self, event):
		self.canvas.destroy()
		self.status_panel.destroy()
		self.out_queue.put("complete")

	### member functions that display events received from the main loop ################################################
	def keyReleased(self, event):
		if event.keysym in self.directions:
			self.stop_submarine()

	def launch(self, event):
		torpedo_coords = self.place_torpedo()

		m = re.match(r'launch (?P<x>\d+),(?P<y>\d+)', event)
		dest_coords = [int(m.group('x')), int(m.group('y'))]

		# calculate deltas for movement towards desired direction
		dx, dy = self.torpedo_deltas(torpedo_coords, dest_coords)

		torpedo_id = self.canvas.create_oval(*torpedo_coords, fill="black")
		
		self.move_torpedo(torpedo_id, dx, dy)

	def ship(self):
		ship_id = self.canvas.create_rectangle(-99, 175, 1, 200, fill="red", tags="ship")
		self.move_ship(ship_id, 2)

	def destroy_ship(self, ship_id):
		self.canvas.delete(ship_id)
		if self.completed and not self.canvas.find_withtag("ship"):
			self.level_complete()
