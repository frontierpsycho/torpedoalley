import math

def circle_center_from_bbox(radius, bbox):
	center = map(lambda x: x+radius, bbox[0:2])
	return center

def deltas_for_speed(speed, tx, ty):
	if tx == 0:
		return 0, math.copysign(speed, ty)
	else:
		tan = ty/tx

		dx = speed/math.sqrt(tan**2 + 1)
		dy = tan*dx

		dx = math.copysign(dx, tx)
		dy = math.copysign(dy, ty)

		return dx, dy
