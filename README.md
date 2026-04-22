# Intelligent Edge-AI Perception and Active Safety System for Autonomous EVs
Dataset Link : "https://www.kaggle.com/datasets/meowmeowmeowmeowmeow/gtsrb-german-traffic-sign"
![ROS 2](https://img.shields.io/badge/ROS_2-Humble-22314E?logo=ros)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)
![TFLite](https://img.shields.io/badge/TensorFlow_Lite-Edge-FF6F00?logo=tensorflow)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry_Pi_4-C51A4A?logo=raspberry-pi)

A scalable, real-time Advanced Driver Assistance System (ADAS) and autonomous control framework built for resource-constrained edge devices. This project solves the **"Edge Compute Crisis"** by utilizing a decoupled ROS 2 microservice architecture and a heavily quantized TensorFlow Lite vision model to achieve high-FPS traffic sign recognition and active motor control strictly on CPU power.

**Author:** Atharva Yadav
**Institution:** Shri Ramdeobaba College of Engineering and Management (RCOEM), Nagpur
**Department:** Electronics and Computer Science Engineering

---

## 🚀 Executive Summary

Traditional autonomous perception models rely on massive GPUs or cloud computing. This project brings real-time AI to the edge. Running entirely **offline on a Raspberry Pi 4**, the system captures live webcam feeds, processes them through a deeply optimized MobileNetV3/YOLO classification model, and broadcasts telemetry via ROS 2 to trigger active safety interventions (e.g., auto-braking, speed limiting). A zero-latency HTML5/Canvas UI powered by WebSockets provides a live digital dashboard of the vehicle's decision-making process.

---

## 🧠 How It Works Under the Hood

### 1. The Machine Learning Pipeline

- **Dataset Engineering:** Trained on the German Traffic Sign Recognition Benchmark (GTSRB). To eliminate class confusion and maximize safety, the dataset was programmatically filtered to isolate **19 highly specific classes** relevant to the vehicle's Operational Design Domain (ODD).
- **Model Architecture:** Utilizes MobileNetV3-Small (or an exported YOLOv8 classification model), specifically designed for mobile and edge devices using lightweight depthwise separable convolutions.
- **Deep Fine-Tuning:** The model was trained using aggressive data augmentation (Color Jitter, Random Rotation) to simulate real-world driving conditions and motion blur.
- **Edge Quantization:** The PyTorch/YOLO model was exported to ONNX and compressed into a **TensorFlow Lite (`.tflite`) graph** with FP16 quantization. This converts 32-bit floating-point math into 16-bit math, drastically reducing the memory footprint and enabling CPU-bound real-time inference.

### 2. ROS 2 Microservice Architecture

The software abandons the monolithic script approach to ensure high-latency vision processing never blocks low-latency motor control.

| Node | Responsibility |
|---|---|
| **Vision Node** | Downsamples webcam to `320×240`, runs TFLite inference via NumPy/Ultralytics backend, publishes recognized sign strings (e.g., `"Speed Limit 30"`) |
| **Safety Manager Node** | Core state machine — subscribes to vision node, checks vehicle telemetry, and commands emergency overrides on hazard detection |
| **Motor Controller Node** | Interfaces with hardware GPIO pins, generating smooth PWM signals to wheel motors based on Safety Manager commands |

### 3. Dynamic Telemetry & UI Dashboard

- A custom ROS 2 node acts as a **WebSocket server**, broadcasting live PWM targets, dynamic speed limits, and hazard warnings directly to a web browser.
- The frontend uses a high-performance **HTML Canvas** graphics engine to render a glowing, interpolated speedometer and animated contextual hazard alerts (⬅️ 🚶 🦌 ⚠️) with zero latency.

---

## 🛠️ Hardware Requirements

| Component | Specification |
|---|---|
| **Compute** | Raspberry Pi 4 Model B (4GB or 8GB RAM recommended) |
| **Vision** | Standard USB Webcam |
| **Actuation** | L298N Motor Driver (or equivalent) & DC Motors |
| **Power** | 5V/3A stable power supply for the Pi; separate battery pack for motors |

---

## 💻 Software & Dependencies

- **OS:** Ubuntu 22.04 LTS (Server or Desktop)
- **Middleware:** ROS 2 Humble Hawksbill
- **Python Dependencies:**

```bash
pip install tflite-runtime opencv-python numpy ultralytics websockets
```

---

## ⚙️ Installation & Setup

**1. Clone the repository into your ROS 2 workspace:**

```bash
mkdir -p ~/ev_ws/src
cd ~/ev_ws/src
git clone https://github.com/yadav29/edge-ai-ev-safety.git
```

**2. Add your Edge AI Model:**

Place your quantized `mobilenet_v3_edge.tflite` (or YOLO exported `.tflite`) file into the `models/` directory of the vision package. Update the model path in `vision_node.py` to match your filename.

**3. Build the Workspace:**

```bash
cd ~/ev_ws
colcon build --symlink-install
```

---

## 🚦 Execution

To run the full autonomous stack, open separate terminal windows (or use a multiplexer like `tmux`) and execute the following in order.

**Terminal 1 — Vision Perception Engine:**
```bash
source ~/ev_ws/install/setup.bash
ros2 run ev_vision vision_node
```

**Terminal 2 — Safety State Machine:**
```bash
source ~/ev_ws/install/setup.bash
ros2 run ev_control safety_manager
```

**Terminal 3 — Hardware Motor Controller:**
```bash
source ~/ev_ws/install/setup.bash
ros2 run ev_hardware motor_controller
```

**Terminal 4 — WebSocket Telemetry Bridge:**
```bash
source ~/ev_ws/install/setup.bash
ros2 run ev_ui websocket_server
```

**Optional — Web Dashboard:**
Open `dashboard.html` in any modern web browser on a laptop connected to the same Wi-Fi network as the Raspberry Pi to view live telemetry and the vehicle decision dashboard.

---

## 📁 Project Structure

```
ev_ws/
├── src/
│   ├── ev_vision/          # Vision node & TFLite inference
│   ├── ev_control/         # Safety Manager state machine
│   ├── ev_hardware/        # GPIO / Motor Controller node
│   └── ev_ui/              # WebSocket server node
├── models/
│   └── mobilenet_v3_edge.tflite
└── dashboard.html          # Live telemetry frontend
```

---

## 📄 License

This project is developed for academic research at RCOEM, Nagpur. Please contact the author before reuse or redistribution.
