from __future__ import annotations

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent

MERCHANTS: list[dict] = []
COMMUNITIES: list[dict] = []
POSTS: list[dict] = []


def _next_id(items: list[dict]) -> int:
    return max((item["id"] for item in items), default=0) + 1


def _json_response(handler: BaseHTTPRequestHandler, status: int, data: dict | list):
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _text_response(handler: BaseHTTPRequestHandler, status: int, content: str, content_type: str):
    payload = content.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body) if body else {}


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            return self._serve_template("index.html")
        if path == "/admin":
            return self._serve_template("admin.html")
        if path.startswith("/static/"):
            return self._serve_static(path.replace("/static/", "", 1))

        if path == "/api/merchants":
            query = parse_qs(parsed.query)
            city = query.get("city", [None])[0]
            category = query.get("category", [None])[0]
            data = MERCHANTS
            if city:
                data = [m for m in data if m["city"] == city]
            if category:
                data = [m for m in data if m["category"] == category]
            return _json_response(self, 200, data)

        if path == "/api/communities":
            return _json_response(self, 200, COMMUNITIES)

        if path == "/api/posts":
            query = parse_qs(parsed.query)
            community_id = query.get("community_id", [None])[0]
            data = POSTS
            if community_id:
                data = [p for p in POSTS if p["community_id"] == int(community_id)]
            return _json_response(self, 200, data)

        if path == "/api/admin/analytics":
            merchant_categories: dict[str, int] = {}
            for merchant in MERCHANTS:
                merchant_categories[merchant["category"]] = merchant_categories.get(merchant["category"], 0) + 1

            member_counts = [len(c["members"]) for c in COMMUNITIES]
            avg_members = round(sum(member_counts) / len(member_counts), 2) if member_counts else 0

            top_communities = sorted(
                [
                    {
                        "community_id": c["id"],
                        "community_name": c["name"],
                        "members": len(c["members"]),
                    }
                    for c in COMMUNITIES
                ],
                key=lambda x: x["members"],
                reverse=True,
            )[:5]

            data = {
                "kpis": {
                    "merchant_count": len(MERCHANTS),
                    "community_count": len(COMMUNITIES),
                    "post_count": len(POSTS),
                    "avg_community_members": avg_members,
                },
                "merchant_categories": merchant_categories,
                "top_communities": top_communities,
            }
            return _json_response(self, 200, data)

        return _json_response(self, 404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/merchants":
            payload = _read_json(self)
            required = ["name", "category", "contact", "city"]
            missing = [field for field in required if not payload.get(field)]
            if missing:
                return _json_response(self, 400, {"error": f"missing fields: {', '.join(missing)}"})

            merchant = {
                "id": _next_id(MERCHANTS),
                "name": payload["name"],
                "category": payload["category"],
                "contact": payload["contact"],
                "city": payload["city"],
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            MERCHANTS.append(merchant)
            return _json_response(self, 201, merchant)

        if path == "/api/communities":
            payload = _read_json(self)
            required = ["name", "owner", "description"]
            missing = [field for field in required if not payload.get(field)]
            if missing:
                return _json_response(self, 400, {"error": f"missing fields: {', '.join(missing)}"})

            community = {
                "id": _next_id(COMMUNITIES),
                "name": payload["name"],
                "owner": payload["owner"],
                "description": payload["description"],
                "members": [payload["owner"]],
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            COMMUNITIES.append(community)
            return _json_response(self, 201, community)

        if path.startswith("/api/communities/") and path.endswith("/join"):
            payload = _read_json(self)
            username = payload.get("username")
            if not username:
                return _json_response(self, 400, {"error": "username is required"})

            try:
                community_id = int(path.split("/")[3])
            except (IndexError, ValueError):
                return _json_response(self, 400, {"error": "invalid community id"})

            community = next((c for c in COMMUNITIES if c["id"] == community_id), None)
            if not community:
                return _json_response(self, 404, {"error": "community not found"})

            if username not in community["members"]:
                community["members"].append(username)
            return _json_response(self, 200, community)

        if path == "/api/posts":
            payload = _read_json(self)
            required = ["community_id", "author", "content"]
            missing = [field for field in required if not payload.get(field)]
            if missing:
                return _json_response(self, 400, {"error": f"missing fields: {', '.join(missing)}"})

            try:
                community_id = int(payload["community_id"])
            except ValueError:
                return _json_response(self, 400, {"error": "community_id must be integer"})

            community = next((c for c in COMMUNITIES if c["id"] == community_id), None)
            if not community:
                return _json_response(self, 404, {"error": "community not found"})

            if payload["author"] not in community["members"]:
                return _json_response(self, 400, {"error": "author is not a member of this community"})

            post = {
                "id": _next_id(POSTS),
                "community_id": community_id,
                "author": payload["author"],
                "content": payload["content"],
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
            POSTS.append(post)
            return _json_response(self, 201, post)

        return _json_response(self, 404, {"error": "not found"})

    def _serve_template(self, name: str):
        file_path = BASE_DIR / "templates" / name
        if not file_path.exists():
            return _json_response(self, 404, {"error": "template not found"})
        return _text_response(self, 200, file_path.read_text(encoding="utf-8"), "text/html; charset=utf-8")

    def _serve_static(self, relative_name: str):
        file_path = BASE_DIR / "static" / relative_name
        if not file_path.exists() or not file_path.is_file():
            return _json_response(self, 404, {"error": "static file not found"})

        if relative_name.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif relative_name.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        else:
            content_type = "text/plain; charset=utf-8"
        return _text_response(self, 200, file_path.read_text(encoding="utf-8"), content_type)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
