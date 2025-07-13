import argparse
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


import datastore
from model import RoomThempSet


def init_store(store_path: str):
    datastore.store = datastore.FileStore(store_path)


def get_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = get_app()


@app.get('/')
async def read_themp(room: str) -> RoomThempSet:
    try:
        return datastore.store.get_room_info(room)
    except ValueError:
        raise fastapi.HTTPException(status_code=404, detail='Room not found')


@app.post('/')
async def update_themp(room: str, data: RoomThempSet) -> RoomThempSet:
    return datastore.store.save_room_info(room, data)


@app.get('/full')
async def full_data():
    return datastore.store.data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--store-path', default='/config/www/climate_store.json')
    args = parser.parse_args()
    init_store(args.store_path)
    uvicorn.run("main:app", host='0.0.0.0', port=5000, log_level="info")


if __name__ == '__main__':
    main()

