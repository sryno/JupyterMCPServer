import os
import base64
import tempfile
import traceback
import urllib.parse
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
from fastapi_mcp import FastApiMCP
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from code_server.utils import logger_setup
from code_server.utils.auth import get_user
from code_server.utils.file_utils import lifespan, FILES_DIR
from code_server.classes import request_classes
from code_server.jupyter.JupyterClient import JupyterNotebook, JupyterKernels


logger_setup.configure_logging()
logger = logger_setup.get_logger()


# Load environment variables from .env file
load_dotenv()

HOST = "127.0.0.1"
PORT = "8080"


tags_metadata = [
    {
        "name": "Code Execution",
        "description": "Execute code in a sandboxed environment",
    },
    {
        "name": "File Management",
        "description": "Manage files in the sandboxed environment",
    },
    {
        "name": "Health Check",
        "description": "Check the health of the server",
    },
    {
        "name": "Logging",
        "description": "Get the logs of the server",
    },
]


app = FastAPI(
    title="Code Execution API",
    description="API for executing code in a sandboxed environment",
    version="0.1.0",
    lifespan=lifespan
)
app.mount("/jupyter/files", StaticFiles(directory=FILES_DIR), name="files")
jk = JupyterKernels()


@app.get(
    "/jupyter/",
    tags=["Health Check"],
    operation_id="root",
    summary="Root endpoint",
    description="Returns a welcome message",
)
async def root():
    """Root endpoint that returns a welcome message.
    
    Returns:
        dict: A dictionary containing a welcome message.
    """
    return {"message": "Hello and Welcome to the Code Execution API"}


@app.get(
    "/jupyter/health",
    tags=["Health Check"],
    operation_id="health_check",
    summary="Check the health of the server",
    description="Returns the health status of the server",
)
async def health_check() -> dict[str, str]:
    """Check the health status of the server.
    
    Returns:
        dict[str, str]: A dictionary containing the server status.
    """
    return {"status": "ok"}


@app.put(
    "/jupyter/files",
    tags=["File Management"],
    operation_id="upload_file",
    summary="Upload a file to the server",
    description="Uploads a file to the server and returns the URL of the uploaded file. The file lives for 20 minutes.",
)
async def upload_file(request: Request, inp: request_classes.FileUpload, user: dict=Depends(get_user)) -> dict:
    """Upload a file to the server.
    
    Args:
        request (Request): The FastAPI request object.
        inp (request_classes.FileUpload): The file upload request containing filename, extension and content.
        user (dict, optional): The authenticated user information. Defaults to Depends(get_user).
    
    Returns:
        dict: A dictionary containing the URL of the uploaded file.
        
    Raises:
        HTTPException: If an error occurs during file upload.
    """
    logger.info("#" * 40)
    logger.info(f"Request to upload file")
    logger.info(f"Received Request at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Request Client IP: {request.client.host}")
    logger.info(f"API Request User: {user}")
    logger.info("#" * 40)

    try:
        uuid = uuid4().hex
        file_name = f"{inp.filename}-{uuid}.{inp.extension}"
        safe_file_name = urllib.parse.quote(file_name)
        file_path = os.path.join("/files", safe_file_name)
        with open(file_path, "wb") as f:
            _ = f.write(inp.decoded_content)

        return {"url": f"http://{HOST}:{PORT}/jupyter{file_path}"}

    except Exception as e:
        # Handle any exceptions that occur during execution
        raise HTTPException(400, {"error": f"An error occurred: {str(e)}", "stacktrace": traceback.format_exc()})


@app.put(
    "/jupyter/files/long-lifetime",
    tags=["File Management"],
    operation_id="upload_long_life_file",
    summary="Upload a file with extended lifetime to the server",
    description="Uploads a file to the server and returns the URL of the uploaded file. The file lives for 2 days."
)
async def upload_long_life_file(request: Request, inp: request_classes.FileUpload, user: dict=Depends(get_user)) -> dict:
    """Upload a file with extended lifetime to the server.
    
    Args:
        request (Request): The FastAPI request object.
        inp (request_classes.FileUpload): The file upload request containing filename, extension and content.
        user (dict, optional): The authenticated user information. Defaults to Depends(get_user).
    
    Returns:
        dict: A dictionary containing the URL of the uploaded file.
        
    Raises:
        HTTPException: If an error occurs during file upload.
    """
    logger.info("#" * 40)
    logger.info(f"Request to upload long life file")
    logger.info(f"Received Request at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Request Client IP: {request.client.host}")
    logger.info(f"API Request User: {user}")
    logger.info("#" * 40)

    try:
        uuid = uuid4().hex
        file_name = f"{inp.filename}-long-{uuid}.{inp.extension}"
        safe_file_name = urllib.parse.quote(file_name)
        file_path = os.path.join("/files", safe_file_name)
        with open(file_path, "wb") as f:
            _ = f.write(inp.decoded_content)

        return {"url": f"http://{HOST}:{PORT}/jupyter{file_path}"}

    except Exception as e:
        # Handle any exceptions that occur during execution
        raise HTTPException(400, {"error": f"An error occurred: {str(e)}", "stacktrace": traceback.format_exc()})


@app.get(
    "/jupyter/list_kernel_specs",
    tags=["Code Execution"],
    operation_id="list_kernel_specs",
    summary="List available Jupyter kernel specifications",
    description="Returns a list of available Jupyter kernel specifications"
)
async def list_kernel_specs(request: Request, user: dict=Depends(get_user)) -> dict:
    """List available Jupyter kernel specifications.
    
    Args:
        request (Request): The FastAPI request object.
        user (dict, optional): The authenticated user information. Defaults to Depends(get_user).
    
    Returns:
        dict: A dictionary containing available kernel specifications or error information.
    """
    logger.info("#" * 40)
    logger.info(f"Request for available kernels")
    logger.info(f"Received Request at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Request Client IP: {request.client.host}")
    logger.info(f"API Request User: {user}")
    logger.info("#" * 40)
    try:
        envs = jk.ks
        envs = {k: v for k, v in envs.items() if k != "python3"}

        return envs

    except Exception as e:
        # Handle any exceptions that occur during execution
        return {"error": f"An error occurred: {str(e)}", "stacktrace": traceback.format_exc()}


@app.post(
    "/jupyter/execute",
    tags=["Code Execution"],
    response_model=request_classes.CodeResponse,
    operation_id="execute_code",
    summary="Execute code in a sandboxed environment",
    description="Executes code in a sandboxed environment and returns the output, errors, files, etc."
)
async def execute_code(request: Request, inp: request_classes.CodeRequest, user: dict=Depends(get_user)) -> request_classes.CodeResponse:
    """Execute code in a Jupyter kernel.
    
    Args:
        request (Request): The FastAPI request object.
        inp (request_classes.CodeRequest): The code execution request containing code, environment, timeout, etc.
        user (dict, optional): The authenticated user information. Defaults to Depends(get_user).
    
    Returns:
        request_classes.CodeResponse: The execution response containing output, errors, files, etc.
    """
    logger.info("#" * 40)
    logger.info(f"Request to execute code")
    logger.info(f"Received Request at {inp.request_date}")
    logger.info(f"API Request User: {user}")
    logger.info(f"Request User: {inp.user}")
    logger.info(f"Request Client IP: {request.client.host}")
    logger.info(f"Request ID: {inp.request_id}")
    logger.info(f"Execution environment: {inp.execution_environment}")
    logger.info(f"Execution Timeout: {inp.timeout}")
    logger.info("#" * 40)

    cwd = os.getcwd()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            logger.info(f"Running code in tempdir: {tmpdir}")

            code_blob = inp.code
            timeout = inp.timeout
            kernel_name = inp.execution_environment

            # If base environment is used then raise an exception
            if kernel_name == 'python3':
                return request_classes.CodeResponse(
                    output=None,
                    error="Base environment is not supported for code execution",
                    timedout=False,
                    files=None,
                    stacktrace=None
                )

            if code_blob != "":
                install_packages = inp.packages
                nb = JupyterNotebook(kernel_name=kernel_name)
                if install_packages:
                    if 'python' in kernel_name.lower():
                        logger.info("Installing additional python packages")
                        pkg_resp = nb.install_python_packages(install_packages, timeout=timeout)
                        if pkg_resp:
                            return request_classes.CodeResponse(
                                output=None,
                                error=pkg_resp[0],
                                timedout=pkg_resp[1],
                                files=None,
                                stacktrace=pkg_resp[2]
                            )
                    elif 'javascript' in kernel_name.lower():
                        logger.info("Installing additional javascript packages")
                        pkg_resp = nb.install_npm_packages(install_packages, timeout=timeout)
                        if pkg_resp:
                            return request_classes.CodeResponse(
                                output=None,
                                error=pkg_resp[0],
                                timedout=pkg_resp[1],
                                files=None,
                                stacktrace=pkg_resp[2]
                            )
                    else:
                        return request_classes.CodeResponse(
                            output=None,
                            error=f"Installations of additional packages is not supported for kernel {kernel_name}",
                            timedout=False,
                            files=None,
                            stacktrace=None
                        )

                logger.info("Running code")
                out, error, files, timedout = nb.run_cell(code_blob, timeout)

                if files:
                    file_urls = []
                    for file in files:
                        file_path = f"/files/{'.'.join(file['file'].split('.')[:-1])}-{uuid4().hex}.{file['file'].split('.')[-1]}"
                        with open(file_path, "wb") as f:
                            _ = f.write(base64.b64decode(file['content'].encode()))
                        file_urls.append({"filename": file['file'],
                                      "url": f"http://{HOST}:{PORT}/jupyter{file_path}"})

                return request_classes.CodeResponse(
                    output=out,
                    error=error,
                    timedout=timedout,
                    files=file_urls if files else None,
                    stacktrace=None
                )

        return request_classes.CodeResponse(
            output=None,
            error="No code provided to run",
            timedout=False,
            files=None,
            stacktrace=None
        )

    except Exception as e:
        # Handle any exceptions that occur during execution
        return request_classes.CodeResponse(
            output=None,
            error=f"An error occurred: {str(e)}",
            timedout=False,
            files=None,
            stacktrace=traceback.format_exc()
        )

    finally:
        os.chdir(cwd)
        logger.info(f"Returning to original directory: {cwd}")


# Initialize FastAPI-MCP
mcp = FastApiMCP(
    app,
    name="Code Execution API",
    description="API for executing code in a sandboxed environment",
    describe_all_responses=False,
    describe_full_response_schema=True
)
mcp.mount()


# Run the application with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=8080)
    except KeyboardInterrupt:
        print("Shutting down...")