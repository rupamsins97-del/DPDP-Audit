FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production \
    PORT=8080 \
    NEXT_PUBLIC_API_URL=https://dpdp-auditor-api-3ryg6y5r3q-el.a.run.app \
    NEXT_PUBLIC_SUPABASE_URL=https://imbhymzwqyfpkdnjnqan.supabase.co \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImltYmh5bXp3cXlmcGtkbmpucWFuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MTMyMTMsImV4cCI6MjEwNTM4OTIxM30.YKtMo0_jjhvOd5iZlS3U6gmjsuzlMk36-RFEgSjJPiI

# Copy package descriptors and install dependencies
COPY package.json ./
RUN npm install

# Copy source code and build
COPY . ./
RUN npm run build

EXPOSE 8080
CMD ["npm", "start", "--", "-p", "8080"]
