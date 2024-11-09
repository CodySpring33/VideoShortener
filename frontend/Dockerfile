FROM node:18-alpine

WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy configuration files
COPY postcss.config.mjs .
COPY tailwind.config.js .
COPY next.config.js .

# Copy the rest of the application
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/.next && \
    chmod -R 777 /app/.next


# Expose port 3456
EXPOSE 3456

# Start the development server
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

CMD ["npm", "run", "dev"]