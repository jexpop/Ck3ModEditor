import hashlib

def file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def get_holder_at_year(history, year):
    holder_list = history.get("holder", [])
    last = None
    for y, h in holder_list:
        if y <= year:
            last = h
        else:
            break
    return last
