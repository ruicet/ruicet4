from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO, join_room, emit
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wparty_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    nickname = request.form.get('nickname', 'Гость')
    room_id = str(uuid.uuid4())[:6]
    rooms[room_id] = {'host': None, 'video_url': ''}
    return redirect(url_for('room', room_id=room_id, nickname=nickname))

@app.route('/room/<room_id>')
def room(room_id):
    # Убрали 'Гость', теперь если ника нет, передается None
    nickname = request.args.get('nickname')
    return render_template('room.html', room_id=room_id, nickname=nickname)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    
    is_host = False
    if room in rooms and rooms[room]['host'] is None:
        rooms[room]['host'] = request.sid
        is_host = True
        
    emit('system_message', {'text': f"{data['nickname']} подключился к комнате"}, room=room)
    emit('you_are_host', {'is_host': is_host, 'video_url': rooms.get(room, {}).get('video_url', '')}, to=request.sid)

@socketio.on('set_video')
def on_set_video(data):
    room = data['room']
    if room in rooms and rooms[room]['host'] == request.sid:
        rooms[room]['video_url'] = data['url']
        emit('video_changed', {'url': data['url']}, room=room)

@socketio.on('sync')
def on_sync(data):
    emit('sync', data, room=data['room'], include_self=False)

@socketio.on('chat')
def on_chat(data):
    data['time'] = datetime.now().strftime('%H:%M')
    data['msg_id'] = str(uuid.uuid4())[:8]
    emit('chat', data, room=data['room'])

@socketio.on('react')
def on_react(data):
    emit('react', data, room=data['room'])

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, debug=True)
