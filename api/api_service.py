class APIService:
    """
    A centralized API service class for handling all API requests in the application.
    Features:
    - Token management
    - Request queueing for time-related events
    - Error handling and retries
    - Centralized endpoint configuration
    """

    # Base URL for API requests
    BASE_URL = "http://localhost:3000/"



    