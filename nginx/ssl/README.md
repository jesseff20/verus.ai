# SSL Certificates

## Let's Encrypt (Certbot)

Na IBM, execute:

```bash
# Instalar certbot
sudo apt update
sudo apt install certbot

# Gerar certificado (modo standalone - para antes dos containers)
sudo certbot certonly --standalone -d bravodoc.bravonix.ia.br --email mqmaellson39@gmail.com --agree-tos

# Copiar certificados para esta pasta
sudo cp /etc/letsencrypt/live/bravodoc.bravonix.ia.br/fullchain.pem ./
sudo cp /etc/letsencrypt/live/bravodoc.bravonix.ia.br/privkey.pem ./
sudo chown $USER:$USER *.pem
```

## Renovação Automática

Adicionar ao crontab:
```bash
0 0 1 * * certbot renew --quiet && docker restart bravodoc_nginx_prod
```
