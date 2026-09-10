from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok", "message": "IP probe running. Hit /probe from your mobile on cellular."}

@app.get("/probe")
async def probe(request: Request):
    # Capture IP — check X-Forwarded-For first (Railway sets this)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    port = request.client.port

    # Enrich with ip-api.com (free, no key, 45 req/min limit)
    geo = {}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,message,country,regionName,city,isp,org,as,query"},
                timeout=5.0
            )
            geo = resp.json()
    except Exception as e:
        geo = {"error": str(e)}

    return {
        "captured": {
            "ip": ip,
            "port": port,
            "x_forwarded_for": forwarded_for,
        },
        "geo": {
            "ip_confirmed": geo.get("query"),
            "city": geo.get("city"),
            "region": geo.get("regionName"),
            "country": geo.get("country"),
            "isp": geo.get("isp"),
            "org": geo.get("org"),
            "asn": geo.get("as"),
        },
        "raw_headers": {
            "user_agent": request.headers.get("user-agent"),
            "accept_language": request.headers.get("accept-language"),
        }
    }
