// node pub_reel.mjs <mp4> <capa.jpg> "<key>"  (env: INSTAGRAM_ACCESS_TOKEN)
import fs from "fs";
const [mp4, capa, key] = process.argv.slice(2);
const T = process.env.INSTAGRAM_ACCESS_TOKEN;
if (!T) throw new Error("INSTAGRAM_ACCESS_TOKEN ausente");
const BASE = "https://raw.githubusercontent.com/adamressel7-web/gtav1-br-media/main/reels/";
const md = fs.readFileSync("/home/claude/gtav1-br-media/legendas_reels.md", "utf8");
const sec = md.split(/^## /m).find(s => s.startsWith(key + " ") || s.startsWith(key + "\n"));
if (!sec) throw new Error("legenda não encontrada: " + key);
const caption = sec.split("\n").slice(1).join("\n").trim();
const G = "https://graph.instagram.com/v23.0";
const api = async (path, params, method = "POST") => {
  const u = new URL(G + path); const body = new URLSearchParams({ ...params, access_token: T });
  const r = method === "GET" ? await fetch(u + "?" + body) : await fetch(u, { method, body });
  const j = await r.json(); if (j.error) { const e = new Error(j.error.message); Object.assign(e, j.error); throw e; } return j;
};
const wait = ms => new Promise(r => setTimeout(r, ms));
const c = await api("/me/media", { media_type: "REELS", video_url: BASE + mp4, cover_url: BASE + capa, caption, share_to_feed: "true" });
console.log("container", c.id);
for (let i = 0; i < 60; i++) {
  await wait(10000);
  const s = await api("/" + c.id, { fields: "status_code,status" }, "GET");
  if (s.status_code === "FINISHED") break;
  if (s.status_code === "ERROR") throw new Error("processamento: " + s.status);
  if (i === 59) throw new Error("timeout");
}
await wait(5000);
const p = await api("/me/media_publish", { creation_id: c.id });
const m = await api("/" + p.id, { fields: "permalink" }, "GET");
console.log("OK " + m.permalink);
