from flask import Flask, send_from_directory
import os

app = Flask(__name__)
root_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(root_dir, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(root_dir, filename)

if __name__ == '__main__':
    print("Starting Splendor P2P Server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5001)
