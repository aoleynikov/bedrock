FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

RUN apk add --no-cache python3

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
