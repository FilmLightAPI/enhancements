"""Download the model weights into ./weights before installing or packaging the effect."""
import hashlib
import http.client
import os
import shutil
import ssl
import sys
import urllib.request

URL = 'https://download.pytorch.org/models/deeplabv3_mobilenet_v3_large-fc3c493d.pth'
SHA256 = 'fc3c493d68e89cc31ef488c803d5d7dd2f3190fb570598faa49fef69be8e5e70'
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weights', 'deeplabv3_mobilenet_v3_large.pth')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


if os.path.exists(DEST) and sha256(DEST) == SHA256:
    print(f'{DEST} is already downloaded')
    sys.exit(0)
os.makedirs(os.path.dirname(DEST), exist_ok=True)
print(f'Downloading {URL}')
try:
    import certifi
    context = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    context = ssl.create_default_context()
try:
    with urllib.request.urlopen(URL, context=context, timeout=60) as response, open(DEST + '.part', 'wb') as f:
        shutil.copyfileobj(response, f)
except urllib.error.URLError as e:
    if os.path.exists(DEST + '.part'):
        os.remove(DEST + '.part')
    hint = ''
    if isinstance(e.reason, ssl.SSLError):
        hint = (' With the python.org Python on macOS, run its "Install Certificates.command", or run this '
                'script with the Flexi platform\'s Python.')
    sys.exit(f'Download failed: {e.reason}.{hint}')
except (OSError, http.client.HTTPException) as e:
    if os.path.exists(DEST + '.part'):
        os.remove(DEST + '.part')
    sys.exit(f'Download failed: {e}')
if sha256(DEST + '.part') != SHA256:
    os.remove(DEST + '.part')
    sys.exit(f'{URL} does not have the expected checksum')
os.replace(DEST + '.part', DEST)
print(f'Saved {DEST}')
