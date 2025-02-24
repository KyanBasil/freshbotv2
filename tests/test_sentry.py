import os
import pytest
from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from unittest.mock import patch, MagicMock

def create_test_app():
    """Create a test Flask application with Sentry integration."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Initialize Sentry with test configuration
    sentry_sdk.init(
        dsn="https://test@sentry.io/1234567",
        integrations=[FlaskIntegration()],
        environment="testing",
        traces_sample_rate=1.0
    )
    
    # Add test routes
    @app.route("/")
    def test_sentry():
        1 / 0  # Intentional error
        return "This won't be displayed"

    @app.route("/success")
    def success():
        return "Success"
        
    return app

@pytest.fixture
def app():
    """Fixture to provide test application."""
    return create_test_app()

@pytest.fixture
def client(app):
    """Fixture to provide test client."""
    return app.test_client()

def test_sentry_captures_error(client):
    """Test that Sentry captures the ZeroDivisionError."""
    with patch('sentry_sdk.capture_exception') as mock_capture:
        # Access route that raises error
        response = client.get('/')
        
        # Verify response
        assert response.status_code == 500
        
        # Verify Sentry captured the error
        mock_capture.assert_called_once()
        captured_exception = mock_capture.call_args[0][0]
        assert isinstance(captured_exception, ZeroDivisionError)

def test_success_route(client):
    """Test that success route works normally."""
    response = client.get('/success')
    assert response.status_code == 200
    assert b"Success" in response.data

def test_sentry_config():
    """Test that Sentry configuration is properly set based on environment."""
    from config import config
    
    # Test production config
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SENTRY_DSN'] = 'https://prod@sentry.io/1'
    os.environ['SENTRY_ENVIRONMENT'] = 'production'
    os.environ['SENTRY_TRACES_SAMPLE_RATE'] = '0.1'
    
    prod_config = config['production']()
    assert prod_config.SENTRY_DSN == 'https://prod@sentry.io/1'
    assert prod_config.SENTRY_ENVIRONMENT == 'production'
    assert prod_config.SENTRY_TRACES_SAMPLE_RATE == 0.1
    
    # Test development config
    os.environ['FLASK_ENV'] = 'development'
    os.environ['SENTRY_DSN'] = 'https://dev@sentry.io/1'
    os.environ['SENTRY_ENVIRONMENT'] = 'development'
    os.environ['SENTRY_TRACES_SAMPLE_RATE'] = '1.0'
    
    dev_config = config['development']()
    assert dev_config.SENTRY_DSN == 'https://dev@sentry.io/1'
    assert dev_config.SENTRY_ENVIRONMENT == 'development'
    assert dev_config.SENTRY_TRACES_SAMPLE_RATE == 1.0
    
    # Test testing config (should use hardcoded values)
    test_config = config['testing']()
    assert test_config.SENTRY_DSN == 'https://test@sentry.io/1234567'
    assert test_config.SENTRY_ENVIRONMENT == 'testing'
    assert test_config.SENTRY_TRACES_SAMPLE_RATE == 1.0