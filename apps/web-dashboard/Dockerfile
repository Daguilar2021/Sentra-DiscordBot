FROM node:24-bookworm-slim

WORKDIR /workspace/apps/web-dashboard

COPY apps/web-dashboard/package*.json ./
RUN npm ci

COPY apps/web-dashboard/. ./

EXPOSE 4200

CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "4200"]
