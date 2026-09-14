import os
import re

def update_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add 2026 Macro & Regulatory Compliance Intelligence Hub right after the abstract or before Portal I
    macro_hub_html = """
    <!-- 2026 MACRO & REGULATORY COMPLIANCE INTELLIGENCE HUB -->
    <section id="macro-intelligence-hub" style="margin-bottom: 40px; background: linear-gradient(135deg, #0b1329 0%, #172554 50%, #0f172a 100%); border: 2px solid var(--accent); border-radius: 12px; padding: 28px; box-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);">
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; border-bottom: 2px solid rgba(56, 189, 248, 0.3); padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 26px;">📡</span>
          <div>
            <h2 style="margin: 0; font-size: 22px; color: #ffffff; border-bottom: none; padding-bottom: 0;">2026 Macro &amp; Regulatory Compliance Intelligence Hub</h2>
            <div style="font-size: 13px; color: var(--accent); font-weight: 600;">Real-Time Financial Modeling, CFPB Regulation Z Rulemaking Timeline, and Industry Risk Audits</div>
          </div>
        </div>
        <span class="badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8;">2026 Live Intelligence</span>
      </div>

      <p style="color: #cbd5e1; font-size: 14.5px; line-height: 1.6; margin-bottom: 20px;">
        As Buy Now Pay Later (BNPL) originators evolve from transactional zero-interest checkout carts into full-scale 36% APR consumer installment lenders, macro credit risk, credit loss provisions, and regulatory supervision have escalated. This intelligence hub synthesizes breaking 2026 federal rulemaking, SEC earnings filings, and empirical forensic dockets.
      </p>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); gap: 16px; margin-bottom: 22px;">
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 18px;">
          <div style="font-size: 11px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">🏛️ CFPB Regulation Z Timeline</div>
          <h4 style="color: #ffffff; font-size: 15px; margin-bottom: 8px;">12 C.F.R. § 1026 Notice-and-Comment Codification</h4>
          <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5; margin: 0;">
            Following the May 2025 enforcement stay in <em>FTA v. CFPB</em>, the Bureau is advancing notice-and-comment rulemaking to codify BNPL providers as credit card issuers, mandating 60-day billing error dispute rights and fee disclosures across 2026.
          </p>
        </div>

        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 18px;">
          <div style="font-size: 11px; font-weight: 800; color: #f59e0b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">📈 Affirm Q2 2026 Earnings &amp; 36% APR</div>
          <h4 style="color: #ffffff; font-size: 15px; margin-bottom: 8px;">$13.8B GMV &amp; 71% Interest-Bearing Volume</h4>
          <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5; margin: 0;">
            Affirm's Q2 2026 results reveal total GMV reaching $13.8 Billion (+35% YoY), with 71% of transaction volume originating in interest-bearing installment loans reaching up to 36% APR, shifting revenue dependence toward subprime consumer interest.
          </p>
        </div>

        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 18px;">
          <div style="font-size: 11px; font-weight: 800; color: #ef4444; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">⚠️ Delinquencies &amp; Credit Losses</div>
          <h4 style="color: #ffffff; font-size: 15px; margin-bottom: 8px;">40% Surge in Provisions to $214M</h4>
          <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5; margin: 0;">
            30+ day consumer delinquencies increased by 18 bps YoY (2.4%), driving a 40% year-over-year surge in credit loss provisions to $214 Million. Debt stacking and unapplied merchant returns accelerate asset-backed securitization (ABS) covenant strain.
          </p>
        </div>
      </div>

      <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: flex-start; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
        <a href="topics/genesis-of-bnpl-installment-loans.html" style="display: inline-flex; align-items: center; gap: 6px; background: var(--accent); color: #0b0f19; font-weight: 700; font-size: 13px; padding: 10px 18px; border-radius: 6px; text-decoration: none; transition: all 0.2s;">
          📖 Read Genesis of BNPL &amp; 36% APR Treatise →
        </a>
        <a href="topics/affirm-investor-regulatory-dossier-risk-audit.html" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.08); border: 1px solid var(--border); color: #ffffff; font-weight: 600; font-size: 13px; padding: 10px 18px; border-radius: 6px; text-decoration: none; transition: all 0.2s;">
          📊 2026 Investor Dossier &amp; ABS Risk Audit →
        </a>
        <a href="llms.txt" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #10b981; font-weight: 600; font-size: 13px; padding: 10px 18px; border-radius: 6px; text-decoration: none;">
          🤖 Machine-Readable AI Grounding (/llms.txt) →
        </a>
      </div>
    </section>
    """

    # Check if macro hub already exists
    if 'id="macro-intelligence-hub"' not in html:
        # Insert before Portal I
        portal1_tag = '<section id="portal-research-library"'
        if portal1_tag in html:
            html = html.replace(portal1_tag, macro_hub_html + '\n    ' + portal1_tag)
        else:
            print("Warning: portal-research-library not found in", filepath)

    # 2. Add New Topic Cards to Portal I
    new_portal1_cards = """
        <div class="doc-card" role="listitem" style="border: 2px solid var(--accent); background: rgba(56, 189, 248, 0.05);">
          <div>
            <div class="doc-type" style="color: var(--accent);">2026 Cornerstone Treatise</div>
            <h3 class="doc-title" style="font-size: 16px; margin: 8px 0;">Genesis of BNPL: From Micro-Installments to 36% APR Risk Engine</h3>
            <p class="doc-desc">From zero-interest checkout carts to 36% APR risk engines: dissecting merchant fees, regulatory arbitrage, credit loss spikes, and the 2026 CFPB timeline.</p>
          </div>
          <a href="topics/genesis-of-bnpl-installment-loans.html" class="btn-doc" style="background: var(--accent); color: #0b0f19; font-weight: 800;">Read Full Treatise →</a>
        </div>

        <div class="doc-card" role="listitem" style="border: 1px solid #f59e0b;">
          <div>
            <div class="doc-type" style="color: #f59e0b;">Investor Regulatory Dossier</div>
            <h3 class="doc-title" style="font-size: 16px; margin: 8px 0;">Affirm 2026 Investor Dossier &amp; Capital Stack Risk Audit</h3>
            <p class="doc-desc">Empirical audit of warehouse facility covenants, ABS repurchase triggers on unapplied merchant refunds, and SOX 404 internal control vulnerabilities.</p>
          </div>
          <a href="topics/affirm-investor-regulatory-dossier-risk-audit.html" class="btn-doc" style="background: #f59e0b; color: #0b0f19; font-weight: 700;">Read Investor Dossier →</a>
        </div>
    """

    if 'genesis-of-bnpl-installment-loans.html' not in html:
        # Insert after <div class="doc-grid" role="list"> in Portal I
        doc_grid_marker = '<section id="portal-research-library"'
        p1_start = html.find(doc_grid_marker)
        if p1_start != -1:
            grid_start = html.find('<div class="doc-grid" role="list">', p1_start)
            if grid_start != -1:
                insert_pos = grid_start + len('<div class="doc-grid" role="list">')
                html = html[:insert_pos] + '\n' + new_portal1_cards + html[insert_pos:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated successfully:", filepath)

# Update both repos
update_html(r'C:\Users\Charwiz43\OneDrive\Desktop\SEO ENGINE\regulatory-archive-worker\index.html')
update_html(r'C:\Users\Charwiz43\OneDrive\Desktop\SEO ENGINE\regulatory-archive-2026\index.html')
