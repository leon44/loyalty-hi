# Loyalty Portal

A minimal but production-shaped Flask web application that provides a passwordless “magic link” login and a customer self-service portal backed by the EPOS Now Customer API.

## How to Run Locally

1.  **Clone the repository**

2.  **Set up the environment:**

    *   It is recommended to use a virtual environment.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    *   Copy the example `.env.example` file to `.env`.

    ```bash
    cp .env.example .env
    ```

    *   Edit the `.env` file and add your actual credentials:
        *   `FLASK_APP`: Set to `main.py` to point Flask to the correct application file.
        *   `FLASK_DEBUG`: Set to `1` to enable debug mode and the auto-reloader.
        *   `SECRET_KEY`: A long, random string for Flask session security.
        *   `EPOS_API_KEY`: Your EPOS Now API Key.
        *   `EPOS_API_SECRET`: Your EPOS Now API Secret.

5.  **Run the application:**

    ```bash
    python -m flask run
    ```

    The application will be available at `http://127.0.0.1:5000`.

    *Note: Since this setup does not include a mail server, the magic link URL will be printed to the console where you are running the Flask app. Copy and paste this URL into your browser to complete the login process.*

## How to Run Tests

1.  **Make sure you have installed the dependencies (including `pytest`).**

2.  **Run pytest from the root of the project:**

    ```bash
    pytest
    ```
