
from flask_cors import cross_origin

#from scimodom.database.models import 

from scimodom import create_app
# app = create_app(os.getenv("CONFIG_MODE"))
app = create_app()


@app.route('/test')
@cross_origin(supports_credentials=True)
def test():
    print('Hello world!')
