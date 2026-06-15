import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import EditorView from "../views/EditorView.vue";
import DetailView from "../views/DetailView.vue";
import StatsView from "../views/StatsView.vue";
import SearchView from "../views/SearchView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  { path: "/editor", name: "editor", component: EditorView },
  { path: "/editor/:id", name: "editor-edit", component: EditorView, props: true },
  { path: "/log/:id", name: "detail", component: DetailView, props: true },
  { path: "/stats", name: "stats", component: StatsView },
  { path: "/search", name: "search", component: SearchView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
