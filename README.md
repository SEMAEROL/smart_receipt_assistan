# Smart Receipt Assistant

**Project Objective:**

It is an intelligent information extraction system that automatically extracts Date, Tax, and Total Amount information from complex receipt images in different languages ​​with high accuracy, using OCR (Optical Character Recognition) and spatial coordinate (BBox) analysis.

## Installation
To avoid system conflicts with dependencies, you must install the project in a virtual environment (venv).

**1. Creating the Virtual Environment:** Create the environment by navigating to the project directory in the terminal:
`python3 -m venv venv`

**2. Activating the Virtual Environment:**
- **Windows:** `venv\Scripts\activate`
- **macOS / Linux:** `source venv/bin/activate`

**3. Installing Necessary Libraries:**
While the environment is active, install the dependencies by reading the `requirements.txt` file:
`pip install -r requirements.txt`