##  Phase 0 — Setup, Validation & Basic Autonomy

### Overview - 
This phase establishes the foundational infrastructure for autonomous UAV control using PX4 SITL (Software-In-The-Loop) and MAVSDK-Python. It establishes reliable MAVLink communication, monitor vehicle health telemetry, and execute closed-loop flight state transitions (Arm, Takeoff, Hover, Land).

### Prerequisites - 

**Flight Stack:** PX4 Autopilot (Running on Raspberry Pi / Linux)

**API:** MAVSDK-Python (pip install mavsdk asyncio)

**GCS:** QGroundControl (Running on Host Mac/PC)

> [!NOTE]
> To get PX4 Up and Running and Connected to Mac -> Refer this [Article](https://tejasjm.com/blog/px4-sitl) 

### Architecture & Network Routing - 

Running the simulator on a remote machine (Raspberry Pi) and the execution script on a host machine (Mac). I Faced some problems while using the PX4 broadcast parameters  and had port collisions with QGroundControl (which aggressively hogs port 14550).

So to run both QGC and the Python script simultaneously, I utilise Direct IP Targeting to create a private MAVLink stream.

**The Routing Bypass -**

Instead of modifying broadcast parameters, I simply route a secondary MAVLink instance directly to the host machine's IP address using a custom port (14555), leaving 14550 free for QGC.


### Execution Scripts -
This phase contains two scripts demonstrating different levels of control logic.

1. ***phase_0_simple.py*** (Open-Loop / Timed)
A "fire-and-forget" script. It polls the core.connection_state() and telemetry.health() streams to ensure the EKF is settled and a GPS lock is achieved (is_global_position_ok and is_armable). It then commands a takeoff, sleeps the Python thread for 10 seconds, and commands a landing.

2. ***phase_0_enhanced.py*** (Closed-Loop / Telemetry Feedback)
A closed-loop profile. Instead of relying on blind timers, it actively monitors the drone.telemetry.position() stream.

Modifies the default PX4 takeoff altitude to Maximum Altitude.

Actively polls position.relative_altitude_m.

Dynamically triggers the hold() command only when the physical telemetry proves the vehicle has crossed the threshold.

### 📊 Deliverables & Proof of Execution - 

**Flight Review Log:** [PX4 Logs](https://logs.px4.io/plot_app?log=42c1b618-a42e-443c-a7bb-f30c7f475269)

**Project Working Snippet -**

![GIF](assets/Phase_0/Phase_0_Video.gif)

### 💻 Usage

Command Sequence - 

```
# 1. Login
ssh commander@dronepi.local

# 2. Fix Wi-Fi Regulation (Run every boot)
sudo iw reg set IN

# 3. Enter Directory
cd PX4-Autopilot

# 4. Start Simulation (Headless)
HEADLESS=1 make px4_sitl jmavsim

# 5. Connection Bind to Mac (pxh>)
mavlink start -u 14581 -o 14555 -t <MAC_IP> -m onboard

# 6. Open QGroundControl in Mac

# 7. Run Program in Mac -
uv run phase_0_enhanced.py
```

Workflow -
 
```mermaid 
sequenceDiagram
    autonumber
    
    actor User as User (Mac)
    participant MacTerm as Mac Terminal
    participant PiTerm as Pi Terminal (SSH)
    participant PX4 as PX4 SITL (Pi)
    participant QGC as QGroundControl (Mac)
    participant MAVSDK as Python Script (Mac)

    rect rgb(240, 248, 255)
    Note over User, PiTerm: Phase 1: Environment Setup
    User->>MacTerm: ssh commander@dronepi.local
    activate MacTerm
    MacTerm->>PiTerm: Establish SSH Connection
    activate PiTerm
    PiTerm-->>MacTerm: Connection Established
    User->>PiTerm: sudo iw reg set IN
    PiTerm-->>User: Wi-Fi Region Updated (India)
    User->>PiTerm: cd PX4-Autopilot
    end

    rect rgb(255, 250, 240)
    Note over User, QGC: Phase 2: Simulation & Networking
    User->>PiTerm: HEADLESS=1 make px4_sitl jmavsim
    PiTerm->>PX4: Spawn Headless Simulator
    activate PX4
    PX4-->>PiTerm: pxh> prompt ready
    Note right of PX4: Default Broadcast active on 14550
    User->>QGC: Open Application
    activate QGC
    PX4->>QGC: MAVLink auto-connects (Port 14550)
    User->>PiTerm: mavlink start -u 14581 -o 14555 -t <MAC_IP> -m onboard
    PiTerm->>PX4: Create private MAVLink stream
    Note right of PX4: Secondary stream bypasses localhost
    PX4-->>User: Dedicated UDP stream routing to Mac (Port 14555)
    end

    rect rgb(240, 255, 240)
    Note over User, MAVSDK: Phase 3: Mission Execution (Closed-Loop)
    User->>MacTerm: uv run phase_0_enhanced.py
    MacTerm->>MAVSDK: Spawn Python Process
    activate MAVSDK
    MAVSDK->>PX4: Connect via udpin://0.0.0.0:14555
    PX4-->>MAVSDK: Handshake & Health Telemetry Stream
    Note left of PX4: Waiting for is_armable & GPS Lock
    MAVSDK->>PX4: Command: Arm & Takeoff to Max Altitude
    PX4-->>MAVSDK: Altitude Telemetry (climbing)
    MAVSDK->>PX4: Command: Hold (at threshold)
    Note right of MAVSDK: Kinematic overshoot occurs
    MAVSDK->>PX4: Command: Land
    PX4-->>MAVSDK: Disarm detected
    MAVSDK-->>MacTerm: Clean Exit
    deactivate MAVSDK
    deactivate QGC
    deactivate PX4
    deactivate PiTerm
    deactivate MacTerm
    end
```