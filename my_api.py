from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timedelta
import json
import math

from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

import db

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('register_form'))

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register_form.html')
    
@app.route('/register', methods=['POST'])
def register():
    login = request.form['login']
    if not login:
        return render_template('register_fail.html', reason='Empty login not allowed.')

    password = request.form['password']
    if len(password) < 6:
        return render_template('register_fail.html', reason='Password is too short')

    name = request.form['name'] or None
    email = request.form['email'] or None

    if db.user(login=login):
        return render_template('register_fail.html', reason='User already exists.'.format(login))

    db.user.insert(login=login,
                   password_hash=sha256(password.encode('UTF-8')).digest(),
                   name=name,
                   email=email)
    db.user.commit()

    return render_template('register_ok.html', login=request.form['login'])

@app.route('/oauth/authorize', methods=['GET'])
def authorize_form():
    response_type = request.args.get('response_type', None)
    client_id = request.args.get('client_id', None)
    state = request.args.get('state', None)

    if client_id is None:
        return render_template('authorize_fail.html', reason='Require client_id.')
    try:
        client_id = int(client_id)
    except:
        client_id = None
    if client_id not in db.client:
        return render_template('authorize_fail.html', reason='client_id is invalid.')

    if response_type is None:
        return redirect(db.client[client_id]['redirect_uri'] + '?error=invalid_request' +
                                                              ('' if state is None else '&state=' + state), code=302)
    if response_type != 'code':
        return redirect(db.client[client_id]['redirect_uri'] + '?error=unsupported_response_type' +
                                                              ('' if state is None else '&state=' + state), code=302)

    return render_template('authorize_form.html', state=state,
                                                  client_id=client_id,
                                                  client_name=db.client[client_id]['name'])

@app.route('/oauth/authorize', methods=['POST'])
def authorize():
    client_id = int(request.form.get('client_id'))
    login = request.form.get('login')
    password = request.form.get('password')
    state = request.form.get('state', None)

    if not db.user(login=login):
        return redirect(db.client[client_id]['redirect_uri'] + '?error=access_denied' + ('' if state is None else '&state=' + state), code=302)
    if db.user(login=login)[0]['password_hash'] != sha256(password.encode('UTF-8')).digest():
        return redirect(db.client[client_id]['redirect_uri'] + '?error=access_denied' + ('' if state is None else '&state=' + state), code=302)

    code=sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    db.authorization_code.insert(user_id=db.user(login=login)[0]['__id__'],
                                 code=code,
                                 expire_time=datetime.now() + timedelta(minutes=10))
    db.authorization_code.commit()

    return redirect(db.client[client_id]['redirect_uri'] + '?code=' + code + ('' if state is None else '&state=' + state), code=302)

@app.route('/oauth/token', methods=['POST'])
def token():
    try:
        grant_type = request.form.get('grant_type')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
    except KeyError:
        return json.dumps({'error': 'invalid_request'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    try:
        client_id = int(client_id)
    except:
        client_id = None
    if client_id not in db.client or db.client[client_id]['secret'] != client_secret:
        return json.dumps({'error': 'invalid_client'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    if grant_type == 'authorization_code':
        try:
            code = request.form.get('code')
        except KeyError:
            return json.dumps({'error': 'invalid_request'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        if not db.authorization_code(code=code) or db.authorization_code(code=code)[0]['expire_time'] < datetime.now():
            return json.dumps({'error': 'invalid_grant'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        user_id = db.authorization_code(code=code)[0]['user_id']

        db.authorization_code.delete(db.authorization_code(code=code))
        db.authorization_code.commit()
    elif grant_type == 'refresh_token':
        try:
            refresh_token = request.form.get('refresh_token')
        except KeyError:
            return json.dumps({'error': 'invalid_request'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        if not db.token(refresh=refresh_token):
            return json.dumps({'error': 'invalid_grant'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        user_id = db.token(refresh=refresh_token)[0]['user_id']

        db.token.delete(db.token(refresh=refresh_token))
        db.token.commit()
    else:
        return json.dumps({'error': 'unsupported_grant_type'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    access_token = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    expire_time = datetime.now() + timedelta(hours=1)
    refresh_token = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    db.token.insert(user_id=user_id,
                    access=access_token,
                    expire_time=expire_time,
                    refresh=refresh_token)
    db.token.commit()

    return json.dumps({
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': 3600,
        'refresh_token': refresh_token,
    }), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
        'Cache-Control': 'no-store',
        'Pragma': 'no-cache',
    }

@app.route('/events/', methods=['GET'])
def get_event():
    try:
        per_page = int(request.args.get('per_page', 20))
        if per_page < 1 or per_page > 100:
            raise Exception()
        page = int(request.args.get('page', 0))
        if page < 0 or page > len(db.event) // per_page:
            raise Exception()
    except:
        return '', 400

    items = []
    for i, event in enumerate(db.event):
        if i < page * per_page:
            continue
        if i >= (page + 1) * per_page:
            break
        items.append({
            'id': event['__id__'],
            'name': event['name'],
            'date': event['date'],
            'desciption': event['description'],
            'organizer': event['organizer'],
        })

    return json.dumps({
        'items': items,
        'per_page': per_page,
        'page': page,
        'page_count': math.ceil(len(db.event) / per_page)
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }

@app.route('/events/<id>', methods=['GET'])
def get_event_item(id):
    try:
        id = int(id)
        if id not in db.event:
            raise Exception()
    except:
        return '', 404

    event = db.event[id]
    return json.dumps({
        'id': event['__id__'],
        'name': event['name'],
        'date': event['date'],
        'desciption': event['description'],
        'organizer': event['organizer'],
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }

@app.route('/bids/', methods=['GET'])
def get_bids():
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db.token(access=access_token) or db.token(access=access_token)[0]['expire_time'] < datetime.now():
        return '', 401 

    user_id = db.token(access=access_token)[0]['user_id']

    try:
        per_page = int(request.args.get('per_page', 20))
        if per_page < 2 or per_page > 100:
            raise Exception()
        page = int(request.args.get('page', 0))
        if page < 0 or page > len(db.bid(user_id=user_id)) // per_page:
            raise Exception()
    except:
        return '', 400

    items = []
    for i, bid in enumerate(db.bid(user_id=user_id)):
        if i < page * per_page:
            continue
        if i >= (page + 1) * per_page:
            break
        items.append({
            'id': bid['__id__'],
            'event': bid['event'],
            'number_tickets': bid['number_tickets'],
        })

    return json.dumps({
        'items': items,
        'per_page': per_page,
        'page': page,
        'page_count': math.ceil(len(db.bid) / per_page)
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }

@app.route('/bids/<id>', methods=['GET'])
def get_bid_item(id):
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db.token(access=access_token) or db.token(access=access_token)[0]['expire_time'] < datetime.now():
        return '', 401

    user_id = db.token(access=access_token)[0]['user_id']

    try:
        id = int(id)
        if id not in db.bid or db.bid[id]['user_id'] != user_id:
            raise Exception()
    except:
        return '', 404

    bid = db.bid[id]
    return json.dumps({
        'id': bid['__id__'],
        'event': bid['event'],
        'number_tickets': bid['number_tickets'],
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }

@app.route('/bids/', methods=['POST'])
def post_bids():
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db.token(access=access_token) or db.token(access=access_token)[0]['expire_time'] < datetime.now():
        return '', 401

    user_id = db.token(access=access_token)[0]['user_id']

    try:
        bid = request.get_json(force=True)
        #print bid['event']
        #for event in bid['event']:
            #print bid['event']['id']
        #if event['id'] not in db.event:
        if bid['event']['id'] not in db.event:
            raise Exception()
        if 'number_tickets' not in bid:
            raise Exception()
    except:
        return '', 400

    id = db.bid.insert(user_id=user_id,
                        event=bid['event'],
                        number_tickets=bid['number_tickets'])

    db.bid.commit()

    return '', 201, {
        'Location': '/bids/{}'.format(id)
    }

@app.route('/bids/<id>', methods=['DELETE'])
def delete_bid_item(id):
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db.token(access=access_token) or db.token(access=access_token)[0]['expire_time'] < datetime.now():
        return '', 401

    user_id = db.token(access=access_token)[0]['user_id']

    try:
        id = int(id)
        if id not in db.bid or db.bid[id]['user_id'] != user_id:
            raise Exception()
    except:
        return '', 404

    db.bid.delete(db.bid[id])
    db.bid.commit()

    return '', 200

@app.route('/bids/<id>', methods=['PUT'])
def put_bid_item(id):
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db.token(access=access_token) or db.token(access=access_token)[0]['expire_time'] < datetime.now():
        return '', 401

    user_id = db.token(access=access_token)[0]['user_id']

    try:
        id = int(id)
        if id not in db.bid or db.bid[id]['user_id'] != user_id:
            raise Exception()
    except:
        return '', 404

    try:
        bid = request.get_json(force=True)
        #for event in bid['event']:
        #    if event['id'] not in db.event or 'amount' not in event:
        #        raise Exception()
        if bid['event']['id'] not in db.event:
            raise Exception()
        if 'number_tickets' not in bid:
            raise Exception()
    except:
        return '', 400

    db.bid.update(db.bid[id], event=bid['event'],
                                  number_tickets=bid['number_tickets'])

    db.bid.commit()

    return '', 200

if __name__ == '__main__':
    app.run(port=5050, debug=True)




