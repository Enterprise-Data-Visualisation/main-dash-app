# 1. Create the virtual environment
python -m venv venv

# 2. Activate it
# Windows (Command Prompt):
venv\Scripts\activate
# Mac/Linux (or Git Bash on Windows):
source venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt 

# 4. Run the signal generator
python signal_generator.py

# 5. To install FastAPI, Uvicorn, and Strawberry GraphQL
pip install fastapi uvicorn strawberry-graphql

