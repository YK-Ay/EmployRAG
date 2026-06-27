# -*- coding: utf-8 -*-
"""
文件存储服务 — 双模式自动切换
- 检测到 OSS 配置 → 使用阿里云 OSS
- 未检测到 OSS 配置 → 使用本地文件系统（local_storage/）
"""

import os
import logging
import datetime
import shutil
from typing import Optional

logger = logging.getLogger(__name__)

# 项目根目录下的本地存储文件夹
_LOCAL_STORAGE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "local_storage"
)


class LocalStorageBackend:
    """本地文件系统存储（无 OSS 时的降级方案）"""

    def __init__(self):
        os.makedirs(_LOCAL_STORAGE_ROOT, exist_ok=True)
        logger.info("📁 文件存储模式: 本地文件系统 (%s)", _LOCAL_STORAGE_ROOT)

    def upload_bytes(self, object_key: str, file_content: bytes) -> str:
        """上传文件到本地"""
        filepath = os.path.normpath(os.path.join(_LOCAL_STORAGE_ROOT, object_key.replace("/", os.sep)))
        # 安全检查：防止路径穿越
        if not filepath.startswith(os.path.normpath(_LOCAL_STORAGE_ROOT)):
            raise ValueError(f"非法文件路径: {object_key}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(file_content)
        logger.info("本地存储: 已写入 %s (%d bytes)", object_key, len(file_content))
        return object_key

    def upload_file(self, category_name: str, file_name: str, file_content: bytes) -> str:
        object_key = f"{category_name}/{file_name}"
        return self.upload_bytes(object_key, file_content)

    def get_object_bytes(self, object_key: str) -> bytes:
        """从本地读取文件"""
        filepath = os.path.normpath(os.path.join(_LOCAL_STORAGE_ROOT, object_key.replace("/", os.sep)))
        if not filepath.startswith(os.path.normpath(_LOCAL_STORAGE_ROOT)):
            raise ValueError(f"非法文件路径: {object_key}")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"本地文件不存在: {object_key} (路径: {filepath})")
        with open(filepath, "rb") as f:
            return f.read()

    def delete_objects(self, object_keys: list) -> int:
        """批量删除本地文件"""
        deleted = 0
        for key in object_keys:
            filepath = os.path.normpath(os.path.join(_LOCAL_STORAGE_ROOT, key.replace("/", os.sep)))
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted += 1
        return deleted

    def get_presigned_url(self, object_key: str, expires: int = 3600) -> str:
        """本地模式返回 API 代理路径（无需预签名）"""
        from urllib.parse import quote
        return f"/api/v1/documents/image-proxy?oss_key={quote(object_key, safe='/')}"

    def get_presigned_url_by_category(self, category_name: str, file_name: str, expires: int = 3600) -> str:
        object_key = f"{category_name}/{file_name}"
        return self.get_presigned_url(object_key, expires)


class OSSBackend:
    """阿里云 OSS 存储（生产环境）"""
    # 原有逻辑：仅在 OSS 配置可用时才初始化

    def __init__(self, access_key_id: str, access_key_secret: str, region: str, endpoint: str, bucket: str):
        import urllib3
        import alibabacloud_oss_v2 as oss
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        credentials_provider = oss.credentials.StaticCredentialsProvider(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = region
        cfg.endpoint = endpoint
        cfg.insecure_skip_verify = True
        self.client = oss.Client(cfg)
        self.bucket = bucket
        logger.info("☁️ 文件存储模式: 阿里云 OSS (bucket=%s, region=%s)", bucket, region)

    def upload_bytes(self, object_key: str, file_content: bytes) -> str:
        try:
            result = self.client.put_object(
                oss.PutObjectRequest(
                    bucket=self.bucket,
                    key=object_key,
                    body=file_content,
                )
            )
            logger.info("OSS 上传成功: %s, status=%s", object_key, result.status_code)
            return object_key
        except Exception as e:
            logger.error("OSS 上传失败: %s, error=%s", object_key, e)
            raise Exception(f"OSS 上传失败: {e}")

    def upload_file(self, category_name: str, file_name: str, file_content: bytes) -> str:
        object_key = f"{category_name}/{file_name}"
        return self.upload_bytes(object_key, file_content)

    def get_object_bytes(self, object_key: str) -> bytes:
        try:
            result = self.client.get_object(
                oss.GetObjectRequest(bucket=self.bucket, key=object_key)
            )
            with result.body as body:
                data = body.read()
            logger.info("OSS 下载成功: %s, size=%d", object_key, len(data))
            return data
        except Exception as e:
            logger.error("OSS 下载失败: %s, error=%s", object_key, e)
            raise Exception(f"OSS 下载失败: {e}")

    def delete_objects(self, object_keys: list) -> int:
        if not object_keys:
            return 0
        try:
            objects = [oss.DeleteObject(key=k) for k in object_keys]
            result = self.client.delete_multiple_objects(
                oss.DeleteMultipleObjectsRequest(bucket=self.bucket, objects=objects)
            )
            deleted_count = len(result.deleted_objects) if result.deleted_objects else 0
            logger.info("OSS 批量删除: 请求 %d 个, 成功 %d 个", len(object_keys), deleted_count)
            return deleted_count
        except Exception as e:
            logger.error("OSS 批量删除失败: %s", e)
            return 0

    def get_presigned_url(self, object_key: str, expires: int = 3600) -> str:
        import alibabacloud_oss_v2 as oss
        try:
            result = self.client.presign(
                oss.GetObjectRequest(bucket=self.bucket, key=object_key),
                expires=datetime.timedelta(seconds=expires),
            )
            return result.url
        except Exception as e:
            logger.error("生成临时 URL 失败: %s, error=%s", object_key, e)
            raise Exception(f"生成临时 URL 失败: {object_key}, error={e}")

    def get_presigned_url_by_category(self, category_name: str, file_name: str, expires: int = 3600) -> str:
        object_key = f"{category_name}/{file_name}"
        return self.get_presigned_url(object_key, expires)


# ── 全局单例 ──
_instance: Optional[object] = None


def get_oss_service():
    """获取存储服务单例（自动选择 OSS 或本地）"""
    global _instance
    if _instance is not None:
        return _instance

    from app.core.config import settings

    # 判断 OSS 是否可用
    oss_available = bool(
        settings.oss_bucket
        and (settings.oss_access_key_id)
        and (settings.oss_access_key_secret)
    )

    if oss_available:
        _instance = OSSBackend(
            access_key_id=settings.oss_access_key_id,
            access_key_secret=settings.oss_access_key_secret,
            region=settings.oss_region,
            endpoint=settings.oss_endpoint,
            bucket=settings.oss_bucket,
        )
    else:
        logger.info("⚠️ 未检测到 OSS 配置，使用本地文件系统存储")
        _instance = LocalStorageBackend()

    return _instance
