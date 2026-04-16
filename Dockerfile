FROM odoo:17.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ODOO_RC=/etc/odoo/odoo.conf

# Cài requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt || true

CMD ["odoo", "-c", "/etc/odoo/odoo.conf"]
