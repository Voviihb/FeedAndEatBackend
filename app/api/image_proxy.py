from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()

# Разрешённые хосты — только те, откуда у нас реально берутся картинки
ALLOWED_HOSTS = {
    "img.spoonacular.com",
    "spoonacular.com",
    "images.spoonacular.com",
}

_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)


@router.get("/image-proxy")
async def image_proxy(url: str = Query(..., description="Абсолютный URL изображения")):
    """
    Проксирует изображение по указанному URL через сервер.
    Используется для обхода проблем с доступностью внешних CDN на устройствах клиентов.
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        raise HTTPException(status_code=400, detail=f"Host '{parsed.hostname}' not allowed")

    try:
        resp = await _client.get(url, headers={"User-Agent": "FeedAndEat/1.0"})
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Upstream returned non-200")

    content_type = resp.headers.get("content-type", "image/jpeg")
    return Response(content=resp.content, media_type=content_type)
