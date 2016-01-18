from pathlib import Path
from pydblite import Base

if not Path('db').exists():
    Path('db').mkdir()

client = Base('db/client.pdl')
if client.exists():
    client.open()
else:
    client.create('secret', 'redirect_uri', 'name')

authorization_code = Base('db/authorization_code.pdl')
if authorization_code.exists():
    authorization_code.open()
else:
    authorization_code.create('user_id', 'code', 'expire_time')

token = Base('db/token.pdl')
if token.exists():
    token.open()
else:
    token.create('user_id', 'access', 'expire_time', 'refresh')

user = Base('db/user.pdl')
if user.exists():
    user.open()
else:
    user.create('login', 'password_hash', 'name', 'email')

event = Base('db/event.pdl')
if event.exists():
    event.open()
else:
    event.create('name', 'date', 'description', 'organizer')

bid = Base('db/bid.pdl')
if bid.exists():
    bid.open()
else:
    bid.create('user_id', 'event', 'number_tickets')

