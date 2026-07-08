from fastapi import FastAPI

app = FastAPI()

@app.post("/predict")
async def predict(data: dict):
    text = data["input"]

    if "love" in text.lower():
        return {
            "prediction": "positive",
            "confidence": 0.98
        }

    return {
        "prediction": "negative",
        "confidence": 0.81
    }