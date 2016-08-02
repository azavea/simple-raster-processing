from flask import Flask

app = Flask(__name__)


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
