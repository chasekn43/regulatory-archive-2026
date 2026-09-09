// IndexNow + Google GSC + Bing URL Submission — GitHub Actions edition.
//
// Per host:
//   1. Fetches the sitemap and diffs it against scripts/indexnow-state.json.
//   2. Merges today's new/removed URLs with any still-pending URLs from
//      previously failed submissions — nothing is ever lost.
//   3. Submits to IndexNow endpoints in order (Bing first), retrying on 429/5xx.
//      One accepted submission propagates to all IndexNow engines.
//   4. Additionally pushes NEW URLs through the Bing Webmaster URL Submission
//      API (authenticated, per-site quota — immune to IP reputation).
//   5. Submits the updated sitemaps directly to the Google Search Console API.
//   6. Only accepted URLs leave the pending queue; failures retry next run.

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";

const STATE_PATH = fileURLToPath(new URL("./indexnow-state.json", import.meta.url));

export const SETTINGS = {
  retryDelayMs: 5000,
  attemptsPerEndpoint: 2,
  maxBatch: 10000,          // IndexNow max urlList per request
  bingApiMaxPerRun: 100     // stay within the Bing Submission API daily quota
};

export const ENDPOINTS = [
  "https://bing.com",
  "https://seznam.cz",
  "https://indexnow.org"
];

// Clean single entry for your verified active tracking layout
export const HOSTS = [
  {
    host: "charwiz43.github.io",
    sitemap: "https://charwiz43.github.io/BNPL-abuse-fintech-lies-regulatory/sitemap.xml",
    bingSiteUrls: ["https://charwiz43.github.io/BNPL-abuse-fintech-lies-regulatory/"],
    gscSiteUrls: ["https://charwiz43.github.io/BNPL-abuse-fintech-lies-regulatory/"]
  },
  {
    host: "chasekn43.github.io",
    sitemap: "https://chasekn43.github.io/regulatory-archive-2026/sitemap.xml",
    bingSiteUrls: ["https://chasekn43.github.io/regulatory-archive-2026/"],
    gscSiteUrls: ["https://chasekn43.github.io/regulatory-archive-2026/"]
  }
];

const env = process.env;
const DRY_RUN = env.DRY_RUN === "1";

async function main() {
  if (!env.INDEXNOW_KEY) {
    console.error("FATAL: INDEXNOW_KEY is not set");
    process.exit(1);
  }

  let state = {};
  try { state = JSON.parse(await readFile(STATE_PATH, "utf8")); }
  catch { console.log("No state file yet — first run submits the full sitemap."); }

  const reports = [];
  for (const h of HOSTS) {
    try {
      reports.push(await runHost(h, state));
    } catch (e) {
      reports.push({ host: h.host, error: e.message });
    }
  }

  if (!DRY_RUN) {
    await writeFile(STATE_PATH, JSON.stringify(state, null, 1) + "\n");
  }

  const noteworthy = reports.some(r => r.error || r.submission);
  if (noteworthy && !DRY_RUN) {
    try { await sendSummaryNotification(reports); }
    catch (err) { console.error("Email notification bypassed or failed:", err.message); }
  }

  for (const r of reports) {
    console.log(JSON.stringify(r, null, 2));
  }

  if (reports.every(r => r.error)) process.exit(1);
}

function fetchWithTimeout(url, opts = {}) {
  return fetch(url, { ...opts, signal: AbortSignal.timeout(30_000) });
}

async function runHost(config, state) {
  let xml;
  if (env.USE_LOCAL_SITEMAP === "1" && config.host === "chasekn43.github.io") {
    try {
      xml = await readFile("sitemap.xml", "utf8");
    } catch {
      const sitemapRes = await fetchWithTimeout(config.sitemap);
      if (!sitemapRes.ok) return { host: config.host, error: `Sitemap fetch failed: ${sitemapRes.status}` };
      xml = await sitemapRes.text();
    }
  } else {
    const sitemapRes = await fetchWithTimeout(config.sitemap);
    if (!sitemapRes.ok) {
      return { host: config.host, error: `Sitemap fetch failed: ${sitemapRes.status}` };
    }
    xml = await sitemapRes.text();
  }

  // FIXED: Regex match mapping extractor to prevent string split crashing
  const currentUrls = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)]
    .map(m => m[1].trim())
    .filter(u => {
      try { return new URL(u).hostname === config.host; }
      catch { return false; }
    });

  if (currentUrls.length === 0) {
    return { host: config.host, error: "No matching-host URLs found in sitemap" };
  }

  const hostState = state[config.sitemap] ?? state[config.host] ?? { last_urls: [], pending_urls: [] };
  const previousSet = new Set(hostState.last_urls);
  const currentSet = new Set(currentUrls);
  const newUrls = currentUrls.filter(u => !previousSet.has(u));
  const removedUrls = hostState.last_urls.filter(u => !currentSet.has(u));

  const pending = [...new Set([...hostState.pending_urls, ...newUrls, ...removedUrls])];

  state[config.sitemap] = { last_urls: currentUrls, pending_urls: pending };

  if (pending.length === 0) {
    let googleApi = null;
    if (env.GSC_SERVICE_ACCOUNT_KEY && config.gscSiteUrls?.length > 0) {
      googleApi = await submitToGoogleConsole(config.gscSiteUrls, config.sitemap);
    }
    return { host: config.host, sitemap: config.sitemap, totalUrls: currentUrls.length, newUrls: [], removedUrls: [], retriedCount: 0, submission: null, googleApi };
  }

  if (DRY_RUN) {
    return { host: config.host, sitemap: config.sitemap, totalUrls: currentUrls.length, newUrls, removedUrls,
      retriedCount: hostState.pending_urls.length, submission: { dryRun: true, wouldSubmit: pending.length } };
  }

  const submission = await submitToIndexNow(config.host, env.INDEXNOW_KEY, pending);
  state[config.sitemap].pending_urls = submission.failedUrls;

  let bingApi = null;
  if (env.BING_WMT_API_KEY && config.bingSiteUrls.length > 0 && newUrls.length > 0) {
    bingApi = await submitToBingApi(config.bingSiteUrls, newUrls.slice(0, SETTINGS.bingApiMaxPerRun));
    if (newUrls.length > SETTINGS.bingApiMaxPerRun) {
      bingApi.note = `capped at ${SETTINGS.bingApiMaxPerRun} of ${newUrls.length} new URLs (daily quota)`;
    }
  }

  let googleApi = null;
  if (env.GSC_SERVICE_ACCOUNT_KEY && config.gscSiteUrls?.length > 0) {
    googleApi = await submitToGoogleConsole(config.gscSiteUrls, config.sitemap);
  }

  return {
    host: config.host,
    sitemap: config.sitemap,
    totalUrls: currentUrls.length,
    newUrls,
    removedUrls,
    retriedCount: hostState.pending_urls.length,
    submission,
    bingApi,
    googleApi
  };
}

export async function submitToIndexNow(host, key, urls) {
  const attempts = [];
  const failedUrls = [];
  let acceptedCount = 0;

  const chunks = [];
  for (let i = 0; i < urls.length; i += SETTINGS.maxBatch) {
    chunks.push(urls.slice(i, i + SETTINGS.maxBatch));
  }

  for (let i = 0; i < chunks.length; i++) {
    const label = chunks.length > 1 ? ` [batch ${i + 1}/${chunks.length}]` : "";
    const ok = await submitChunk(host, key, chunks[i], attempts, label);
    if (ok) acceptedCount += chunks[i].length;
    else failedUrls.push(...chunks[i]);
  }

  return { ok: failedUrls.length === 0, acceptedCount, failedUrls, attempts };
}

async function submitChunk(host, key, chunk, attempts, label) {
  const body = JSON.stringify({
    host,
    key,
    keyLocation: `https://${host}/${key}.txt`,
    urlList: chunk
  });

  for (const endpoint of ENDPOINTS) {
    for (let attempt = 1; attempt <= SETTINGS.attemptsPerEndpoint; attempt++) {
      let status;
      try {
        const res = await fetchWithTimeout(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=utf-8" },
          body
        });
        status = res.status;
      } catch (err) {
        status = `network error: ${err.message}`;
      }
      attempts.push(`${endpoint}${label} (attempt ${attempt}): ${status}`);

      if (status === 200 || status === 202) return true;

      const retryable = status === 429 || status === 500 || status === 503 || typeof status === "string";
      if (!retryable) break;
      if (attempt < SETTINGS.attemptsPerEndpoint) await sleep(SETTINGS.retryDelayMs);
    }
  }
  return false;
}

async function submitToBingApi(siteUrls, urls) {
  const attempts = [];
  for (const siteUrl of siteUrls) {
    let status, detail = "";
    try {
      const res = await fetchWithTimeout(`https://bing.com{env.BING_WMT_API_KEY}`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ siteUrl, urlList: urls })
      });
      status = res.status;
      if (!res.ok) detail = (await res.text()).slice(0, 200);
    } catch (err) {
      status = `network error: ${err.message}`;
    }
    attempts.push(`SubmitUrlBatch ${siteUrl}: ${status} ${detail}`.trim());
    if (status === 200) return { ok: true, submitted: urls.length, attempts };
  }
  return { ok: false, submitted: 0, attempts };
}

async function getGoogleAccessToken(clientEmail, privateKey) {
  const now = Math.floor(Date.now() / 1000);
  const header = Buffer.from(JSON.stringify({ alg: "RS256", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(JSON.stringify({
    iss: clientEmail,
    scope: "https://googleapis.com",
    aud: "https://googleapis.com",
    exp: now + 3600,
    iat: now
  })).toString("base64url");
  
  const signer = crypto.createSign("RSA-SHA256");
  signer.update(`${header}.${payload}`);
  const signature = signer.sign(privateKey, "base64url");
  const assertion = `${header}.${payload}.${signature}`;
  
  const res = await fetch("https://googleapis.com", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion
    })
  });
  
  if (!res.ok) {
    throw new Error(`Google Auth failed: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();
  return data.access_token;
}

async function submitToGoogleConsole(gscSiteUrls, sitemapUrl) {
  const attempts = [];
  let ok = false;
  
  try {
    const key = JSON.parse(env.GSC_SERVICE_ACCOUNT_KEY);
    const token = await getGoogleAccessToken(key.client_email, key.private_key);
    
    for (const siteUrl of gscSiteUrls) {
      let status, detail = "";
      try {
        const apiPath = `https://googleapis.com{encodeURIComponent(siteUrl)}/sitemaps/${encodeURIComponent(sitemapUrl)}`;
        const res = await fetchWithTimeout(apiPath, {
          method: "PUT",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Length": "0"
          }
        });
        status = res.status;
        if (status !== 204) {
          detail = `error: ${res.status} ${await res.text()}`;
        } else {
          ok = true;
        }
      } catch (err) {
        status = "network error";
        detail = err.message;
      }
      attempts.push(`GSC Submit ${siteUrl}: ${status} ${detail}`.trim());
    }
  } catch (err) {
    attempts.push(`Google Authentication failed: ${err.message}`);
  }
  
  return { ok, attempts };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function sendSummaryNotification(reports) {
  if (!env.RESEND_API_KEY || !env.TO_EMAIL) return;
  const fromEmail = env.FROM_EMAIL || "onboarding@resend.dev";

  const failedHosts = reports.filter(r => r.error || (r.submission && !r.submission.ok));
  const totalNew = reports.reduce((n, r) => n + (r.newUrls?.length ?? 0), 0);
  const totalRemoved = reports.reduce((n, r) => n + (r.removedUrls?.length ?? 0), 0);

  const subject = failedHosts.length > 0
    ? `IndexNow: FAILED (${failedHosts.map(r => r.host).join(", ")}), queued for retry`
    : `IndexNow: OK — ${totalNew} new, ${totalRemoved} removed`;

  const lines = [];
  lines.push(`IndexNow run (GitHub Actions) — ${reports.length} host(s)`);
  lines.push(`Timestamp: ${new Date().toISOString()}`);
  lines.push(``);

  for (const r of reports) {
    const sitemapFilename = r.sitemap && typeof r.sitemap === 'string' ? r.sitemap.split('/').pop() : 'sitemap.xml';
    lines.push(`=== ${r.host} (${sitemapFilename}) ===`);
    if (r.error) { lines.push(`  ERROR: ${r.error}`, ``); continue; }
    if (!r.submission) { lines.push(`  Nothing changed (${r.totalUrls} URLs in sitemap).`, ``); continue; }
    const s = r.submission;
    lines.push(`  IndexNow: ${s.ok ? "OK" : `FAILED, ${s.failedUrls.length} URLs queued for retry`}`);
    lines.push(`  Accepted: ${s.acceptedCount} URLs`);
    if (r.retriedCount > 0) lines.push(`  Retried from previous failed runs: ${r.retriedCount} URLs`);
    lines.push(`  Attempts:`);
    s.attempts.forEach(a => lines.push("    " + a));
    if (r.bingApi) {
      lines.push(`  Bing Submission API: ${r.bingApi.ok ? `OK — ${r.bingApi.submitted} URLs` : "FAILED"}${r.bingApi.note ? ` (${r.bingApi.note})` : ""}`);
      r.bingApi.attempts.forEach(a => lines.push("    " + a));
    }
    if (r.googleApi) {
      lines.push(`  Google Search Console API: ${r.googleApi.ok ? "OK" : "FAILED"}`);
      r.googleApi.attempts.forEach(a => lines.push("    " + a));
    }
    if (r.newUrls?.length > 0) {
      lines.push(`  New URLs (${r.newUrls.length}):`);
      r.newUrls.forEach(u => lines.push("    " + u));
    }
    if (r.removedUrls?.length > 0) {
      lines.push(`  Removed URLs (${r.removedUrls.length}):`);
      r.removedUrls.forEach(u => lines.push("    " + u));
    }
    lines.push(``);
  }

  const res = await fetchWithTimeout("https://resend.com", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: fromEmail,
      to: env.TO_EMAIL,
      subject,
      text: lines.join("\n")
    })
  });
  if (!res.ok) throw new Error(`Resend API ${res.status}: ${await res.text()}`);
}

main();
