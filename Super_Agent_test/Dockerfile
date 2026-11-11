FROM node:24-bookworm-slim AS node_runtime
FROM hllr:navigation
COPY --from=node_runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node_runtime /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
RUN npm install -g @deepseek-ai/dsh@0.2.1-rc.3 pnpm@11.7.0
WORKDIR /opt/dsh-superagent
COPY upstream/package.json upstream/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY upstream/ ./
RUN pnpm build
