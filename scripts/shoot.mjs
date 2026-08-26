import http from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdirSync } from "node:fs";
import { chromium } from "playwright-core";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "shots");
mkdirSync(OUT, { recursive: true });

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".jpg": "image/jpeg", ".png": "image/png", ".txt": "text/plain" };
const server = http.createServer(async (req, res) => {
  let p = req.url.split("?")[0];
  if (p === "/") p = "/index.html";
  try {
    const data = await readFile(join(ROOT, p));
    res.writeHead(200, { "Content-Type": MIME[extname(p)] || "application/octet-stream" });
    res.end(data);
  } catch {
    res.writeHead(404); res.end("nope");
  }
});
await new Promise(r => server.listen(4173, r));
console.log("server on :4173");

const browser = await chromium.launch({ channel: "chrome", headless: true });
const errors = [];

async function audit(page, label) {
  const m = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    docH: document.body.scrollHeight,
  }));
  console.log(`[${label}] viewport=${m.innerW} scrollWidth=${m.scrollW} pageHeight=${m.docH} ${m.scrollW > m.innerW ? "⚠️ H-OVERFLOW" : "ok"}`);
}

async function settle(page, ms = 1400) {
  await page.waitForTimeout(ms);
  try { await page.evaluate(() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 2500))])); } catch {}
  await page.waitForTimeout(300);
}

async function run(name, viewport, actions) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: name.includes("mobile") ? 2 : 1 });
  const page = await ctx.newPage();
  page.on("console", msg => { if (msg.type() === "error") errors.push(`[${name}] console: ${msg.text()}`); });
  page.on("pageerror", e => errors.push(`[${name}] pageerror: ${e.message}`));
  await page.goto("http://localhost:4173/", { waitUntil: "networkidle", timeout: 45000 }).catch(e => errors.push(`nav: ${e.message}`));
  await settle(page);
  await audit(page, name);
  await actions?.(page, name);
  await ctx.close();
}

await run("mobile-hero", { width: 390, height: 844 }, async (page) => {
  await page.screenshot({ path: `${OUT}/01-mobile-hero.png` });
});

await run("desktop-hero", { width: 1280, height: 720 }, async (page) => {
  await page.screenshot({ path: `${OUT}/02-desktop-hero.png` });
});

await run("mobile-full", { width: 390, height: 844 }, async (page, name) => {
  for (let i = 0; i < 12; i++) { await page.mouse.wheel(0, 700); await page.waitForTimeout(160); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/03-mobile-full.png`, fullPage: true });
});

await run("desktop-full", { width: 1280, height: 720 }, async (page) => {
  for (let i = 0; i < 16; i++) { await page.mouse.wheel(0, 900); await page.waitForTimeout(150); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/04-desktop-full.png`, fullPage: true });
});

await run("interactions-mobile", { width: 390, height: 844 }, async (page, name) => {
  await page.locator('.tab-chip:has-text("United Kingdom")').click();
  await page.waitForTimeout(700);
  await page.locator("#countries").scrollIntoViewIfNeeded();
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/05-tab-uk.png` });

  await page.evaluate(() => document.getElementById("eligibility").scrollIntoView());
  await page.waitForTimeout(500);
  await page.locator('[data-key="dest"] .opt:has-text("Canada")').click();
  await page.waitForTimeout(350);
  await page.locator('[data-key="category"] .opt:has-text("Study Visa")').scrollIntoViewIfNeeded().catch(()=>{});
  await page.locator('[data-key="category"] .opt:has-text("Study Visa")').click();
  await page.waitForTimeout(350);
  await page.locator('[data-key="qual"] .opt:has-text("Bachelor")').first().scrollIntoViewIfNeeded().catch(()=>{});
  await page.locator('[data-key="qual"] .opt[data-val="Bachelor\'s Degree"]').click();
  await page.waitForTimeout(350);
  await page.locator('[data-key="score"] .opt:has-text("60–75%")').click();
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/06-calculator-filled.png` });

  await page.locator("#calcSubmit").click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT}/07-calculator-summary.png` });
  console.log("wa href:", await page.locator("#calcSummary a").getAttribute("href"));

  const journey = await page.evaluate(() => {
    document.getElementById("journeyInner").scrollIntoView({ block: "center" });
    return true;
  });
  await page.waitForTimeout(1200);
  await page.evaluate(() => window.scrollBy(0, 260));
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/08-journey-mid.png` });

  const routeInfo = await page.evaluate(() => {
    const g = document.getElementById("routeGhost"), p = document.getElementById("routeProgress");
    return { ghostD: !!g.getAttribute("d"), progD: !!p.getAttribute("d"),
             dashoffset: getComputedStyle(p).strokeDashoffset };
  });
  console.log("route:", JSON.stringify(routeInfo));
});

console.log(errors.length ? "\n❌ ERRORS:\n" + errors.join("\n") : "\n✅ zero console/page errors");
await browser.close();
server.close();
