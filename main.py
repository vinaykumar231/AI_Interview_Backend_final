from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from api.endpoints import (user_router,resume_router,report_router,student_resume_upload_router,student_report_router, Business_Message_router,jobposting_router,jobapply_router,
                           apply_resume_analysis_router)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user_router, prefix="/api", tags=["user Routes"])
app.include_router(resume_router, prefix="/api", tags=["HR Routes"])
app.include_router(report_router, prefix="/api", tags=["HR Routes"])
app.include_router(jobposting_router, prefix="/api", tags=["HR Routes"])
app.include_router(student_resume_upload_router, prefix="/api", tags=["student Routes"])
app.include_router(student_report_router, prefix="/api", tags=["student Routes"])
app.include_router(Business_Message_router, prefix="/api", tags=["admin Routes"])
app.include_router(jobapply_router, prefix="/api", tags=["job apply Routes"])
app.include_router(apply_resume_analysis_router, prefix="/api", tags=["apply resume analysis Routes"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload= True, host="0.0.0.0")