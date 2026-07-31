import os

# Configure Vertex AI environment for the integration test suite
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"] = "law-search-456009"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
