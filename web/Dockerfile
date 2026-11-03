FROM node:22-bookworm AS build
WORKDIR /app
ARG ANGULAR_BUILD_CONFIGURATION=development
ARG AUTH_SERVICE_ORIGIN
ARG API_SERVICE_ORIGIN
ENV AUTH_SERVICE_ORIGIN=${AUTH_SERVICE_ORIGIN}
ENV API_SERVICE_ORIGIN=${API_SERVICE_ORIGIN}
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration=${ANGULAR_BUILD_CONFIGURATION}

FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/workshop-login-frontend/browser /usr/share/nginx/html
EXPOSE 80
