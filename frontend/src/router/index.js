import { createRouter, createWebHistory } from "vue-router";
import LoginView from "@/views/LoginView.vue";
import TaskListView from "@/views/TaskListView.vue";
import CreateTaskView from "@/views/CreateTaskView.vue";
import TaskDetailView from "@/views/TaskDetailView.vue";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/tasks",
    name: "tasks",
    component: TaskListView,
  },
  {
    path: "/tasks/create",
    name: "task-create",
    component: CreateTaskView,
  },
  {
    path: "/tasks/:id",
    name: "task-detail",
    component: TaskDetailView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const publicPages = ["/login"];
  const authRequired = !publicPages.includes(to.path);

  if (authRequired && !token) {
    return next("/login");
  }

  next();
});

export default router;
