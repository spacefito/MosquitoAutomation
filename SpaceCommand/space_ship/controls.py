import time
def calculate_desired_g_force(vessel_speed, target_speed, delta_t):

    delta_v  = target_speed - vessel_speed
    desired_acceleration  = delta_v/delta_t
    desired_g_force = desired_acceleration/9.8
    if desired_g_force < 0:
        desired_g_force = 0
    return desired_g_force

def correct_speed(vessel, target_speed, delay=0):
    time.sleep(delay)
    throttle_value  = vessel.control.throttle
    g_force = vessel.flight().g_force
    margin = 0.1
    acceleration_time = 2

    # if vessel speed is below our target speed AND the g force is not accelerating it
    # we have to increase the throttle until g_force is large enough
    vessel_speed = vessel.flight(vessel.orbit.body.reference_frame).speed
    desired_g_force = calculate_desired_g_force(vessel_speed,target_speed, acceleration_time)
    if g_force >0:
        g_force_ratio = desired_g_force / g_force
    else:
        g_force_ration = -1.0

    if vessel_speed < target_speed:
        if g_force < desired_g_force:
            ratio = target_speed / vessel_speed
            throttle_value = 0.5 + (throttle_value + (1- throttle_value)* ratio)
            if throttle_value > 1:
                throttle_value = 1.0
            print ("increasing throttle to")
            vessel.control.throttle = throttle_value

    # if we are going faster than the target speed, we cut down on the throtle
    elif vessel_speed > target_speed * (1 + margin):
        throttle_value= vessel.control.throttle / 2
        print ("reducing throtle to %s "% throttle_value)
        vessel.control.throttle = throttle_value

