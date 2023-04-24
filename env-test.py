import os
from dotenv import load_dotenv

load_dotenv()

x = os.getenv('DB_ENGINE')
y = os.getenv('DB_NAME')

print(x, y)
