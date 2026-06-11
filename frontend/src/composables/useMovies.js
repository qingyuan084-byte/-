import { ref, computed } from "vue";
import { getMovieListRich, getBannerMovies } from "@/api/index.js";
import { preloadPosters } from "@/utils/poster.js";

const MOCK_MOVIES = [
  { movie_id: "1292052", title: "肖申克的救赎", rating: 9.7, year: 1994, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p480747492.webp", genres: "剧情, 犯罪", summary: "银行家安迪因被误判杀害妻子及情人而入狱，在肖申克监狱中他凭借才智与毅力最终重获自由的故事。" },
  { movie_id: "1291546", title: "霸王别姬", rating: 9.6, year: 1993, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p2911205318.webp", genres: "剧情, 爱情, 同性", summary: "段小楼与程蝶衣从小在京剧班学艺，两人合演《霸王别姬》名震京师，历经半个世纪的悲欢离合。" },
  { movie_id: "1292722", title: "泰坦尼克号", rating: 9.5, year: 1998, poster_url: "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p457760035.webp", genres: "剧情, 爱情, 灾难", summary: "穷画家杰克和贵族少女露丝在泰坦尼克号上坠入爱河，巨轮撞上冰山沉没的生死诀别。" },
  { movie_id: "1295644", title: "这个杀手不太冷", rating: 9.4, year: 1994, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p511118051.webp", genres: "剧情, 动作, 犯罪", summary: "职业杀手莱昂救下被灭门的小女孩玛蒂尔达，两人在相处中产生了超越年龄的温情。" },
  { movie_id: "1292063", title: "美丽人生", rating: 9.5, year: 1997, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2578474613.webp", genres: "剧情, 喜剧, 爱情, 战争", summary: "犹太人圭多为了保护儿子的心灵，在纳粹集中营中编造了一场游戏，用父爱照亮了黑暗。" },
  { movie_id: "1291561", title: "千与千寻", rating: 9.4, year: 2001, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p2557573348.webp", genres: "动画, 奇幻, 冒险", summary: "少女千寻误入神灵世界，父母被变成猪，她必须在汤屋工作并寻找拯救父母的方法。" },
  { movie_id: "1295124", title: "辛德勒的名单", rating: 9.5, year: 1993, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p492406163.webp", genres: "剧情, 历史, 战争", summary: "德国商人辛德勒在二战期间倾家荡产，拯救了 1100 名犹太人的生命。" },
  { movie_id: "3541415", title: "盗梦空间", rating: 9.4, year: 2010, poster_url: "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p513344864.webp", genres: "科幻, 悬疑, 冒险", summary: "专业窃贼柯布进入他人梦境窃取秘密，为回家见孩子接受了一项不可能的任务——植入思想。" },
  { movie_id: "1292064", title: "楚门的世界", rating: 9.4, year: 1998, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p479682972.webp", genres: "剧情, 科幻", summary: "楚门从出生就生活在一个巨大的真人秀片场中，所有人都是演员，只有他被蒙在鼓里。" },
  { movie_id: "1889243", title: "星际穿越", rating: 9.4, year: 2014, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2614988097.webp", genres: "科幻, 冒险, 剧情", summary: "未来地球环境恶化，前 NASA 飞行员库珀穿越虫洞寻找人类新家园的史诗之旅。" },
  { movie_id: "1291560", title: "龙猫", rating: 9.2, year: 1988, poster_url: "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p2540924496.webp", genres: "动画, 奇幻, 冒险", summary: "姐妹俩搬到乡下后，遇见了森林中的精灵龙猫，展开了一段充满童真的奇幻冒险。" },
  { movie_id: "1300267", title: "乱世佳人", rating: 9.3, year: 1939, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p1963126880.webp", genres: "剧情, 爱情, 历史, 战争", summary: "美国南北战争时期，南方庄园主之女斯嘉丽在乱世中的爱与生存。" },
  { movie_id: "1929463", title: "少年派的奇幻漂流", rating: 9.1, year: 2012, poster_url: "https://img2.doubanio.com/view/photo/s_ratio_poster/public/p1784592701.webp", genres: "剧情, 奇幻, 冒险", summary: "印度少年派在海上与一只孟加拉虎共度 227 天的漂流求生之旅。" },
  { movie_id: "1292215", title: "天使爱美丽", rating: 8.7, year: 2001, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2447590313.webp", genres: "喜剧, 爱情", summary: "巴黎女孩艾米丽通过一系列善意的小举动改变身边人生活，自己也找到了爱情。" },
  { movie_id: "1293350", title: "两杆大烟枪", rating: 9.1, year: 1998, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p792443418.webp", genres: "喜剧, 犯罪", summary: "伦敦小混混艾德和朋友卷入黑帮、毒贩的连环套中，笑料百出的黑色幽默经典。" },
  { movie_id: "1302425", title: "喜剧之王", rating: 8.8, year: 1999, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2618313392.webp", genres: "喜剧, 剧情, 爱情", summary: "跑龙套演员尹天仇对演戏的执着追求，以及他与舞女柳飘飘的动人爱情故事。" },
  { movie_id: "1292217", title: "穆赫兰道", rating: 8.4, year: 2001, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p792248233.webp", genres: "悬疑, 惊悚, 剧情", summary: "好莱坞穆赫兰道上的一场车祸引出了一个关于梦与现实交织的迷离故事。" },
  { movie_id: "1304447", title: "记忆碎片", rating: 8.7, year: 2000, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p641688453.webp", genres: "悬疑, 惊悚, 犯罪", summary: "患有短期失忆症的莱纳德通过纹身和便条追踪杀害妻子的凶手，叙事结构天才之作。" },
  { movie_id: "1306029", title: "美丽心灵", rating: 9.1, year: 2001, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p1665997400.webp", genres: "剧情, 传记", summary: "数学家约翰·纳什在精神分裂症的困扰下，凭借意志力和妻子的爱获得诺贝尔奖。" },
  { movie_id: "1293182", title: "十二怒汉", rating: 9.4, year: 1957, poster_url: "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2173577632.webp", genres: "剧情, 犯罪", summary: "12 名陪审员在密室中对一桩看似铁证的谋杀案展开辩论，一人之力扭转全局。" },
  { movie_id: "1306249", title: "唐伯虎点秋香", rating: 8.8, year: 1993, poster_url: "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p2357915564.webp", genres: "喜剧, 爱情, 古装", summary: "江南才子唐伯虎为追求华府丫鬟秋香，混入华府做低等佣人，笑料百出。" },
  { movie_id: "1291858", title: "鬼子来了", rating: 9.3, year: 2000, poster_url: "https://img1.doubanio.com/view/photo/s_ratio_poster/public/p2553104888.webp", genres: "剧情, 喜剧, 战争", summary: "抗战末期，一个日本俘虏和翻译官被塞给河北村民看管，引发了一系列荒诞而悲剧的事件。" },
];

const categoryKeywords = {
  suspense: ["悬疑", "惊悚", "犯罪", "推理"],
  comedy: ["喜剧", "搞笑"],
  scifi: ["科幻", "奇幻", "冒险"],
  action: ["动作", "战争", "武侠"],
};

export function formatGenres(g) {
  if (!g) return "";
  if (Array.isArray(g)) return g.slice(0, 3).join(" · ");
  return String(g).split(/[,，]/).slice(0, 3).join(" · ");
}

export function truncate(s, n) {
  if (!s) return "";
  return s.length > n ? s.slice(0, n) + "……" : s;
}

export function useMovies() {
  const allMovies = ref([]);
  const bannerMovies = ref([]);
  const loading = ref({
    banner: true, hot: true, newest: true, top: true,
    categories: true, sidebar: true, search: false,
  });

  async function fetchMovies() {
    try {
      const data = await getMovieListRich({ pageSize: 100, sortBy: "rating" });
      const items = data.items || [];
      if (items.length > 0) {
        allMovies.value = items;
      }
    } catch {
      console.warn("[useMovies] API 不可用，使用 Mock 数据");
    }
    if (allMovies.value.length === 0) {
      allMovies.value = MOCK_MOVIES.map((m) => ({ ...m, similarity_score: 0 }));
    }
  }

  async function fetchNewestMovies() {
    try {
      const data = await getMovieListRich({ pageSize: 20, sortBy: "year" });
      const items = data.items || [];
      if (items.length > 0) {
        newestMoviesAll.value = items;
        return;
      }
    } catch {
      console.warn("[useMovies] 最新电影 API 不可用");
    }
  }

  async function fetchBannerMovies() {
    try {
      const data = await getBannerMovies(10);
      if (data && data.length > 0) {
        bannerMovies.value = data;
        preloadPosters(
          data.map((m) => m.poster_url).filter(Boolean),
          3,
        );
      }
    } catch {
      const shuffled = [...baseMovies.value].sort(() => Math.random() - 0.5);
      bannerMovies.value = shuffled.slice(0, 10);
    }
    loading.value.banner = false;
  }

  const baseMovies = computed(() => allMovies.value);

  const hotMoviesAll = computed(() =>
    [...baseMovies.value].sort((a, b) => b.rating - a.rating)
  );

  const newestMoviesAll = ref([]);

  const topMoviesAll = computed(() =>
    [...baseMovies.value].filter((m) => m.rating >= 8.5).sort((a, b) => b.rating - a.rating)
  );

  function getCatMoviesAll(key) {
    const keywords = categoryKeywords[key] || [];
    return baseMovies.value
      .filter((m) => {
        const gs = formatGenres(m.genres);
        return keywords.some((kw) => gs.includes(kw));
      })
      .sort((a, b) => b.rating - a.rating);
  }

  const topRankMovies = computed(() =>
    [...baseMovies.value].sort((a, b) => b.rating - a.rating).slice(0, 10)
  );

  const hotTags = computed(() => {
    const count = {};
    baseMovies.value.forEach((m) => {
      const gs = formatGenres(m.genres);
      if (!gs) return;
      gs.split(" · ").forEach((g) => {
        if (g.trim()) count[g.trim()] = (count[g.trim()] || 0) + 1;
      });
    });
    return Object.entries(count)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, cnt], i) => ({ name, count: cnt, hue: (i * 37 + 10) % 360 }));
  });

  function markLoaded() {
    loading.value.hot = false;
    loading.value.newest = false;
    loading.value.top = false;
    loading.value.categories = false;
    loading.value.sidebar = false;
  }

  return {
    allMovies, loading, baseMovies,
    bannerMovies, hotMoviesAll, newestMoviesAll, topMoviesAll,
    getCatMoviesAll, topRankMovies, hotTags,
    fetchMovies, fetchBannerMovies, fetchNewestMovies, markLoaded, categoryKeywords,
  };
}
