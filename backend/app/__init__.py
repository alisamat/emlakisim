from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(env='production'):
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))

    from .routes import auth, webhook, panel, musteri, sohbet, muhasebe, hesaplama, planlama, egitim, toplu, tanitim, lead, gelismis
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

    return app
