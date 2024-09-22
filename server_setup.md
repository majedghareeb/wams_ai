# Server Setup for WAMS AI Application

This document outlines the steps to set up the WAMS AI application to run with Gunicorn on system startup.

## Steps to Create a Systemd Service for Gunicorn

1. **Create a Gunicorn Service File**

   Open a terminal and create a new service file for your application:

   ```bash
   sudo nano /etc/systemd/system/wams_ai.service
   ```

2. **Add the Following Configuration**

   Replace `<your-username>` and `<path-to-your-app>` with your actual username and the path to your `app.py` file.

   ```ini
   [Unit]
   Description=WAMS AI Application
   After=network.target

   [Service]
   User=<your-username>
   Group=www-data
   WorkingDirectory=<path-to-your-app>
   Environment="PATH=<path-to-your-app>/venv/bin"
   ExecStart=<path-to-your-app>/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

3. **Reload Systemd to Apply Changes**

   After saving the service file, reload the systemd manager configuration:

   ```bash
   sudo systemctl daemon-reload
   ```

4. **Start the Gunicorn Service**

   Start the service with the following command:

   ```bash
   sudo systemctl start wams_ai
   ```

5. **Enable the Service to Start on Boot**

   To ensure that the service starts automatically on system boot, run:

   ```bash
   sudo systemctl enable wams_ai
   ```

6. **Check the Status of the Service**

   You can check the status of your service to ensure it is running:

   ```bash
   sudo systemctl status wams_ai
   ```

## Conclusion

Following these steps will ensure that the WAMS AI application runs with Gunicorn and starts automatically on system boot.
