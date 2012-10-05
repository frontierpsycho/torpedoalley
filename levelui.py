try:
	from Tkinter import *
	from Queue import Queue, Empty
except ImportError:
	from tkinter import *
	from queue import Queue, Empty

import tkMessageBox

import threading
import operator

import math
import re

import graphics_helpers

class LevelUI(threading.Thread):
	def __init__(self, level_number, in_queue, out_queue):
		threading.Thread.__init__(self)
		self.in_queue = in_queue
		self.out_queue = out_queue
		self.start()
	def run(self):
		self.root=Tk()
		self.root.protocol("WM_DELETE_WINDOW", self.destroy_confirm)

		self.canvas = Canvas(self.root, width=800, height=600)
		self.canvas.bind("<KeyPress>", self.keyPressed)
		self.canvas.bind("<KeyRelease>", self.keyReleased)
		self.canvas.bind("<Button-1>", self.launch_send)
		self.canvas.focus_set()
		self.canvas.pack()

		# create the sea
		self.sea = self.canvas.create_rectangle(0, 200, 800, 600, fill="blue")
		# and the sky
		self.sky = self.canvas.create_rectangle(0, 0, 800, 200, fill="cyan")

		# create submarine and keep it
		self.submarine = self.canvas.create_rectangle(350, 383, 450, 412, fill="green")

		# these keypresses are forwarded to steer, the rest go to the game loop
		self.directions = ["Left", "Right", "Up", "Down"]

		self.stopped = True

		self.check_input()

		self.root.mainloop()

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
					pass
		except Empty:
			pass
		self.root.after(5, self.check_input)

	def destroy_confirm(self):
		if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
			self.out_queue.put("quit")
			self.root.destroy()

	def keyPressed(self, event):
		if event.keysym in self.directions:
			if self.stopped:
				self.stopped = False
				self.steer(event.keysym)

		self.out_queue.put(event.keysym)

	def keyReleased(self, event):
		if event.keysym in self.directions:
			self.stop_submarine()

	def place_torpedo(self):
		sub_coords = self.canvas.coords(self.submarine)

		sub_height = math.ceil(math.fabs(sub_coords[3]-sub_coords[1]))
		sub_coords[1] -= 10
		sub_coords[3] -= sub_height

		sub_width = math.ceil(math.fabs(sub_coords[0] - sub_coords[2])/2.0)

		sub_coords[0] += sub_width - 5
		sub_coords[2] -= sub_width - 5

		return sub_coords

	def torpedo_deltas(self, torpedo_coords, dest_coords):
		torpedo_center = graphics_helpers.circle_center_from_bbox(5, torpedo_coords)

		# get difference of destination coordinates from center coordinates
		tx, ty = [float(dest_coords[0]-torpedo_center[0]), float(dest_coords[1]-torpedo_center[1])]
		
		tan = ty/tx

		# dx, dy and desired speed form a right triangle
		return graphics_helpers.deltas_for_speed(7, tx, ty)

	### item movement functions ###
	def check_underwater(self, object):
		coords = self.canvas.coords(self.sea)
		return (object in self.canvas.find_enclosed(*coords))

	def stop_submarine(self):
		self.stopped = True

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

			self.root.after(50, self.move_torpedo, *[torpedo_id, dx, dy])
		else:
			# if torpedo left the sea, delete it
			self.canvas.delete(torpedo_id)

	def move_ship(self, ship_id, speed):
		self.canvas.move(ship_id, speed, 0)

		if ship_id not in self.canvas.find_overlapping(*self.canvas.coords(self.sky)):
			self.canvas.delete(ship_id)
		else:
			self.root.after(30, self.move_ship, ship_id, speed)

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
			print "Received", direction,"and don't know how to handle it!"
	
		self.canvas.move(self.submarine, dx, dy)
		if not self.check_underwater(self.submarine):
			self.canvas.move(self.submarine, -dx, -dy)
			self.stopped = True
	
		if not self.stopped:
			self.root.after(30, self.steer, direction, speed)

	### member functions that send events to the main loop ###
	def launch_send(self, mouseclick):
		if mouseclick.y < self.canvas.coords(self.submarine)[1]:
			# only destinations over the sub are valid
			self.out_queue.put("launch %d,%d" % (mouseclick.x, mouseclick.y))

	### member functions that display events received from the main loop ###
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
