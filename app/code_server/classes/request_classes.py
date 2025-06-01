import sys
import uuid
import base64
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field


EXECUTION_ENVS = [
    'python',
    'python_scientific',
    'bash',
    'java',
    'javascript'
]


class FileReturn(BaseModel):
    filename: str = Field(..., description="The name of the file")
    content: str | bytes = Field(..., description="The (optionally Base64) encoded content of the file")

    @computed_field
    @property
    def base64encoded(self) -> bool:
        if isinstance(self.content, bytes):
            return True

        try:
            base64.b64decode(self.content.encode())
            return True

        except Exception as e:
            return False

    @model_validator(mode='after')
    def check_content(self) -> 'FileReturn':
        if isinstance(self.content, bytes):
            try:
                self.content = base64.b64encode(self.content).decode('utf-8')
            except Exception as e:
                raise ValueError(f"Unable to Base64 encode content: {e}")
        else:
            self.content = str(self.content)

        return self


class FileUpload(BaseModel):
    filename: str = Field(..., description="The name of the file")
    extension: str = Field(..., description="The extension of the file")
    content: str = Field(..., description="The(optionally Base64) encoded content of the file")
    base64encoded: bool = Field(..., description="Whether the content is Base64 encoded")

    @computed_field
    @property
    def file_id(self) -> str:
        return uuid.uuid4().hex

    @computed_field
    @property
    def decoded_content(self) -> bytes:
        if self.base64encoded:
            try:
                return base64.b64decode(self.content.encode())
            except Exception as e:
                raise ValueError(f"Invalid Base64 content: {e}")
        else:
            return self.content.encode()

    @computed_field
    @property
    def file_size(self) -> int:
        return sys.getsizeof(self.decoded_content)

    @computed_field
    @property
    def full_filename(self) -> str:
        return f"{self.filename}.{self.extension}"


class CodeRequest(BaseModel):
    code: str = Field(..., description="The python code to be executed")
    files: List[FileUpload] | None = Field(None, description="The files to be used in the code execution")
    timeout: int = Field(default=60, description="The timeout for the code execution in seconds")
    execution_environment: str | None = Field(default='python', description="The execution environment to use for the code execution")
    packages: List[str] | None = Field(None, description="Optional list of packages to be installed in the execution environment")
    user: str = Field(..., description="The user who is executing the code")

    @computed_field
    @property
    def request_date(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @computed_field
    @property
    def request_id(self) -> str:
        return uuid.uuid4().hex

    @field_validator('timeout')
    def check_timeout(cls, v):
        if v <= 1:
            raise ValueError("Timeout must be greater than 1")

        if v > 120:
            raise ValueError("Timeout must be less than 120")

        return v

    @field_validator('files')
    def check_files(cls, v):
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError("Files must be a list")

        if len(v) == 0:
            raise ValueError("Files must not be empty")

        if isinstance(v, list):
            total_size = 0
            for file in v:
                if not isinstance(file, FileUpload):
                    raise ValueError("Files must be FileUpload objects")
                total_size += file.file_size

            if total_size > 100 * 1024 * 1024:
                raise ValueError("Total size of files must not exceed 100MB")

        return v

    @model_validator(mode='after')
    def check_environment(self) -> 'CodeRequest':
        if self.execution_environment is None:
            raise ValueError("Execution environment must be specified")
        else:
            self.execution_environment = self.execution_environment.lower()

        if self.execution_environment not in EXECUTION_ENVS:
            raise ValueError(f"Invalid execution environment: {self.execution_environment}")

        return self


class CodeResponse(BaseModel):
    output: str | None = Field(..., description="The standard output of the code execution")
    error: str | bool | None = Field(..., description="The standard error of the code execution")
    timedout: bool = Field(..., description="Whether the code execution timed out")
    files: List[FileReturn] | None | List[None] | List[dict[str, str]] = Field(..., description="The files to be returned from the code execution")
    stacktrace: str | None = Field(..., description="The stacktrace of the code execution")
