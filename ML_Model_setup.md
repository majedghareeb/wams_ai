# Server Setup for WAMS AI Application

This document outlines the steps to set up the WAMS AI application to run with Gunicorn on system startup and download the required models.

## Steps to Download Required Models

1. **Download the NER Model and Tokenizer**

   Navigate to the directory where you want to store the models and run the following commands:

   ```bash
   mkdir -p camel-tool
   cd camel-tool
   git clone <ner-model-repository-url>  # Replace with the actual repository URL for the NER model
   ```

2. **Download the Classification Model**

   Similarly, download the classification model:

   ```bash
   mkdir -p mbert
   cd mbert
   git clone <classification-model-repository-url>  # Replace with the actual repository URL for the classification model
   ```

3. **Return to the Application Directory**

   After downloading the models, return to the application directory:

   ```bash
   cd <path-to-your-app>  # Replace with the actual path to your app
   ```

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

Following these steps will ensure that the WAMS AI application runs with Gunicorn, starts automatically on system boot, and has the required models downloaded.
