import databases
import sqlalchemy
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import urllib

app = FastAPI()

host_server = os.environ.get("host_server", "localhost")
db_server_port = urllib.parse.quote_plus(str(os.environ.get("db_server_port", "5432")))
database_name = os.environ.get("database_name", "fastdata")
db_username = urllib.parse.quote_plus(str(os.environ.get("db_username", "postgres")))
db_password = urllib.parse.quote_plus(str(os.environ.get("db_password", "root")))
ssl_mode = urllib.parse.quote_plus(str(os.environ.get("ssl_mode", "prefer")))
DATABASE_URL = "postgresql://{}:{}@{}:{}/{}?sslmode={}".format(
    db_username, db_password, host_server, db_server_port, database_name, ssl_mode
)

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

address = sqlalchemy.Table(
    "address",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("address", sqlalchemy.String),
)

engine = sqlalchemy.create_engine(DATABASE_URL, pool_size=3, max_overflow=0)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Address(BaseModel):
    id = int
    name = str
    address = str


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Adding the address to database
@app.post("/add_address/", response_model=Address, status_code=status.HTTP_201_CREATED)
async def create_address(address=Address):
    query = Address(name=address.name, address=address.address)
    await database.execute(query)
    return {**address.dict()}


# Getting the address from database
@app.get("/get_address/", response_model=Address, status_code=status.HTTP_200_OK)
async def read_address():
    #import pdb
    #pdb.set_trace()
    query = address.select()
    return await database.fetch_all(query)


# Updating the address in database
@app.put(
    "/update_address/{address_id}/",
    response_model=Address,
    status_code=status.HTTP_200_OK,
)
async def update_address(address_id: int, payload: Address):
    query = (
        address.update()
        .where(address.c.id == address_id)
        .values(name=payload.name, address=payload.address)
    )
    await database.execute(query)
    return {**payload.dict(), "id": address_id}


# Deleting the address from database
@app.delete("/delete_address/{address_id}/", status_code=status.HTTP_200_OK)
async def delete_address(address_id: int):
    query = address.delete().where(address.c.id == address_id)
    await database.execute(query)
    return {"message": "Address with id: {} deleted successfully!".format(address_id)}