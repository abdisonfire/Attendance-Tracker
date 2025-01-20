from app import create_app
from flask_bootstrap import Bootstrap5

app = create_app()
Bootstrap5(app)

if __name__ == "__main__":
    app.run(debug=True)
