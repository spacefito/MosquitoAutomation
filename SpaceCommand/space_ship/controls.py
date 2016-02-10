import math
import time
import sys

class NavComputer(object):
    def __init__(self, vessel):
        self._vessel = vessel

    @property
    def vessel(self):
        return self._vessel

    @vessel.setter
    def vessel(self, vessel):
        self._vessel = vessel

    @staticmethod
    def calculate_desired_g_force(vessel_speed, target_speed, delta_t):

        delta_v = target_speed - vessel_speed
        desired_acceleration = delta_v/delta_t
        desired_g_force = desired_acceleration/9.8
        if desired_g_force < 0:
            desired_g_force = 0
        return desired_g_force

    def correct_speed(self, target_speed, delay=0):
        time.sleep(delay)
        throttle_value = self._vessel.control.throttle
        g_force = self.vessel.flight().g_force
        margin = 0.1
        acceleration_time = 2

        # if vessel speed is below our target speed AND the g force is not
        # accelerating it we have to increase the throttle until g_force is
        # large enough
        vessel_speed = self._vessel.flight(
            self._vessel.orbit.body.reference_frame).speed
        desired_g_force = self.calculate_desired_g_force(vessel_speed,
                                                         target_speed,
                                                         acceleration_time)
        if vessel_speed < target_speed:
            if g_force < desired_g_force:
                ratio = target_speed / vessel_speed
                throttle_value = (throttle_value +
                                        (1 - throttle_value) / ratio)
                if throttle_value > 1:
                    throttle_value = 1.0
                self._vessel.control.throttle = throttle_value

        # if we are going faster than the target speed, we cut down on
        # the throttle
        elif vessel_speed > target_speed * (1 + margin):
            throttle_value = self._vessel.control.throttle / 2
            self._vessel.control.throttle = throttle_value

    def execute_gravity_turn(self):
        print("Starting gravity turn")
        self.vessel.auto_pilot.target_pitch_and_heading(60, 90)

    def decouple_empty_engines(self, number_of_engines_to_decouple=1):
        engines = []
        for part in self.vessel.parts.all:
            if part.engine:
                engines.append(part)
        number_of_empty_egines = 0
        for part in engines:
            if not part.engine.has_fuel:
                number_of_empty_egines += 1
            if number_of_empty_egines > number_of_engines_to_decouple - 1:
                self.vessel.control.activate_next_stage()
                return True
        return False


    def better_chase_the_apoapsis(self, desired_apoapsis_altitude,
                                  accuracy = 0.05):
        derivative_of_delta_v = 1
        degrees_to_horizon = 10
        print("entering while loop")
        while True:
            start_time_to_apoapsis = self._vessel.orbit.time_to_apoapsis
            if start_time_to_apoapsis < 10:
                delta_v = self.accelerate_towards_apoapsis(
                    1, 30)
            else:
                delta_v = self.accelerate_towards_apoapsis(
                    derivative_of_delta_v,degrees_to_horizon)
            end_time_to_apoapsis = self._vessel.orbit.time_to_apoapsis
            print("delta_v: %s"%delta_v)
            derivative_of_delta_v = ( delta_v /
                            (end_time_to_apoapsis - start_time_to_apoapsis)
                                    )
            print("derivative of delta_v: %s"%derivative_of_delta_v)
            if self._vessel.orbit.periapsis_altitude >= (desired_apoapsis_altitude *
                                                          (1 - accuracy)):
                print ("reached altitude")
                return True
            self.decouple_empty_engines(1)

            if self.all_ship_fuel_spent():
                return False

    def all_ship_fuel_spent(self):
        if self._vessel.mass == self._vessel.dry_mass:
            return True
        return False

    def accelerate_towards_apoapsis(self, derivative_of_delta_v=1,
                                    degrees_above_horizon=0):
        ''''@:param derivative_of_delta: constant representing a relationship
        between the thrustof the vessel and its delta_v
        '''
        start_vessel_speed = self._vessel.flight(
                                self._vessel.orbit.body.reference_frame).speed
        self._vessel.auto_pilot.target_pitch_and_heading(degrees_above_horizon, 90)
        print ("derivative: %s"%derivative_of_delta_v)
        throttle_value = 1/derivative_of_delta_v
        if throttle_value > 1 :
            throttle_value = 1
        print("throttling to: %s"%throttle_value)
        self._vessel.control.throttle = throttle_value
        time.sleep(2)
        self._vessel.control.throttle = 0
        end_vessel_speed = self._vessel.flight(
                                self._vessel.orbit.body.reference_frame).speed
        return end_vessel_speed - start_vessel_speed

    def get_magnitude_of_vector(self, vector):
        x = vector[0]
        y = vector[1]
        z = vector[2]
        return math.sqrt(x*x + y*y + z*z)


    def chase_the_apoapsis(self):
        desired_orbit_reached = False

        while not desired_orbit_reached:
            throttle_value = 0.01
            orbital_ratio = ( self._vessel.orbit.periapsis_altitude
                              / self._vessel.orbit.apoapsis_altitude)
            if orbital_ratio < 0 :
                orbital_ratio  = 0

            degrees_above_horizon = 15 * (1- orbital_ratio)
            drag = self.get_magnitude_of_vector(self._vessel.flight().drag)
            sys.stdout.write("\rTime to apoapsis: %i s"
                             % self.vessel.orbit.time_to_apoapsis)
            sys.stdout.flush()
            if drag >  5:
                if self._vessel.orbit.time_to_apoapsis < 30:
                    throttle_value = 0.5
                    degrees_above_horizon = 10
                if self._vessel.orbit.time_to_apoapsis < 25:
                    throttle_value = 0.10
                    degrees_above_horizon = 10
                if self._vessel.orbit.time_to_apoapsis < 20 :
                    throttle_value = 0.15
                    degrees_above_horizon = 10
            if self._vessel.orbit.time_to_apoapsis < 10:
                throttle_value = 0.50
                degrees_above_horizon = 15
            if self._vessel.orbit.time_to_apoapsis < 7:
                throttle_value = 0.75
                degrees_above_horizon = 15
            if self._vessel.orbit.time_to_apoapsis < 5:
                throttle_value = 1
                degrees_above_horizon = 15
            if self._vessel.orbit.time_to_apoapsis > 45:
                throttle_value = 0

            self._vessel.auto_pilot.target_pitch_and_heading(degrees_above_horizon, 90)
            self._vessel.control.throttle = throttle_value
            acceptable_error = self._vessel.orbit.apoapsis_altitude * .01
            if ((self._vessel.orbit.apoapsis_altitude
                     - self._vessel.orbit.periapsis_altitude) <
                    acceptable_error):
                desired_orbit_reached = True
            if(self.decouple_empty_engines(1)):
                self._vessel.control.activate_next_stage()

