# Use a base image with Node.js to build the frontend
FROM node:18 AS frontend-builder

WORKDIR /frontend

# Copy only the package.json and package-lock.json for dependency installation
COPY ./frontend/package.json ./frontend/package-lock.json ./
RUN npm install

# Copy the rest of the frontend files and build the frontend
COPY ./frontend ./
RUN npm run build

# Use a base image with Python for the backend
FROM python:3.9-slim

WORKDIR /app

# Copy backend files and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Copy the built frontend files into the Flask app's static folder
COPY --from=frontend-builder /frontend/public ./frontend/public

# Expose the port Flask will run on
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "src/app.py"]