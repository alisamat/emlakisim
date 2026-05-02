"""
SESLİ NOT SERVİSİ — OpenAI Whisper ile ses → yazı dönüşümü
Gösterim notu, toplantı notu, sesli komut.
"""
import os
import logging

logger = logging.getLogger(__name__)


def ses_to_yazi(audio_bytes, dosya_adi='ses.webm'):
    """Ses dosyasını yazıya çevir — OpenAI Whisper API."""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return {'basarili': False, 'hata': 'OpenAI API anahtarı bulunamadı'}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Geçici dosya oluştur
        import tempfile
        ext = dosya_adi.rsplit('.', 1)[-1] if '.' in dosya_adi else 'webm'
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        # Whisper API çağır
        with open(temp_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file,
                language='tr',
                response_format='text',
            )

        # Geçici dosyayı sil
        os.unlink(temp_path)

        metin = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
        logger.info(f'[SesliNot] Transkript: {metin[:100]}...')
        return {'basarili': True, 'metin': metin}

    except Exception as e:
        logger.error(f'[SesliNot] Hata: {e}')
        return {'basarili': False, 'hata': str(e)}
