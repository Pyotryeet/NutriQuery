# NutriQuery: Setup & Testing Guide

This guide provides instructions on how to set up the backend and frontend environments, run the test suites, and start the application using `uv` (for Python) and `npm` (for React).

## 1. Prerequisites

Ensure you have the following installed on your system:
- **Python 3.10+**
- **Node.js & npm** (for the React frontend)
- **uv** (an extremely fast Python package installer and resolver)
  *To install `uv`, you can run: `curl -LsSf https://astral.sh/uv/install.sh | sh` or use Homebrew: `brew install uv`*
- **Docker** (for MSSQL database)

---

## 2. Backend Setup & Testing (Using `uv`)

We are using `uv` for blazing fast dependency management instead of `pip`. 

### A. Environment Setup
Navigate to the `backend` directory and create a virtual environment:

```bash
cd backend

# Create a fast virtual environment using uv
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install all requirements using uv
uv pip install -r requirements.txt
```

### B. Running the Tests
Now that your MSSQL Docker container is running, you can execute the test suite to verify the database interactions, API endpoints, and Machine Learning functionalities.

```bash
# Ensure you are in the backend directory with the virtual environment activated
pytest tests/ -v
```

**Test Coverage:**
- `test_api.py`: Validates FastAPI endpoints (`/foods`, `/categories`, `/queries`, etc.)
- `test_crud.py`: Tests direct SQL interactions and MSSQL queries.
- `test_ml.py`: Checks the ML service and device allocations.
- `test_import.py`: Validates the structure for bulk data imports.

### C. Starting the Backend Server
To run the backend for the application:

```bash
uvicorn main:app --reload --reload-exclude ".venv" --host 0.0.0.0 --port 8000
```

---

## 3. Frontend Setup (React)

The frontend has been completely rewritten using a modern React & Vite stack.

### A. Environment Setup
Navigate to the `frontend` directory and install the node packages:

```bash
# From the project root, go to the frontend folder
cd frontend

# Install the React dependencies (including AG Grid)
npm install
```

### B. Starting the Frontend Server
To launch the React application in development mode:

```bash
npm run dev
```

The terminal will provide a local URL (typically `http://localhost:5173`). Open that in your browser to view the new creamy-matte NutriQuery interface!
