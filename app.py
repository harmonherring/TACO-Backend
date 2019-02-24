from taco_api import app
import os
if __name__ == '__main__':
    app.run(host=app.config['IP'], port=app.config['PORT'])

application = app
