from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Rate limiter (lazy init)
_limiter = None


def create_app(env='production'):
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))

    # Rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        global _limiter
        _limiter = Limiter(get_remote_address, app=app, default_limits=["200 per minute"],
                          storage_uri="memory://")
    except ImportError:
        pass

    from .routes import auth, webhook, panel, musteri, sohbet, muhasebe, hesaplama, planlama, egitim, toplu, tanitim, lead, gelismis, bildirim, fatura, islem_takip, ofis, ekip, admin, ayarlar as ayarlar_route
    app.register_blueprint(auth.bp)
    app.register_blueprint(webhook.bp)
    app.register_blueprint(panel.bp)
    app.register_blueprint(musteri.bp)
    app.register_blueprint(sohbet.bp)
    app.register_blueprint(muhasebe.bp)
    app.register_blueprint(hesaplama.bp)
    app.register_blueprint(planlama.bp)
    app.register_blueprint(egitim.bp)
    app.register_blueprint(toplu.bp)
    app.register_blueprint(tanitim.bp)
    app.register_blueprint(lead.bp)
    app.register_blueprint(gelismis.bp)
    app.register_blueprint(bildirim.bp)
    app.register_blueprint(fatura.bp)
    app.register_blueprint(islem_takip.bp)
    app.register_blueprint(ofis.bp)
    app.register_blueprint(ekip.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(ayarlar_route.bp)

    # Zamanlayıcı başlat (otomatik hatırlatma, günlük özet, yedek uyarısı)
    try:
        from app.services.zamanlayici import zamanlayici_baslat
        zamanlayici_baslat(app)
    except Exception:
        pass

    from flask import render_template_string
    @app.route('/gizlilik')
    def gizlilik():
        return render_template_string("""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Gizlilik Politikası — Emlakisim</title>
<style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#1e293b;line-height:1.7}h1{color:#16a34a}h2{margin-top:32px}</style>
</head><body>
<h1>Emlakisim Gizlilik Politikası</h1>
<p>Son güncelleme: Nisan 2026</p>
<h2>1. Toplanan Veriler</h2>
<p>Emlakisim, hizmet sunumu amacıyla ad-soyad, telefon numarası, e-posta adresi ve TC kimlik numarası gibi kişisel verileri toplar.</p>
<h2>2. Verilerin Kullanımı</h2>
<p>Toplanan veriler yalnızca emlak işlemlerinin yürütülmesi, yer gösterme belgesi oluşturulması ve müşteri iletişimi amacıyla kullanılır.</p>
<h2>3. WhatsApp Entegrasyonu</h2>
<p>Uygulama, Meta'nın WhatsApp Business API'sini kullanmaktadır. WhatsApp üzerinden iletilen mesajlar işlenmekte ve güvenli sunucularda saklanmaktadır.</p>
<h2>4. Veri Güvenliği</h2>
<p>Verileriniz şifrelenerek saklanır ve üçüncü taraflarla paylaşılmaz.</p>
<h2>5. İletişim</h2>
<p>Gizlilik ile ilgili sorularınız için: <a href="mailto:info@emlakisim.com.tr">info@emlakisim.com.tr</a></p>
</body></html>""")

    _sayfa_stil = 'body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#1e293b;line-height:1.7}h1{color:#16a34a}h2{margin-top:32px}a{color:#16a34a}'

    @app.route('/hakkimizda')
    def hakkimizda():
        return render_template_string(f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Hakkımızda — Emlakisim</title><style>{_sayfa_stil}</style></head><body>
<h1>Hakkımızda</h1>
<p>Emlakisim, emlak profesyonelleri için geliştirilen yapay zeka destekli asistan platformudur.</p>
<h2>Misyonumuz</h2>
<p>Emlakçıların günlük işlerini kolaylaştırmak, müşteri ilişkilerini güçlendirmek ve iş verimliliklerini artırmak.</p>
<h2>Ne Yapıyoruz?</h2>
<ul>
<li>Müşteri ve portföy yönetimi (CRM)</li>
<li>WhatsApp ve web üzerinden AI asistan</li>
<li>Belge oluşturma (yer gösterme, kontrat, fatura)</li>
<li>Muhasebe ve finansal raporlama</li>
<li>Eşleştirme, hesaplama ve analiz araçları</li>
</ul>
<p><a href="/">← Ana Sayfa</a></p>
</body></html>""")

    @app.route('/fiyatlar')
    def fiyatlar():
        return render_template_string(f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Fiyatlar — Emlakisim</title><style>{_sayfa_stil}</style></head><body>
<h1>Fiyatlar</h1>
<h2>Kredi Sistemi</h2>
<p>Emlakisim kredi bazlı çalışır. Her işlem belirli miktarda kredi harcar.</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
<tr style="border-bottom:2px solid #e2e8f0"><th style="text-align:left;padding:8px">İşlem</th><th style="text-align:right;padding:8px">Kredi</th></tr>
<tr style="border-bottom:1px solid #f1f5f9"><td style="padding:8px">Pattern komutları (müşteri listele, rapor...)</td><td style="text-align:right;padding:8px"><strong>0</strong></td></tr>
<tr style="border-bottom:1px solid #f1f5f9"><td style="padding:8px">AI sohbet mesajı</td><td style="text-align:right;padding:8px"><strong>1</strong></td></tr>
<tr style="border-bottom:1px solid #f1f5f9"><td style="padding:8px">Belge oluşturma (PDF)</td><td style="text-align:right;padding:8px"><strong>2</strong></td></tr>
<tr><td style="padding:8px">OCR / görsel işleme</td><td style="text-align:right;padding:8px"><strong>2</strong></td></tr>
</table>
<p>Yeni kayıt: <strong>10 kredi</strong> hediye!</p>
<p><a href="/">← Ana Sayfa</a></p>
</body></html>""")

    @app.route('/iletisim')
    def iletisim_sayfasi():
        return render_template_string(f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>İletişim — Emlakisim</title><style>{_sayfa_stil}</style></head><body>
<h1>İletişim</h1>
<p>Bize ulaşmak için:</p>
<ul>
<li>Email: <a href="mailto:info@emlakisim.com">info@emlakisim.com</a></li>
<li>Web: <a href="https://emlakisim.com">emlakisim.com</a></li>
</ul>
<p><a href="/">← Ana Sayfa</a></p>
</body></html>""")

    @app.route('/kvkk')
    def kvkk():
        return render_template_string(f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>KVKK — Emlakisim</title><style>{_sayfa_stil}</style></head><body>
<h1>KVKK Aydınlatma Metni</h1>
<p>6698 sayılı Kişisel Verilerin Korunması Kanunu kapsamında:</p>
<h2>Veri Sorumlusu</h2>
<p>Emlakisim platformu olarak kişisel verilerinizin güvenliğine önem veriyoruz.</p>
<h2>Toplanan Veriler</h2>
<p>Ad-soyad, telefon, e-posta, TC kimlik numarası, adres bilgileri, emlak tercihleri.</p>
<h2>İşleme Amaçları</h2>
<p>Emlak danışmanlık hizmetlerinin sunulması, müşteri ilişkilerinin yönetimi, yasal yükümlülüklerin yerine getirilmesi.</p>
<h2>Veri Saklama</h2>
<p>Verileriniz yasal süre boyunca güvenli ortamda saklanır. Kullanıcılar verilerini her zaman export edebilir ve silme talep edebilir.</p>
<h2>Haklarınız</h2>
<ul>
<li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
<li>İşlenmişse buna ilişkin bilgi talep etme</li>
<li>İşlenme amacını öğrenme</li>
<li>Yanlış/eksik işlenmişse düzeltilmesini isteme</li>
<li>Silinmesini veya yok edilmesini isteme</li>
</ul>
<p>Başvuru: <a href="mailto:info@emlakisim.com">info@emlakisim.com</a></p>
<p><a href="/">← Ana Sayfa</a></p>
</body></html>""")

    return app
