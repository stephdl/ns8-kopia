//
// Copyright (C) 2023 Nethesis S.r.l.
// SPDX-License-Identifier: GPL-3.0-or-later
//
import Vue from "vue";
import VueRouter from "vue-router";
import Status from "../views/Status.vue";
import Clients from "../views/Clients.vue";
import Policies from "../views/Policies.vue";
import Alerts from "../views/Alerts.vue";
import Settings from "../views/Settings.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "Status",
    component: Status,
    alias: "/status", // important
  },
  {
    path: "/clients",
    name: "Clients",
    component: Clients,
  },
  {
    path: "/policies",
    name: "Policies",
    component: Policies,
  },
  {
    path: "/alerts",
    name: "Alerts",
    component: Alerts,
  },
  {
    path: "/settings",
    name: "Settings",
    component: Settings,
  },
  {
    path: "/about",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/About.vue"),
  },
];

const router = new VueRouter({
  base: process.env.BASE_URL,
  routes,
});

export default router;
