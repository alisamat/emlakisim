"""
DOSYA SERVİSİ — Fotoğraf/belge yükleme altyapısı
Storage backend gelince aktif olur (Supabase/S3/local)

Gerekli env:
  STORAGE_TYPE = local / supabase / s3
  SUPABASE_URL = https://xxx.supabase.co
  SUPABASE_KEY = service_role_key
  SUPABASE_BUCKET = emlakisim
  AWS_ACCESS_KEY = (S3 için)
  AWS_SECRET_KEY = (S3 için)
  AWS_BUCKET = (S3 için)
"""
import os
import io
import uuid
import logging

logger = logging.getLogger(__name__)


def dosya_yukle(dosya_bytes, dosya_adi, klasor='genel'):
    """Dosya yükle → URL döndür."""
    storage_type = os.environ.get('STORAGE_TYPE', 'local')

    if storage_type == 'supabase':
        return _supabase_yukle(dosya_bytes, dosya_adi, klasor)
    elif storage_type == 's3':
        return _s3_yukle(dosya_bytes, dosya_adi, klasor)
    else:
        return _local_yukle(dosya_bytes, dosya_adi, klasor)


def _local_yukle(dosya_bytes, dosya_adi, klasor):
    """Local storage — base64 data URL olarak döndür (Supabase/S3 yokken geçerli)."""
    import base64
    b64 = base64.b64encode(dosya_bytes).decode()
    ext = dosya_adi.rsplit('.', 1)[-1].lower() if '.' in dosya_adi else 'bin'
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'pdf': 'application/pdf'}.get(ext, 'application/octet-stream')
    return True, f'data:{mime};base64,{b64}'


def _supabase_yukle(dosya_bytes, dosya_adi, klasor):
    """Supabase Storage ile dosya yükle."""
    import requests
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_KEY', '')
    bucket = os.environ.get('SUPABASE_BUCKET', 'emlakisim')

    if not url or not key:
        return False, 'Supabase yapılandırması eksik'

    try:
        yol = f'{klasor}/{uuid.uuid4().hex}_{dosya_adi}'
        r = requests.post(
            f'{url}/storage/v1/object/{bucket}/{yol}',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/octet-stream'},
            data=dosya_bytes, timeout=30,
        )
        if r.status_code in (200, 201):
            dosya_url = f'{url}/storage/v1/object/public/{bucket}/{yol}'
            return True, dosya_url
        return False, f'Supabase hata: {r.status_code}'
    except Exception as e:
        return False, str(e)


def _s3_yukle(dosya_bytes, dosya_adi, klasor):
    """AWS S3 ile dosya yükle."""
    try:
        import boto3
        s3 = boto3.client('s3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
        )
        bucket = os.environ.get('AWS_BUCKET', 'emlakisim')
        yol = f'{klasor}/{uuid.uuid4().hex}_{dosya_adi}'
        s3.put_object(Bucket=bucket, Key=yol, Body=dosya_bytes)
        dosya_url = f'https://{bucket}.s3.amazonaws.com/{yol}'
        return True, dosya_url
    except Exception as e:
        return False, str(e)


def storage_durum():
    """Storage servis durumu."""
    storage_type = os.environ.get('STORAGE_TYPE', 'local')
    return {
        'aktif': storage_type != 'local',
        'tip': storage_type,
        'supabase': bool(os.environ.get('SUPABASE_URL')),
        's3': bool(os.environ.get('AWS_ACCESS_KEY')),
    }
