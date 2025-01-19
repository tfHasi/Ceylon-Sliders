from app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    os.environ["FLASK_APP"] = "run.py"  # Explicitly set the FLASK_APP
    app.run(debug=True)
