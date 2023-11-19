from config import *

class Beat(Resource):
    def get(self):
        return 'the app is running on {}'.format(os.getenv("FLASK_RUN_PORT"))
