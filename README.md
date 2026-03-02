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
%%{init: { 'theme': 'base', 'themeVariables': { 'textColor': '#000000', 'actorTextColor': '#000000', 'signalTextColor': '#000000', 'noteTextColor': '#000000', 'labelTextColor': '#000000', 'loopTextColor': '#000000', 'sectionTextColor': '#000000', 'activationBorderColor': '#000000' } } }%%
sequenceDiagram
    autonumber
    
    %% Use Actor/Participant aliases for cleaner logic
    actor U as User (Mac)
    participant MT as Mac Terminal
    participant PT as Pi Terminal (SSH)
    participant PX4 as PX4 SITL (Pi)
    participant QGC as QGroundControl (Mac)
    participant PY as MAVSDK Script (Mac)

    %% Phase 1
    rect rgb(230, 240, 255)
    Note over U, PT: Phase 1: Environment Setup
    U->>MT: ssh commander@dronepi.local
    activate MT
    MT->>PT: Establish SSH Connection
    activate PT
    PT-->>MT: Connection Established
    U->>PT: sudo iw reg set IN
    PT-->>U: Wi-Fi Region Updated (India)
    end

    %% Phase 2
    rect rgb(240, 240, 240)
    Note over U, QGC: Phase 2: Simulation & Networking
    U->>PT: HEADLESS=1 make px4_sitl jmavsim
    activate PX4
    PT->>PX4: Spawn Headless Simulator
    PX4-->>PT: pxh> prompt ready
    Note right of PX4: Broadcast active on 14550
    U->>QGC: Open Application
    activate QGC
    PX4->>QGC: MAVLink auto-connects (14550)
    U->>PT: mavlink start -u 14581 -o 14555 -t <MAC_IP>
    PT->>PX4: Create private MAVLink stream
    PX4-->>U: UDP stream to Mac (Port 14555)
    end

    %% Phase 3
    rect rgb(230, 255, 230)
    Note over U, PY: Phase 3: Mission Execution
    U->>MT: uv run phase_0_enhanced.py
    activate PY
    MT->>PY: Spawn Python Process
    PY->>PX4: Connect via udpin://0.0.0.0:14555
    PX4-->>PY: Handshake & Telemetry
    Note left of PX4: Wait for Armable/GPS
    PY->>PX4: Command: Arm & Takeoff
    PX4-->>PY: Altitude Telemetry
    PY->>PX4: Command: Land
    PX4-->>PY: Disarm detected
    PY-->>MT: Clean Exit
    deactivate PY
    deactivate QGC
    deactivate PX4
    deactivate PT
    deactivate MT
    end
```