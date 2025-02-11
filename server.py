from fastapi import FastAPI, UploadFile
from libs.super_brain import SuperBrain
from libs.memories.sematic_memory import SEMANTIC_MEMORY_TYPE
from pydantic import BaseModel

app = FastAPI()


class Params(BaseModel):
    question: str
    iteration: int = 1


@app.post("/")
def think(question: Params):
    super_brain = SuperBrain(include_semetic_memory=True)
    answer = super_brain.think(question.question)
    return {"message": answer}


@app.post("/core_knowledge")
async def insert(file: UploadFile):
    try:
        # Create file path in /tmp directory
        file_path = f"./tmp/{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        super_brain = SuperBrain(include_semetic_memory=True)
        super_brain.insert(file_path, SEMANTIC_MEMORY_TYPE.CORE_KNOWLEDGE)

        return {"message": f"File uploaded successfully to {file_path}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/domain_knowledge")
async def insert(file: UploadFile):
    try:
        # Create file path in /tmp directory
        file_path = f"./tmp/{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        super_brain = SuperBrain(include_semetic_memory=True)
        super_brain.insert(
            file_path, SEMANTIC_MEMORY_TYPE.DOMAIN_SPECIFIC_KNOWLEDGE)

        return {"message": f"File uploaded successfully to {file_path}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/company_knowledge")
async def insert(file: UploadFile):
    try:
        # Create file path in /tmp directory
        file_path = f"./tmp/{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        super_brain = SuperBrain(include_semetic_memory=True)
        super_brain.insert(file_path, SEMANTIC_MEMORY_TYPE.COMPANY_KNOWLEDGE)

        return {"message": f"File uploaded successfully to {file_path}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/personal_knowledge")
async def insert(file: UploadFile):
    try:
        # Create file path in /tmp directory
        file_path = f"./tmp/{file.filename}"

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        super_brain = SuperBrain(include_semetic_memory=True)
        await super_brain.insert(file_path, SEMANTIC_MEMORY_TYPE.PERSONAL_KNOWLEDGE)

        return {"message": f"File uploaded successfully to {file_path}"}
    except Exception as e:
        return {"error": str(e)}
