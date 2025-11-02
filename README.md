# 🩹 AidNexus - AI First Aid Assistant

A minimal viable product (MVP) for an AI-powered first aid assistant built using **Streamlit** and the **Google Gemini API**.

This application allows users to upload an image of a potential injury. The Gemini model analyzes the image (multimodal input) and generates immediate, concise, step-by-step first aid instructions, along with a crucial medical disclaimer.

## Quick start

### 1. **setup**
Choose one of the following methods to set up your Python environment and dependencies:
#### Option A: Standard Virtual Environment (venv + pip)

##### 1. Clone the repository:

```commandline
git clone 
cd first_aid_ai_agent
```
##### 2. Create and activate the virtual environment:
```bash
python -m venv venv
source venv/bin/activate  
```
for windows
```commandline
python -m venv venv
venv\Scripts\activate
```
##### 3. Install Dependencies:
This method uses the `requirements.txt` file (assuming it's present in the project root).
```commandline
pip install -r requirements.txt
```
##### 4. Run the App:
```commandline
streamlit run app.py
```
#### Option B: Dependency Management with Poetry (Recommended)
This project supports Poetry for cleaner dependency management.
##### 1. Clone the repository:
```commandline
git clone 
cd first_aid_ai_agent
```
##### 2. Install Poetry:

If you haven't already, install Poetry by following the instructions on the [official documentation site](https://python-poetry.org/docs/).

##### 3. Install Dependencies:
Poetry will read the dependencies from `pyproject.toml` (if available), create a virtual environment (if needed), and install all necessary packages.
```commandline
poetry install
```
you can also get the dependencies from `requirements.txt`
```commandline
poetry run pip install -r requirements.txt
```
##### 4. Run the App:

Use `poetry run` to execute the application within the virtual environment managed by Poetry.

```commandline
poetry run streamlit run app.py
```

### 2. API Key Configuration
The application uses Streamlit's native secrets management.

#### 1. Create a folder named .streamlit in the root of your project:
```commandline
mkdir .streamlit
```
#### 2. Create a file named secrets.toml inside the .streamlit folder and add your Gemini API Key:
```streamlit/secrets.toml
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```
## Project Structure Overview
* `app.py`: The main Streamlit UI and flow control.
* `utils/ai_helpers.py`: Contains the `get_gemini_client` and analyze_injury_and_get_first_aid functions for clean, reusable AI logic.
* `.streamlit/secrets.toml`: Securely stores the `GEMINI_API_KEY`.