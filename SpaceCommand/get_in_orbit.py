import sys
import time

import krpc

from SpaceCommand.space_ship.controls import NavComputer

SPEED_ALTITUDE_RATIO = 40
APOAPSIS_IN_M = 100000
STARTING_SPEED_LIMIT = 350
ENGINE_DELAY = 1

conn = krpc.connect(name="Get in orbit")
vessel = conn.space_center.active_vessel
navComputer = NavComputer(vessel)

print("Taking over ship")
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.auto_pilot.engage()
throttle_value = 1.0
print(" Launch in")
for i in ["3", "2", "1", "0"]:
    time.sleep(1)
    print(i+"...")
vessel.control.throttle = throttle_value
gravity_turn_not_initiated = True
print("Egine Ignition")

vessel.control.activate_next_stage()
time.sleep(ENGINE_DELAY)
print("Release clamps")
vessel.control.activate_next_stage()

speed_limit = STARTING_SPEED_LIMIT

# First four three stages are engines.
while vessel.control.current_stage > 4:
    if gravity_turn_not_initiated and vessel.flight().mean_altitude > 10000:
        navComputer.execute_gravity_turn()
        gravity_turn_not_initiated = False
    navComputer.correct_speed(speed_limit,1)
    navComputer.decouple_empty_engines(2)

# now we head for apoapsis
print("Waiting to reach apoapsis of %s" % APOAPSIS_IN_M)
# At this point we check apoapsis and continue to accelerate until we get what
# we want
while vessel.orbit.apoapsis_altitude < APOAPSIS_IN_M:
    speed_limit = vessel.flight().mean_altitude / SPEED_ALTITUDE_RATIO
    navComputer.correct_speed(speed_limit,0.5)


print("Projected vessel apoappsis: ", vessel.orbit.apoapsis_altitude)
print("Cutting throttle off!")
# at this point cut thrust to a minimum so we don't loose control
vessel.control.throttle = 0.001
while (vessel.orbit.time_to_apoapsis > 30):
    degrees_above_horizon = 10
    sys.stdout.write("\rTime to apoapsis: %i s"
                     % vessel.orbit.time_to_apoapsis)
    sys.stdout.flush()

navComputer.chase_the_apoapsis()

conn.close()








