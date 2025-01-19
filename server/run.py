from app import create_app
from flask_bootstrap import Bootstrap

app = create_app()
Bootstrap(app)

if __name__ == "__main__":
    app.run(debug=True)
