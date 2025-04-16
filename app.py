from flask import Flask 
app = Flask(__name__)
@app.route('/')
def hello():
    return "Hello from Flask in Codespaces!"
if __name__ == '__main__':
    app.run(debug=True)

@app.route('/two')
def hello_two():
    return "Hello from Flask in Codespaces! This is the second route."
