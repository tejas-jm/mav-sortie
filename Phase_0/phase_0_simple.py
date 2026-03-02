# Dcoumentation - https://mavsdk.mavlink.io/main/en/python/quickstart.html

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

    print("Taking off...")
    await drone.action.takeoff()

    print("Hovering for 10 seconds...")
    await asyncio.sleep(10)

    print("Initiating landing sequence...")
    await drone.action.land()


if __name__ == "__main__":
    asyncio.run(func())
