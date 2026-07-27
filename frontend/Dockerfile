# --- Stage 1: build the Angular app ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build:prod

# --- Stage 2: serve the static build with nginx ---
FROM nginx:1.27-alpine
COPY --from=build /app/dist/book-platform /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
