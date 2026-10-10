from pathlib import Path
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .database import Base, migrar_esquema_sqlite, motor_banco_dados
from .routes import admin, api, require_admin
from .settings import configuracoes

app = FastAPI(title="Agenda Pereira & Monteiro", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)
if configuracoes.criar_tabelas:
    migrar_esquema_sqlite()
    Base.metadata.create_all(bind=motor_banco_dados)
app.include_router(api)
app.include_router(admin)
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=RAIZ_PROJETO / "TELA_LANDING_PAGE"), name="arquivos_estaticos")


@app.get("/", include_in_schema=False)
def exibir_pagina_inicial():
    return FileResponse(RAIZ_PROJETO / "TELA_LANDING_PAGE" / "lp.html")


@app.get("/politica-de-privacidade", include_in_schema=False)
def exibir_politica_de_privacidade():
    return FileResponse(RAIZ_PROJETO / "backend" / "privacy.html")


@app.get("/admin", include_in_schema=False, dependencies=[Depends(require_admin)])
def exibir_painel_administrativo():
    return FileResponse(RAIZ_PROJETO / "backend" / "admin.html")



app.mount("/", StaticFiles(directory=RAIZ_PROJETO / "TELA_LANDING_PAGE"), name="arquivos_frontend")
