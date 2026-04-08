<template>
  <div>
    <AppNav />
    <router-view />
  </div>
</template>

<script setup>
import AppNav from "./components/AppNav.vue";
</script>

<style>
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
  background: #f5f7fb;
  color: #222;
}
* {
  box-sizing: border-box;
}
a {
  text-decoration: none;
}
</style>
