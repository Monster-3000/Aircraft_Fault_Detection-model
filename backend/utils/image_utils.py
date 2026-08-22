import os
import shutil
from fastapi import UploadFile

def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Saves an uploaded file to the specified destination.
    """
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    return destination
