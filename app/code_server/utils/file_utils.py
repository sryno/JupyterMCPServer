import os
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI


FILES_DIR = "/files"
os.makedirs(FILES_DIR, exist_ok=True)


async def _cleanup_old_files():
    """
    Continuously monitors and removes old files from the FILES_DIR directory.

    Files containing '-long' in their name have a lifetime of 48 hours (2880 minutes),
    while other files have a lifetime of 20 minutes. The function runs every minute
    and removes files that exceed their lifetime based on their modification time.

    This function runs indefinitely until cancelled.
    """
    while True:
        await asyncio.sleep(60)  # run every minute
        now = datetime.utcnow()
        for fname in os.listdir(FILES_DIR):
            if '-long' in fname:
                lt = 2880
            else:
                lt = 20

            path = os.path.join(FILES_DIR, fname)
            if not os.path.isfile(path):
                continue
            # Use modification time to decide age
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime > timedelta(minutes=lt):
                try:
                    os.remove(path)
                except OSError:
                    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager that manages the file cleanup task.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Yields control back to the FastAPI application.

    The context manager starts the file cleanup task on application startup
    and ensures proper cleanup task cancellation on application shutdown.
    """
    # startup: launch cleanup task
    cleanup_task = asyncio.create_task(_cleanup_old_files())
    yield
    # shutdown: cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
