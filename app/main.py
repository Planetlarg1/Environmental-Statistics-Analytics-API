from fastapi import FastAPI

# CONFIG
app = FastAPI(
    title="Environmental Statistics Analytics API",
    description="A RESTful API for environmental and climate statistics across cities.",
    version="0.1.0"
)

# ROUTES
# Root
@app.get("/")
def root():
    return {"message": "Running Environmental Statistics Analytics API"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}