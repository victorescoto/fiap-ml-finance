import os
from mangum import Mangum
from app.fastapi_app.main import app

handler = Mangum(app)