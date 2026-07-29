import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

client = TestClient(app)

db = SessionLocal()
user = db.query(User).filter(User.email == 'uploader@example.com').first()
if user is None:
    raise SystemExit('no user found')

token = create_access_token(user.id)
files = {'file': ('test.txt', b'hello upload test', 'text/plain')}
resp = client.post('/api/v1/books/upload', files=files, headers={'Authorization': f'Bearer {token}'})
print(resp.status_code)
print(resp.text)
