import functions_framework
from main import app

@functions_framework.http
def escrow_bot(request):
    """Firebase Functions entry point that wraps the Quart app"""
    return app(request.environ, lambda x, y: None) 