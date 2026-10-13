"""Bounded private-interface transfer of only the approved public Qwen snapshot.

No directory listing or arbitrary path access. Serves one tar response, then exits.
Both source and destination must separately pass the registered SHA manifest.
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import tarfile

ASSET = Path('/mnt/data0601/yangjinyue/new_SCII/assets/Qwen3-4B-Instruct-2507-cdbee75')
FILES = ('LICENSE', 'README.md', 'config.json', 'generation_config.json', 'merges.txt',
         'model-00001-of-00003.safetensors', 'model-00002-of-00003.safetensors',
         'model-00003-of-00003.safetensors', 'model.safetensors.index.json',
         'tokenizer.json', 'tokenizer_config.json', 'vocab.json')


class Snapshot(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/qwen-original.tar':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-tar')
        self.end_headers()
        with tarfile.open(fileobj=self.wfile, mode='w|') as archive:
            for name in FILES:
                archive.add(ASSET/name, arcname=name, recursive=False)

    def log_message(self, *args):
        pass  # no request headers or network addresses in saved experiment logs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', required=True)
    args = parser.parse_args()
    if not args.bind.startswith('172.16.'):
        raise ValueError('This transfer must bind only the observed private interface')
    for name in FILES:
        if not (ASSET/name).is_file() or (ASSET/name).is_symlink():
            raise RuntimeError('Registered regular snapshot file missing: ' + name)
    with HTTPServer((args.bind, 43192), Snapshot) as server:
        server.timeout = 90
        print('READY one approved snapshot, one response', flush=True)
        server.handle_request()
