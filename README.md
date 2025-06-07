# CafèBot-a-Socially-Aware-Assistant-for-coffee-shop-service
This repository contains the source code for CaféBot, an autonomous, socially-aware robotic platform designed to augment service quality and operational efficiency in a coffee-shop environment. Built on the Pepper humanoid robot, CaféBot delivers personalized assistance to customers, staff and supervisors by combining:

- **Advanced Natural Language Processing** powered by Large Language Models for adaptive, role-based dialogue management.
- **Semantic Environmental Mapping** for spatial reasoning and precise product lookup.
- **Multimodal Interaction** (vocal, gestural, and tablet GUI) with dynamic adaptation based on user role and real-time cognitive load.
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
│   ├── perception.py
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

## **Authors and License**

- **Authors**:  
  - Michael Corelli | [corelli.1938627@studenti.uniroma1.it](mailto:corelli.1938627@studenti.uniroma1.it)
  - Gianmarco Donnesi | [donnesi.2152311@studenti.uniroma1.it](mailto:donnesi.2152311@studenti.uniroma1.it)  

- **License**: this project is licensed under the [Apache License 2.0](LICENSE). See the file for more details.