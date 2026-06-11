import { createApp } from "vue";
import ElementPlus from "element-plus";

// Element Plus 暗色主题 CSS 变量覆盖
import "element-plus/dist/index.css";
import "./styles/theme.css";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(ElementPlus, { locale: undefined });
app.use(router);
app.mount("#app");
