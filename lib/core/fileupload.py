from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from features.accounts import models

from core.config import settings
from core.permissions import get_current_user
from core.response import SimpleResponse


class FileExtensionValidator:
    default_message = "Extension “{extension}” not allowed. Allowed extensions are {allowed_extensions}"
    default_mime_message = "MIME type “{mime_type}” not allowed. Allowed MIME types are {allowed_mime_types}"

    def __init__(
        self,
        allowed_extensions=None,
        allowed_mime_types=None,
        message=None,
        mime_message=None,
    ):
        if allowed_extensions is not None:
            allowed_extensions = [
                allowed_extension.lower() for allowed_extension in allowed_extensions
            ]
        if allowed_mime_types is not None:
            allowed_mime_types = [
                allowed_mime_type.lower() for allowed_mime_type in allowed_mime_types
            ]
        self.allowed_extensions = allowed_extensions
        self.allowed_mime_types = allowed_mime_types
        self.message = message or self.default_message
        self.mime_message = mime_message or self.default_mime_message

    def __call__(self, file: UploadFile):
        extension = Path(file.filename or "").suffix[1:].lower()

        if self.allowed_extensions and extension not in self.allowed_extensions:
            detail = self.message.format(
                extension=extension,
                allowed_extensions=", ".join(self.allowed_extensions),
            )
            raise HTTPException(status_code=400, detail=detail)
        # if extension == "pdf":
        #     # TODO do other check
        #     return
        # # Check MIME type
        # try:
        #     import magic

        #     mime = magic.Magic(mime=True)
        #     mime_type = mime.from_buffer(
        #         file.file.read(1024)
        #     )  # Read a portion of the file to determine its MIME type
        #     file.file.seek(0)  # Reset file pointer to the beginning

        #     if self.allowed_mime_types and mime_type not in self.allowed_mime_types:
        #         detail = self.mime_message.format(
        #             mime_type=mime_type,
        #             allowed_mime_types=", ".join(self.allowed_mime_types),
        #         )
        #         raise HTTPException(status_code=400, detail=detail)
        # except ImportError:
        #     pass
        # # Check if file is a valid image
        # image_type = imghdr.what(file.file)
        # file.file.seek(0)  # Reset file pointer to the beginning

        # if image_type is None:
        #     raise HTTPException(
        #         status_code=400, detail="Uploaded file is not a valid image."
        #     )


image_file_validator = FileExtensionValidator(
    allowed_extensions=["jpg", "jpeg", "png", "gif", "pdf"],
    allowed_mime_types=["image/jpeg", "image/png", "image/gif", "application/pdf"],
)
video_file_validator = FileExtensionValidator(
    allowed_extensions=["mp4", "mov", "avi", "wmv", "flv"],
    allowed_mime_types=["video/mp4", "video/quicktime", "video/x-msvideo"],
)
docs_file_validator = FileExtensionValidator(
    allowed_extensions=[
        "jpg",
        "jpeg",
        "png",
        "gif",
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
    ],
    allowed_mime_types=[
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ],
)


class MaxFileSizeMBValidator:
    def __init__(self, max_mb: int):
        self.max_mb = max_mb

    def __call__(self, file: UploadFile):
        if not file.size:
            return
        if file.size / 1024 / 1024 > self.max_mb:
            message = f"Maximum file size exceeded {file.size / 1024 / 1024}"
            raise HTTPException(400, detail=message)


def upload_to_s3(file: BinaryIO, file_name: str, path: str):
    s3_client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=f"https://{settings.aws_region}.digitaloceanspaces.com",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    s3_key = f"{path.rstrip('/')}/{file_name}"
    s3_client.upload_fileobj(
        file,
        settings.aws_bucket_name,
        s3_key,
        ExtraArgs={"ACL": "public-read"},  # Set public-read permission here
    )


class ImageUploadResponse(SimpleResponse):
    image_path: str


class FileType(Enum):
    PROFILE = "profile"
    COVER = "cover"
    MEDIA = "media"


file_upload_route = APIRouter(prefix="/api/v1/file_upload", tags=["FileUpload"])


@file_upload_route.post(
    "/",
    dependencies=[
        Depends(
            MaxFileSizeMBValidator(50),
        ),
        Depends(image_file_validator),
    ],
    response_model=ImageUploadResponse,
)
async def upload_file(
    file: UploadFile,
    file_type: FileType,
    account: models.Account = Depends(get_current_user),
):
    if file.filename is None:
        return HTTPException(status_code=400, detail="No file name")
    if file.content_type is None:
        return HTTPException(status_code=400, detail="No content type")
    if file.file is None:
        return HTTPException(status_code=400, detail="No file")
    file_path = f"{file_type.name}/{account.uuid}/"
    await run_in_threadpool(upload_to_s3, file.file, file.filename, path=file_path)
    return ImageUploadResponse(
        image_path=file_path + file.filename,
        message="File uploaded successfully",
        status_code=200,
    )


@file_upload_route.post(
    "/open/",
    dependencies=[
        Depends(
            MaxFileSizeMBValidator(50),
        ),
    ],
    response_model=ImageUploadResponse,
)
async def upload_file_open(
    file: UploadFile,
    file_type: FileType,
    # account: models.Account = Depends(get_current_user),
):
    if file.filename is None:
        return HTTPException(status_code=400, detail="No file name")
    if file.content_type is None:
        return HTTPException(status_code=400, detail="No content type")
    if file.file is None:
        return HTTPException(status_code=400, detail="No file")
    file_path = "test/"
    await run_in_threadpool(upload_to_s3, file.file, file.filename, path=file_path)
    return ImageUploadResponse(
        image_path=file_path + file.filename,
        message="File uploaded successfully",
        status_code=200,
    )


@file_upload_route.post(
    "/video/",
    dependencies=[
        Depends(
            MaxFileSizeMBValidator(100),
        ),
        Depends(video_file_validator),
    ],
    response_model=ImageUploadResponse,
)
async def upload_video(
    file: UploadFile,
    file_type: FileType = FileType.MEDIA,
    account: models.Account = Depends(get_current_user),
):
    if file.filename is None:
        return HTTPException(status_code=400, detail="No file name")
    if file.content_type is None:
        return HTTPException(status_code=400, detail="No content type")
    if file.file is None:
        return HTTPException(status_code=400, detail="No file")
    file_path = f"{file_type.name}/{account.uuid}/"
    await run_in_threadpool(upload_to_s3, file.file, file.filename, path=file_path)
    return ImageUploadResponse(
        image_path=file_path + file.filename,
        message="File uploaded successfully",
        status_code=200,
    )


@file_upload_route.post(
    "/delete/",
    response_model=SimpleResponse,
)
async def delete_file_from_s3_func(file_path: str):
    try:
        result = await delete_file_from_s3(file_path)
    except Exception as _:
        raise HTTPException(status_code=400, detail="File not found")
    return SimpleResponse(
        message=str(result),
        status_code=200,
    )


@lru_cache()
async def delete_file_from_s3(file_path: str):
    s3_client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=f"https://{settings.aws_region}.digitaloceanspaces.com",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    return await run_in_threadpool(
        s3_client.delete_object,
        Bucket=settings.aws_bucket_name,
        Key=file_path.lstrip("/"),
    )
