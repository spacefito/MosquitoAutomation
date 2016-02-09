import sys
import time

import krpc

from space_ship.controls import correct_speed

SPEED_ALTITUDE_RATIO = 40
APOAPSIS_IN_M = 100000
STARTING_SPEED_LIMIT = 250
ENGINE_DELAY=1

def  execute_gravity_turn(vessel):
    print("Starting gravity turn")
    vessel.auto_pilot.target_pitch_and_heading(60,90)

def decouple_empty_engines(vessel):
    engines = []
    for part in vessel.parts.all:
        if part.engine:
            engines.append(part)
    number_of_empty_egines  = 0
    for part in engines:
        if not part.engine.has_fuel:
            number_of_empty_egines +=1
        if number_of_empty_egines > 1:
                number_of_empty_egines  = 0;
                vessel.control.activate_next_stage()


conn = krpc.connect(name="Get in orbit")

vessel = conn.space_center.active_vessel

print("Taking over ship")
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.auto_pilot.engage()
throttle_value = 1.0
print (" Launch in")
for i in [ "3","2","1","0"]:
    time.sleep(1)
    print (i+"...")
vessel.control.throttle = throttle_value
gravity_turn_not_initiated = True
print ("Egine Ignition")

vessel.control.activate_next_stage()
time.sleep(ENGINE_DELAY)
print ("Release clamps")
vessel.control.activate_next_stage()

speed_limit = STARTING_SPEED_LIMIT

# First four three stages are engines.
while vessel.control.current_stage >4:
    if gravity_turn_not_initiated and vessel.flight().mean_altitude > 10000:
        execute_gravity_turn(vessel)
        gravity_turn_not_initiated = False
    correct_speed(vessel,speed_limit)
    decouple_empty_engines(vessel)

# now we head for apoapsis
print ("Waiting to reach apoapsis of %s" %APOAPSIS_IN_M)
# At this point we check apoapsis and continue to accelerate until we get what we want
while vessel.orbit.apoapsis_altitude < APOAPSIS_IN_M:
    correct_speed(vessel,speed_limit)
    speed_limit = vessel.flight().mean_altitude / SPEED_ALTITUDE_RATIO

print ("Projected vessel apoappsis: ", vessel.orbit.apoapsis_altitude)
print ("Cutting throttle off!")
# at this point cut thrust to a minimum so we don't loose control
throttle_value = 0.001
vessel.control.throttle = throttle_value
# and wait to reach orbit
desired_orbit_reached = False
while not desired_orbit_reached:
    degrees_above_horizon = 10
    sys.stdout.write("\rTime to apoapsis: %i s" % vessel.orbit.time_to_apoapsis)
    sys.stdout.flush()
    if vessel.orbit.time_to_apoapsis < 30:
        throttle_value= 0.10
        degrees_above_horizon = 10
    if vessel.orbit.time_to_apoapsis < 20:
        throttle_value= 0.20
        degrees_above_horizon = 10
    if vessel.orbit.time_to_apoapsis < 10:
        throttle_value= 0.75
        degrees_above_horizon = 15
    if vessel.orbit.time_to_apoapsis < 7:
        throttle_value= 1
        degrees_above_horizon = 15
    if vessel.orbit.time_to_apoapsis > 45:
        throttle_value = 0

    vessel.auto_pilot.target_pitch_and_heading(degrees_above_horizon ,90)

    vessel.control.throttle = throttle_value



    acceptable_error = vessel.orbit.apoapsis_altitude * .01
    if (vessel.orbit.apoapsis_altitude - vessel.orbit.periapsis_altitude) < acceptable_error:
        desired_orbit_reached = True

    engines = []
    number_of_empty_egines = 0
    for part in vessel.parts.all:
        if part.engine:
            engines.append(part)
    for part in engines:
        if not part.engine.has_fuel:
            number_of_empty_egines +=1
        if number_of_empty_egines > 0:
                number_of_empty_egines  = 0;
                vessel.control.activate_next_stage()
                print ("current stage: ", vessel.control.current_stage)

vessel.control.throttle = 0
if desired_orbit_reached:
    print ("success!")









