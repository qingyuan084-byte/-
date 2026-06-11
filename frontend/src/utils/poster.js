const DOUBAN_HOSTS = [
  "img1.doubanio.com", "img2.doubanio.com", "img3.doubanio.com",
  "img9.doubanio.com", "img.doubanio.com",
];

export function proxyPoster(url) {
  if (!url) return "";
  try {
    const host = new URL(url).hostname;
    if (DOUBAN_HOSTS.some((h) => host === h || host.endsWith("." + h))) {
      return `/api/image-proxy?url=${encodeURIComponent(url)}`;
    }
  } catch {}
  return url;
}

/**
 * 预加载海报：插入 <link rel="preload"> 触发浏览器提前下载
 */
export function preloadPosters(urls, count = 3) {
  urls.slice(0, count).forEach((url) => {
    const proxyUrl = proxyPoster(url);
    if (!proxyUrl) return;
    const link = document.createElement("link");
    link.rel = "preload";
    link.as = "image";
    link.href = proxyUrl;
    link.setAttribute("fetchpriority", "high");
    document.head.appendChild(link);
  });
}

export const placeholderPoster =
  "data:image/svg+xml," +
  "%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='500'%3E" +
  "%3Crect width='1200' height='500' fill='%23111827'/%3E" +
  "%3Ctext x='600' y='260' text-anchor='middle' font-size='64'%3E🎬%3C/text%3E" +
  "%3C/svg%3E";
