import json, mimetypes, os, sqlite3, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
FILES = DATA / 'files'
FILES.mkdir(parents=True, exist_ok=True)
DB = DATA / 'assets.db'
MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {'image/jpeg', 'image/png', 'image/webp', 'video/mp4'}

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

with connect() as db:
    db.execute('CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, media_type TEXT NOT NULL, file_name TEXT NOT NULL, uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def body(self):
        size = int(self.headers.get('Content-Length', '0'))
        if size < 1 or size > ((MAX_BYTES + 2) // 3 * 4) + 1024 * 1024: raise ValueError('Request size exceeds limit')
        return json.loads(self.rfile.read(size))
    def get_asset(self, asset_id):
        with connect() as db: row = db.execute('SELECT * FROM assets WHERE id=?', (asset_id,)).fetchone()
        return dict(row) if row else None
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/assets':
            with connect() as db: rows = [dict(r) for r in db.execute('SELECT * FROM assets ORDER BY uploaded_at DESC')]
            return self.reply(200, rows)
        if path.startswith('/api/assets/'):
            row = self.get_asset(path.rsplit('/', 1)[-1]); return self.reply(200 if row else 404, row or {'error':'Not found'})
        if path.startswith('/media/'):
            asset_id = path.rsplit('/', 1)[-1]; row = self.get_asset(asset_id); file = FILES / asset_id
            if not row or not file.is_file(): return self.reply(404, {'error':'Not found'})
            content = file.read_bytes(); self.send_response(200); self.send_header('Content-Type', row['media_type']); self.send_header('Content-Length', str(len(content))); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(content); return
        static = {'/':'index.html', '/app.js':'app.js', '/style.css':'style.css'}.get(path)
        if not static: return self.reply(404, {'error':'Not found'})
        file = ROOT / 'static' / static; content = file.read_bytes(); self.send_response(200); self.send_header('Content-Type', (mimetypes.guess_type(file.name)[0] or 'text/plain') + '; charset=utf-8'); self.send_header('Content-Length', str(len(content))); self.end_headers(); self.wfile.write(content)
    def do_POST(self):
        if urlparse(self.path).path != '/api/assets': return self.reply(404, {'error':'Not found'})
        import base64, binascii
        try:
            data = self.body(); title = str(data.get('title','')).strip(); description = str(data.get('description','')).strip(); media_type = data.get('mediaType'); name = str(data.get('fileName',''))
            if not title or len(title)>120 or len(description)>2000 or media_type not in ALLOWED: raise ValueError('Invalid metadata or file type')
            raw = base64.b64decode(data.get('content',''), validate=True)
            if not raw or len(raw)>MAX_BYTES: raise ValueError('File must be between 1 byte and 10 MB')
            asset_id = str(uuid.uuid4()); file = FILES / asset_id
            file.write_bytes(raw)
            try:
                with connect() as db: db.execute('INSERT INTO assets(id,title,description,media_type,file_name) VALUES(?,?,?,?,?)', (asset_id,title,description,media_type,name[:255]))
            except Exception:
                file.unlink(missing_ok=True); raise
            return self.reply(201, self.get_asset(asset_id))
        except (ValueError, TypeError, binascii.Error, json.JSONDecodeError) as e: return self.reply(400, {'error':str(e)})
    def do_PUT(self):
        path = urlparse(self.path).path
        if not path.startswith('/api/assets/'): return self.reply(404, {'error':'Not found'})
        asset_id = path.rsplit('/',1)[-1]
        try:
            data = self.body(); title = str(data.get('title','')).strip(); desc = str(data.get('description','')).strip()
            if not title or len(title)>120 or len(desc)>2000: raise ValueError('Invalid metadata')
            with connect() as db: count = db.execute('UPDATE assets SET title=?,description=? WHERE id=?',(title,desc,asset_id)).rowcount
            return self.reply(200 if count else 404, self.get_asset(asset_id) if count else {'error':'Not found'})
        except (ValueError, TypeError, json.JSONDecodeError) as e: return self.reply(400, {'error':str(e)})
    def do_DELETE(self):
        path = urlparse(self.path).path
        if not path.startswith('/api/assets/'): return self.reply(404, {'error':'Not found'})
        asset_id = path.rsplit('/',1)[-1]
        with connect() as db: count = db.execute('DELETE FROM assets WHERE id=?',(asset_id,)).rowcount
        if not count: return self.reply(404, {'error':'Not found'})
        (FILES / asset_id).unlink(missing_ok=True)
        return self.reply(200, {'deleted':asset_id})

if __name__ == '__main__':
    print('Travel Journal: http://127.0.0.1:8000', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
