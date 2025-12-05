from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "ERP Talento Humano API funcionando 👍"}

