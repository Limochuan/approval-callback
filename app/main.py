from fastapi import FastAPI
from app.routes.approval import router as approval_router

app = FastAPI(title="Approval Callback Service")

app.include_router(approval_router)

@app.get("/")
def health_check():
    return {"status": "ok"}
