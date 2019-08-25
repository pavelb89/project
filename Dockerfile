FROM python:3.7

# Create app dirs
RUN mkdir -p /app /var/www

# Install: app
WORKDIR /app
COPY requirements.txt ./
RUN python3.7 -m pip install -r requirements.txt

# Copy Python code
# We only copy the code at a late stage in order to avoid rebuilding the environment on every update
COPY giftshop ./giftshop

# User and runtime folder
USER www-data
WORKDIR /var/www

# Expose
VOLUME /var/www
EXPOSE 5000

# Run
ENV FLASK_APP=/code/giftshop/app.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST 0.0.0.0

CMD flask run -p 5000
