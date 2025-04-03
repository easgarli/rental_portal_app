#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit
fi

# Create application directory
sudo mkdir -p /var/www/rental_portal_app
sudo chown www-data:www-data /var/www/rental_portal_app

# Clone the repository
sudo -u www-data git clone https://github.com/yourusername/rental-portal.git /var/www/rental_portal_app

# Create and activate virtual environment
cd /var/www/rental_portal_app
sudo -u www-data python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create wsgi.py file
cat > wsgi.py << EOL
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
EOL

# Create systemd service file
cat > /etc/systemd/system/rental-portal.service << EOL
[Unit]
Description=Gunicorn instance to serve Rental Portal application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/rental_portal_app
Environment="PATH=/var/www/rental_portal_app/venv/bin"
ExecStart=/var/www/rental_portal_app/venv/bin/gunicorn --workers 3 --bind unix:rental-portal.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOL

# Create Nginx configuration
cat > /etc/nginx/sites-available/rent-a-home.tft.az << EOL
server {
    listen 80;
    server_name rent-a-home.tft.az;

    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }

    location /static/ {
        root /var/www/rental_portal_app;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/rental_portal_app/rental-portal.sock;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_buffering off;
        proxy_redirect off;
    }

    access_log /var/log/nginx/rental-portal-access.log;
    error_log /var/log/nginx/rental-portal-error.log;
}
EOL

# Create log files and set permissions
touch /var/log/nginx/rental-portal-access.log
touch /var/log/nginx/rental-portal-error.log
chown www-data:www-data /var/log/nginx/rental-portal-*.log

# Reload systemd to recognize new service
systemctl daemon-reload

# Set up Nginx configuration
if [ -L /etc/nginx/sites-enabled/rent-a-home.tft.az ]; then
    echo "Removing existing symbolic link..."
    rm /etc/nginx/sites-enabled/rent-a-home.tft.az
fi

echo "Creating new symbolic link..."
sudo ln -s /etc/nginx/sites-available/rent-a-home.tft.az /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start Gunicorn service
sudo systemctl start rental-portal
sudo systemctl enable rental-portal

# Set up SSL with Certbot (if needed)
sudo certbot --nginx -d rent-a-home.tft.az

echo "Deployment completed! Check service status with:"
echo "sudo systemctl status rental-portal"
echo "sudo nginx -t"
echo "sudo systemctl status nginx" 