import sentry_sdk
from flask import Flask

# Initialize Sentry SDK with the provided configuration
sentry_sdk.init(
    dsn="https://63247aa8e98648a5ee4c438764852216@o4508876433326080.ingest.us.sentry.io/4508876444860416",
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

# Create a minimal Flask app for testing
test_app = Flask(__name__)

@test_app.route("/")
def test_sentry():
    # This will intentionally raise a ZeroDivisionError
    # which Sentry should capture
    1 / 0
    return "This won't be displayed due to the error"

@test_app.route("/success")
def success():
    # A route that doesn't error, to test transaction tracking
    return "Sentry is working! Check your dashboard for this transaction."

if __name__ == "__main__":
    print("Starting Sentry test server...")
    print("Navigate to http://localhost:5000/ to trigger an error")
    print("Navigate to http://localhost:5000/success to generate a transaction without an error")
    print("Check your Sentry dashboard to verify the events are being captured")
    test_app.run(debug=False)  # Set debug=False to ensure Sentry catches the error
