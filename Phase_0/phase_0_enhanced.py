# Documentation - https://mavsdk.mavlink.io/main/en/python/quickstart.html
# http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/plugins/telemetry.html
# http://mavsdk-python-docs.s3-website.eu-central-1.amazonaws.com/plugins/action.html

import asyncio
from mavsdk import System

async def func():
    drone = System()
    # Listening on the dedicated offboard API port
    await drone.connect(system_address="udpin://0.0.0.0:14555")
    
    print("Waiting for drone to connect on port 14555...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Connection to Drone Successful")
            break
            
    print("Waiting for drone sensors to settle (EKF) and GPS lock...")
    async for health in drone.telemetry.health():
        # The ultimate safety check: wait until PX4 officially says "I am ready"
        if health.is_global_position_ok and health.is_armable:
            print("[INFO] Drone is fully Armable and GPS Locked")
            break
    
    print("Arming motors...")
    await drone.action.arm()
    
    #Default TakeOff Altitude is 2.5 Meters to change it
    max_altitude = 10
    await drone.action.set_takeoff_altitude(max_altitude)
    print("Taking off...")
    await drone.action.takeoff()
    
    flag = 1
    async for position in drone.telemetry.position():
        lat, long = position.latitude_deg, position.longitude_deg
        if flag:
            print(f"[INFO] COORDS: LAT {lat} LON {long}")
            flag = 0
        altitude = position.relative_altitude_m
        target_altitude = 3 # Because simulated sensors still have a tiny bit of noise 
        if(altitude < target_altitude):
            print(f"[INFO] Current Altitude : {altitude} meters") 
        else:
            print(f"[INFO] Target Altitude Reached, i.e, {altitude} meters")
            break    
    
    print("Hover/Loiter at Current Position....")
    await drone.action.hold()
    
    await asyncio.sleep(10)
        
    print("Initiating landing sequence...")
    await drone.action.land()
    
    
if __name__ == "__main__":
    asyncio.run(func())