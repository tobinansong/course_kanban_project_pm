from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/api/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/", response_class=HTMLResponse)
    def read_root() -> HTMLResponse:
        return HTMLResponse(
            """
            <!doctype html>
            <html lang=\"en\">
              <head>
                <meta charset=\"utf-8\" />
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
                <title>PM App - Build Required</title>
                <style>
                  :root {
                    color-scheme: light;
                    font-family: "Segoe UI", system-ui, sans-serif;
                    background: #f7f8fb;
                    color: #032147;
                  }
                  body {
                    margin: 0;
                    padding: 40px;
                  }
                  .card {
                    max-width: 640px;
                    background: #ffffff;
                    border-radius: 20px;
                    padding: 24px;
                    box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
                  }
                  h1 {
                    margin: 0 0 8px;
                    font-size: 28px;
                  }
                  p {
                    margin: 0 0 12px;
                    color: #888888;
                  }
                  code {
                    display: inline-block;
                    padding: 2px 6px;
                    background: #eef2f7;
                    border-radius: 6px;
                    color: #032147;
                  }
                </style>
              </head>
              <body>
                <div class=\"card\">
                  <h1>Frontend build not found</h1>
                  <p>Build the frontend to generate static assets.</p>
                  <p>Expected folder: <code>backend/app/static</code></p>
                </div>
              </body>
            </html>
            """
        )
