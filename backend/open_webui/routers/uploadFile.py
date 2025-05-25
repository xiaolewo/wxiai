from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
from datetime import datetime
import uuid
import base64
from pydantic import BaseModel

app = FastAPI()

# 配置上传文件夹和允许的扩展名
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 挂载静态文件目录用于访问上传的文件
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


class FeedbackRequest(BaseModel):
    content: str
    contact: Optional[str] = None
    images: Optional[List[str]] = None


class ImageUploadRequest(BaseModel):
    file: str  # base64编码的图片数据
    filename: Optional[str] = None


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


router = APIRouter()


@router.post("/upload_image")
async def upload_image(request: Request, data: ImageUploadRequest):
    try:
        # 验证文件类型
        filename = data.filename or f"upload_{uuid.uuid4().hex[:8]}"
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="File type not allowed")

        # 解码Base64数据
        file_data = data.file
        if "," in file_data:
            file_data = file_data.split(",")[1]
        file_content = base64.b64decode(file_data)

        # 生成安全的文件名
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "png"
        safe_filename = (
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        )
        save_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        # 保存文件
        with open(save_path, "wb") as f:
            f.write(file_content)

        # 返回访问URL
        file_url = f"{request.base_url}uploads/{safe_filename}"

        return JSONResponse(
            {
                "code": 200,
                "message": "File uploaded successfully",
                "data": {"url": file_url, "filename": safe_filename},
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.post("/api/v1/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    # 处理反馈数据（实际项目中应该存入数据库）
    feedback_data = {
        "content": feedback.content,
        "contact": feedback.contact or "",
        "images": feedback.images or [],
        "created_at": datetime.now().isoformat(),
    }

    # 这里可以添加数据库存储逻辑
    # await save_to_database(feedback_data)

    return JSONResponse(
        {
            "status": "success",
            "message": "Feedback submitted successfully",
            "data": feedback_data,
        }
    )


# 文件上传替代方案（使用multipart/form-data）
@app.post("/api/v2/upload")
async def upload_file(file: UploadFile = File(...)):
    if not allowed_file(file.filename):
        raise HTTPException(400, detail="Invalid file type")

    ext = file.filename.split(".")[-1]
    filename = (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    )
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"filename": filename}
