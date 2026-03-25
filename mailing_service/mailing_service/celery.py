import os

from celery import Celery
from mailing_service.settings import REDIS_URL, TIME_ZONE
import dill
import zstandard as zstd
from kombu.serialization import pickle_loads, pickle_protocol, registry
from kombu.utils.encoding import str_to_bytes

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mailing_service.settings")

celery_app = Celery("mailing_service", broker_url=REDIS_URL)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


def register_dill():
    def encode(obj, dumper=dill.dumps):
        dump_obj = dumper(obj, protocol=pickle_protocol)
        compressor = zstd.ZstdCompressor(level=3)
        return compressor.compress(dump_obj)

    def decode(s):
        decompressor = zstd.ZstdDecompressor()
        decompressed_obj = decompressor.decompress(s)
        return pickle_loads(str_to_bytes(decompressed_obj), load=dill.load)

    registry.register(
        name="dill",
        encoder=encode,
        decoder=decode,
        content_type="application/x-python-serialize",
        content_encoding="binary",
    )


register_dill()
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_ignore_result=False,
    broker_connection_retry_on_startup=True,
    task_serializer="dill",
    accept_content=["dill", "json"],
    result_serializer="dill",
    timezone=TIME_ZONE,
    task_track_started=True,
    task_create_missing_meta=True
)
