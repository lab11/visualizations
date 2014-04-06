#!/usr/bin/env python3

import copy
import json
import glob
import os
import sys

try:
	import dxfgrabber
except:
	print('You need dxfgrabber')
	print('sudo pip install dxfgrabber')
	sys.exit(1)


buildings = {}

building_template = {
	'name':          '',
	'name_short':    '',
	'gps_latitude':  0,
	'gps_longitude': 0,
	'width':         0,
	'height':        0,
	'floors':        {}
};

floor_template = {
	'name': '',
	'z':0,
	'rooms':[]
}

dxfs = glob.glob('../floorplan/*.dxf')
for dxf in dxfs:
	dirname = os.path.dirname(dxf)
	filename = os.path.splitext(dxf)[0]

	building_id,floorid = os.path.basename(filename).split('_')

	# Parse the .DXF
	dxfparsed = dxfgrabber.readfile(dxf)

	# Make sense of the rooms
	min_global_x = 10000000.0
	min_global_y = 10000000.0
	max_global_x = -10000000.0
	max_global_y = -10000000.0

	rooms = []

	with open(filename + '_rooms.txt') as f:
		room_numbers = f.readlines()

	for e in dxfparsed.entities:
		if type(e) == dxfgrabber.entities.Polyline:
			room = {'lower_left':[],
			        'vertices':[]}

			min_x = 1000000.0
			min_y = 1000000.0


			for v in e.points():
				x = round(v[0]/1000.0, 4)
				y = round(v[1]/1000.0, 4)
				room['vertices'].append([x,y])

				if x < min_x:
					min_x = x
				if y < min_y:
					min_y = y

				if x < min_global_x:
					min_global_x = x
				if y < min_global_y:
					min_global_y = y

				if x > max_global_x:
					max_global_x = x
				if y > max_global_y:
					max_global_y = y

			for v in room['vertices']:
				v[0] -= min_x
				v[1] -= min_y

			room['lower_left'] = [min_x, min_y]

			rooms.append(room)


	# Check if this building exists (from parsing a different floor)
	if building_id not in buildings:
		buildings[building_id] = copy.deepcopy(building_template)

		# Fill in info from .info file
		with open(dirname + '/' + building_id + '.info') as f:
			for line in f:
				if len(line.strip()) == 0:
					continue
				opts = line.split(':', 1)
				buildings[building_id][opts[0].strip().lower()] = opts[1].strip()

	# Add the new floor
	buildings[building_id]['floors'][floorid] = copy.deepcopy(floor_template)

	# Check if we made the building bigger
	width = max_global_x - min_global_x
	height =  max_global_y - min_global_y
	if width > buildings[building_id]['width']:
		buildings[building_id]['width'] = width
	if height > buildings[building_id]['height']:
		buildings[building_id]['height'] = height

	# All all rooms

	# order by lowest y value, then use lowest x value to break any ties
	def orderroom(r):
		return r['lower_left'][1]*1000.0 + r['lower_left'][0]

	for i,room in zip(range(len(rooms)), sorted(rooms, key=orderroom)):
		offset_x = room['lower_left'][0] - min_global_x
		offset_y = room['lower_left'][1] - min_global_y

		buildings[building_id]['floors'][floorid]['rooms'].append({
			'name': room_numbers[i].strip(),
			'coordinates': room['vertices'],
			'offset': (offset_x, offset_y)
		})


for buildingid,building in buildings.items():
	with open('../web/' + buildingid + '.json', 'w') as f:
		f.write(json.dumps(building))

