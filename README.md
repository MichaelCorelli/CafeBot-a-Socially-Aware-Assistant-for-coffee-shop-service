# CafèBot-a-Socially-Aware-Assistant-for-coffee-shop-service
This repository contains the source code for CaféBot, an autonomous, socially-aware robotic platform designed to augment service quality and operational efficiency in a coffee-shop environment. Built on the Pepper humanoid robot, CaféBot delivers personalized assistance to customers, staff and supervisors by combining:

- **Advanced Natural Language Processing** powered by Large Language Models for adaptive, role-based dialogue management.
- **Semantic Environmental Mapping** for spatial reasoning and precise product lookup.
- **Multimodal Interaction** (vocal, gestural, and tablet GUI) with dynamic adaptation based on user role and real-time cognitive load.
-   **Dynamic 3D Perception & Semantic Mapping**: In the simulation, CaféBot performs an initial 360-degree scan of its environment to build a `dynamic_semantic_map`. Using a **YOLOv8** model, it detects objects, localizes them in 3D space, and maps general COCO labels to cafe-specific items (e.g., 'cup' becomes 'cappuccino'), creating a rich, queryable world model.
- **Human-Aware Navigation** using an A*-derived planner with dynamic collision avoidance that differentiates between static obstacles and moving humans.
- **Vision-Based Perception** (YOLO object detection) to recognize user-presented products and retrieve details such as pricing, location, and qualitative attributes.

--- 

## Directory Structure
The project files are organized as follows:

```
CafeBot-a-Socially-Aware-Assistant-for-coffee-shop-service/
│
├── llm_server.py                # The cognitive server based on FastAPI and LLMs
├── main_simulation_dynamic.py   # Main entry point for the dynamic and interactive simulation
├── main_simulation.py           # Entry point for a static navigation demo
├── main.py                      # Entry point for execution on the real Pepper robot
│
├── pepper_llm_bridge.py         # Bridge to connect the real Pepper robot to the LLM server
├── simulation_llm_bridge.py     # Bridge to connect the simulation to the LLM server
│
├── src/                         # Source code for the real robot
│   ├── motion.py
│   ├── say.py
│   ├── dance.py
│   └── default_configuration.py
│
├── simulation/                  # Source code and assets for the simulation
│   ├── motion_simulation.py
│   ├── motion_simulation_dynamic.py
│   ├── perception.py
│   ├── dynamic_planner.py
│   ├── live_speech.py
│   ├── say_simulation.py
│   ├── dance_simulation.py
│   └── ... (other support files and URDF objects)
│
├── menu.json                    # Product knowledge base for the coffee shop
├── requirements.txt             # Project's Python dependencies
└── README.md                    # This file
```
---

## Setup and Installation
Follow these steps to set up the development environment.

1. Clone the Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd CafeBot-a-Socially-Aware-Assistant-for-coffee-shop-service
```

2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install Dependencies
The project requires the libraries listed in requirements.txt. For a successful installation of PyAudio, you may need to install portaudio on your system (sudo apt-get install portaudio19-dev on Debian/Ubuntu, brew install portaudio on macOS).
```bash
pip install -r requirements.txt
```

4. Configure API Keys
Create a file named `.env` in the project's root directory. This file will hold your OpenAI API key.
```bash
OPENAI_API_KEY="sk-xx...xx"
```

The `llm_server.py` script will automatically load this key.

---

## How to Run the Project
The system requires two separate components to be running: the LLM Server and the Simulation Client.

**1. Start the LLM Server**

Open a terminal, activate the virtual environment, and start the FastAPI server.
```bash
uvicorn llm_server:app --reload
```
The server will be listening at `http://localhost:8000`. Leave this terminal running.

**2. Run the Dynamic Simulation**

This is the main mode that demonstrates all the robot's capabilities. Open a second terminal, activate the virtual environment, and launch the main_simulation_dynamic.py script.
```bash
python main_simulation_dynamic.py
```

**3. Run on the Real Robot**

To run the code on a physical Pepper robot, ensure you are connected to the same network.

Make sure the LLM Server is running (see step 1).

Launch the main.py script, providing the robot's IP address.
```bash
python main.py --pip <YOUR_PEPPER_IP>
```
This script will execute a pre-defined sequence of actions (wake_up, welcome, moveToGoal, dance, rest) using the modules in the `/src` directory. For a full LLM-based interaction, the `pepper_llm_bridge.py` script contains the necessary logic.

---

## **Authors and License**

- **Authors**:  
  - Michael Corelli | [corelli.1938627@studenti.uniroma1.it](mailto:corelli.1938627@studenti.uniroma1.it)
  - Gianmarco Donnesi | [donnesi.2152311@studenti.uniroma1.it](mailto:donnesi.2152311@studenti.uniroma1.it)  

- **License**: this project is licensed under the [Apache License 2.0](LICENSE). See the file for more details.