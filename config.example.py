DOCKER_URL = 'unix:///var/run/docker.sock'

DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = ''
DB_DATABASE = ''
DB_CHARSET = 'utf8mb4'

WTF_CSRF_ENABLED = False
SECRET_KEY = 'Dockore'
DATA_DIR = './data'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s:%d/%s?charset=%s' % (
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE, DB_CHARSET
)
