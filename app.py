from taco_api import app

if __name__ == '__main__':
    app.run(port=os.environ.get('API_PORT', 8080))

application = app
