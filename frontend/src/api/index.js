import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

// 统一响应处理
client.interceptors.response.use(
  (response) => {
    const body = response.data;
    if (body.code !== 0) {
      const err = new Error(body.msg || "请求失败");
      err.code = body.code;
      throw err;
    }
    return body.data;
  },
  (error) => {
    const msg = error.response?.data?.msg || error.message || "网络错误";
    const err = new Error(msg);
    err.code = error.response?.status ?? 0;
    throw err;
  }
);

// ── 日志 ──

export function getLogs(params = {}) {
  return client.get("/logs", { params });
}

export function createLog(data) {
  return client.post("/logs", data);
}

export function getLog(id) {
  return client.get(`/logs/${id}`);
}

export function updateLog(id, data) {
  return client.put(`/logs/${id}`, data);
}

export function deleteLog(id) {
  return client.delete(`/logs/${id}`);
}

// ── 标签 ──

export function getTags() {
  return client.get("/tags");
}

export function createTag(data) {
  return client.post("/tags", data);
}

export function deleteTag(id) {
  return client.delete(`/tags/${id}`);
}

// ── 统计 ──

export function getHeatmap() {
  return client.get("/stats/heatmap");
}

export function getSummary() {
  return client.get("/stats/summary");
}

export function getDaily() {
  return client.get("/stats/daily");
}
