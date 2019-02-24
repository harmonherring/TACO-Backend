from taco_api import app
import os
if __name__ == '__main__':
    app.run(ip=os.environ.get('API_IP', "0.0.0.0"), port=os.environ.get('API_PORT', 8080))

application = app
