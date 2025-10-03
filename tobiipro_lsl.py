#!/usr/bin/env python
""" Streams Tobii pro data through an LSL outlet
Will find all connected Tobii devices and start streaming the data of the first one.
"""

import time
import math
import signal
import sys
from pylsl import StreamInfo, StreamOutlet
import tobii_research as tr

__author__ = "Marios Fanourakis"

def gaze_data_callback(gaze_data):
    
#    if gaze_data['left_gaze_point_validity']:
    left_on_display_x = gaze_data['left_gaze_point_on_display_area'][0]
    left_on_display_y = gaze_data['left_gaze_point_on_display_area'][1]
#    else:
#        left_on_display_x = -1
#        left_on_display_y = -1
#    if gaze_data['left_gaze_origin_validity']:
    left_origin_x = gaze_data['left_gaze_origin_in_user_coordinate_system'][0]
    left_origin_y = gaze_data['left_gaze_origin_in_user_coordinate_system'][1]
    left_origin_z = gaze_data['left_gaze_origin_in_user_coordinate_system'][2]
#    else:
#        left_origin_x = -1
#        left_origin_y = -1
#        left_origin_z = -1
#    if gaze_data['left_pupil_validity']:
    left_pupil_diam = gaze_data['left_pupil_diameter']
#    else:
#        left_pupil_diam = -1
#        
#    if gaze_data['right_gaze_point_validity']:
    right_on_display_x = gaze_data['right_gaze_point_on_display_area'][0]
    right_on_display_y = gaze_data['right_gaze_point_on_display_area'][1]
#    else:
#        right_on_display_x = -1
#        right_on_display_y = -1
#    if gaze_data['right_gaze_origin_validity']:
    right_origin_x = gaze_data['right_gaze_origin_in_user_coordinate_system'][0]
    right_origin_y = gaze_data['right_gaze_origin_in_user_coordinate_system'][1]
    right_origin_z = gaze_data['right_gaze_origin_in_user_coordinate_system'][2]
#    else:
#        right_origin_x = -1
#        right_origin_y = -1
#        right_origin_z = -1
#    if gaze_data['right_pupil_validity']:
    right_pupil_diam = gaze_data['right_pupil_diameter']
#    else:
#        right_pupil_diam = -1
    
    sample = [
              left_on_display_x, left_on_display_y, 
              left_origin_x, left_origin_y, left_origin_z, 
              left_pupil_diam,
              right_on_display_x, right_on_display_y, 
              right_origin_x, right_origin_y, right_origin_z, 
              right_pupil_diam
              ]
    
    timestamp = gaze_data['system_time_stamp']/1000000
    outlet.push_sample(sample, timestamp)


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
    outlet.__del__()
    print("Unsubscribed from gaze data.")
    sys.exit(0)


eyetrackers = tr.find_all_eyetrackers()
if not eyetrackers:
  raise ValueError('eyetrackers not found')
eyetracker = eyetrackers[0]

# print("Address: " + eyetracker.address)
# print("Model: " + eyetracker.model)
# print("Name (It's OK if this is empty): " + eyetracker.device_name)
# print("Serial number: " + eyetracker.serial_number)


sampling_rate = 120
if eyetracker.model=='Tobii Pro Nano':
  sampling_rate = 60

info = StreamInfo('ET', 'gaze', 12, sampling_rate, 'float32', eyetracker.serial_number)
print(info.type())

# append some meta-data
info.desc().append_child_value("manufacturer", "Tobii")
channels = info.desc().append_child("channels")
for c in ["left_on_display_x", "left_on_display_y", 
          "left_origin_x", "left_origin_y", "left_origin_z", 
          "left_pupil_diam",
          "right_on_display_x", "right_on_display_y",
          "right_origin_x", "right_origin_y", "right_origin_z",
          "right_pupil_diam"]:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "mm") \
        .append_child_value("type", "gaze")

# next make an outlet; we set the transmission chunk size to 5 samples and
# the outgoing buffer size to 360 seconds (max.)
outlet = StreamOutlet(info, 5, 360)   


print("Subscribing to gaze data for eye tracker with serial number {0}.".format(eyetracker.serial_number))
eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)

signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to exit')

while True:
    pass
    