# 🌊 Ocean Buzz | The Data Lab

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Deep-Diving into Data to Protect the Pale Blue Dot.**

Welcome to the **Ocean Buzz Data Lab**. This repository houses the source code for the interactive simulators and auditing tools featured in the Ocean Buzz ecosystem. The goal is to take the vast, often murky currents of global information and transform them into real signal, helping users understand what is actually driving the Blue Economy.

## 🤿 The Tools

Currently, the Data Lab features the following operational modules:

* **Blue Carbon Offset (BCO) Budget Calculator:** A financial modeling tool that allows users to input corporate Carbon Offset Targets and time windows to generate baseline budget estimations for meeting sustainability needs.

## 🚀 Local Installation & Usage

To run the Ocean Buzz Data Lab on your local machine, follow these steps:

**1. Clone the repository:**
```bash
git clone https://github.com/ArturJVBarbosa/Ocean-Buzz.git
cd Ocean-Buzz
```
**2. Create and activate a virtual environment (Recommended):**
```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```
**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

## 📂 Project Structure

```text
Ocean-Buzz/
│
├── Home.py                  # Main Streamlit landing page
├── pages/                   # Directory containing individual tool scripts
│   └── 1_BCO_Calculator.py   
├── utils.py                 # Helper functions and global styling
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
