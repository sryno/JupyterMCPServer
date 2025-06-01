# Jupyter-based Code Execution API with Sandboxed Environment Support

A secure and scalable FastAPI application that enables remote code execution in isolated Jupyter kernels. The service 
supports multiple programming languages (Python, JavaScript, Java, Bash), manages file uploads, and provides 
comprehensive execution monitoring with configurable timeouts and resource limits.

The application offers a containerized environment with pre-configured Jupyter kernels and scientific computing 
packages, making it ideal for educational platforms, coding assessments, or remote code execution services. Key 
features include package installation support, file management with configurable lifetimes, and robust error handling 
with detailed execution feedback.

A basic mechanism for API key authentication is included, but should be replaced with your own implementation.

## Repository Structure
```
.
├── app/                         # Main application directory
│   ├── code_server/             # Core server implementation
│   │   ├── classes/             # Data models and request/response classes
│   │   ├── jupyter/             # Jupyter kernel management and execution
│   │   └── utils/               # Utility functions for auth, logging, and file management
│   ├── main_ray.py              # Ray Serve distributed deployment entry point
│   ├── main.py                  # FastAPI application entry point
|   └── .env                     # Environment variable file
└── Dockerfile                   # Multi-stage container build with Jupyter environments
```

## Usage Instructions
### Installation

#### Using Docker (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Build the Docker image
docker build -t jupyter-code-execution .

# Run the container
docker run --rm -d -p 8080:8080 --env-file .env -v --name code-execution jupyter-code-execution
```

### Quick Start
1. Check available kernels:
```bash
curl http://localhost:8080/jupyter/list_kernel_specs
```

2. Execute Python code:
```python
import requests
import json

code_request = {
    "code": "print('Hello, World!')",
    "execution_environment": "python",
    "timeout": 10
}

response = requests.post(
    "http://localhost:8080/jupyter/execute",
    json=code_request
)
print(json.dumps(response.json(), indent=2))
```

### Additional Examples

1. Execute code with package installation:
```python
code_request = {
    "code": """
    import numpy as np
    arr = np.array([1, 2, 3])
    print(arr.mean())
    """,
    "execution_environment": "python_scientific",
    "packages": ["numpy"],
    "timeout": 30
}
```

2. Upload and use files:
```python
# Upload file
file_content = base64.b64encode(b"1,2,3\n4,5,6").decode()
file_request = {
    "filename": "data",
    "extension": "csv",
    "content": file_content
}
file_response = requests.put(
    "http://localhost:8080/jupyter/files",
    json=file_request
)
```

## Data Flow
The application processes code execution requests through a pipeline of kernel management, execution, and result collection. Input code and files are validated, executed in isolated environments, and results are collected with proper error handling.

```ascii
Client -> FastAPI -> Jupyter Kernel Manager -> Kernel Execution -> Result Collection -> Client
```

Key component interactions:
1. FastAPI validates incoming requests and manages authentication
2. Jupyter Kernel Manager creates and maintains isolated execution environments
3. Code execution happens in separate kernel processes with resource limits
4. File management system handles uploads with configurable retention periods
5. Results are collected, formatted, and returned with execution metadata

## Infrastructure
### Docker Resources
- Base Image: jupyter/base-notebook:latest
- Exposed Ports: 8080
- Environment Variables:
  - RAY_memory_monitor_refresh_ms: 50
  - RAY_memory_usage_threshold: 0.90

### Jupyter Kernels
- python: Base Python environment with plotting packages
- python_scientific: Extended Python environment with additional scientific libraries
- javascript: Node.js kernel with npm support
- java: Java 11 kernel

### Health Monitoring
- Health check interval: 5s
- Timeout: 60s
- Start period: 5s
- Retries: 3