import base64
import io
import secrets


QR_PAYLOAD_PREFIX = 'WMSQR:'


def generate_qr_token():
    return secrets.token_hex(5).upper()


def build_qr_payload(qr_token):
    return f'{QR_PAYLOAD_PREFIX}{qr_token}'


def build_qr_preview_data_url(qr_payload):
    try:
        import qrcode
    except ImportError:
        return None

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    buffer = io.BytesIO()

    try:
        image = qr.make_image(fill_color='black', back_color='white')
        image.save(buffer, format='PNG')
    except Exception:
        try:
            from qrcode.image.pure import PyPNGImage
        except ImportError:
            return None

        image = qr.make_image(image_factory=PyPNGImage)
        image.save(buffer)

    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'
