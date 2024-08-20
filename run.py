from app import create_app
from dotenv import load_dotenv
from config import Config
from helpers import get_url


load_dotenv()
app = create_app()


@app.context_processor
def inject_helpers():
    return dict(get_url=get_url)

if __name__ == '__main__':
    app.run(debug=True, port=Config.PORT)