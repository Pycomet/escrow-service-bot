from config import *
from .routes import UserList, User, TradeList, Trade, Beat, DisputeList, Dispute

### API configurations
api_bp = Blueprint('api', __name__)
api = Api(api_bp, prefix='/api/v1')

api.add_resource(Beat, '/')

api.add_resource(UserList, '/users')
api.add_resource(User, '/users/<user_id>')

api.add_resource(TradeList, '/trades')
api.add_resource(Trade, '/trades/<trade_id>')

api.add_resource(DisputeList, '/disputes')
api.add_resource(Dispute, '/disputes/<dispute_id>')