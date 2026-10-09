import json
import os
from urllib.request import Request, urlopen


def update_document(document_id: str, **fields) -> None:
    base = os.environ["BACKEND_URL"].rstrip("/")
    request = Request(
        f"{base}/documents/{document_id}",
        data=json.dumps(fields).encode(),
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request):
        return
