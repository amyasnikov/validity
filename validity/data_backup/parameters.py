from pydantic import BaseModel


class GitParams(BaseModel):
    username: str
    password: str
    branch: str | None = None


class S3Params(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    archive: bool
