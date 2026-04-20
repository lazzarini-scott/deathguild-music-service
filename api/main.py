from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.playlists import router as playlists_router
from api.v1.songs import router as songs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Deathguild API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(playlists_router, prefix="/v1")
app.include_router(songs_router, prefix="/v1")
