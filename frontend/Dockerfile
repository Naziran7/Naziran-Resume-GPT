# Stage 1: Build React Application
FROM node:22-alpine AS build

WORKDIR /app

# Copy package dependencies and install
COPY package*.json ./
RUN npm install

# Copy source and build production bundle
COPY . .
RUN npm run build

# Stage 2: Serve Bundle with Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
