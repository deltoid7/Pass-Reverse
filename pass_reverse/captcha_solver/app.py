from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
import captcha_cracker_ll as cc
import uvicorn

app = FastAPI()

img_width = 140
img_height = 40
max_length = 6
characters = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
weights_path = "model/weights.weights.h5"
AM = None

def load_model():
    global AM
    if AM is None:
        AM = cc.ApplyModel(weights_path, img_width, img_height, max_length, characters)

@app.on_event("startup")
async def startup_event():
    load_model()

@app.get("/")
async def root():
    if AM is None:
        return JSONResponse({
            "status": "모델이 로드되지 않았습니다",
            "model_loaded": False
        })
    else:
        return JSONResponse({
            "status": "모델이 활성화되어 있습니다",
            "model_loaded": True,
            "model_info": {
                "img_width": img_width,
                "img_height": img_height,
                "max_length": max_length,
                "characters": sorted(list(characters)),
                "weights_path": weights_path
            }
        })

def convert_transparent_to_white(captcha_bytes):
    img = Image.open(BytesIO(captcha_bytes))
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    output = BytesIO()
    img.save(output, 'PNG')
    return output.getvalue()

@app.post("/predict")
async def predict_captcha(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        processed_image = convert_transparent_to_white(contents)
        if AM is None:
            load_model()
        pred = AM.predict_from_bytes(processed_image)
        return JSONResponse({
            "success": True,
            "number": pred,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
