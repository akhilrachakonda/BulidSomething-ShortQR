# Stage 1: Build the React application
FROM node:20-alpine as builder

WORKDIR /app

# Copy package manifests and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# In production, API calls will be relative to the domain (e.g., /api/links).
# Setting VITE_API_BASE to an empty string ensures this.
ENV VITE_API_BASE=""

# Build the static files
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:stable-alpine

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files from the builder stage to Nginx's web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 for the web server
EXPOSE 80

# The default Nginx command starts the server. We add `daemon off;` to run it in the foreground.
CMD ["nginx", "-g", "daemon off;"]