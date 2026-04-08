from pydantic import BaseModel


class ParseFileRequest(BaseModel):
    file_url: str


class ParseTextRequest(BaseModel):
    travelPlan: str