"""
Permanent Wayback Machine & Archive.org Snapshot Engine
Submits all live vault endpoints, PDF dockets, topic pages, and exhibits to Web.Archive.org
"""

import urllib.request
import urllib.error
import time

URLS_TO_ARCHIVE = [
    "https://kinslow-regulatory-archive.org/",
    "https://kinslow-regulatory-archive.org/Dear%20Penny.pdf",
    "https://kinslow-regulatory-archive.org/documents/monroe-police-report-26-29572.pdf",
    "https://kinslow-regulatory-archive.org/documents/fraudulent-vendor-emails-and-tracking.pdf",
    "https://kinslow-regulatory-archive.org/documents/mobile-call-history-screenshots.pdf",
    "https://kinslow-regulatory-archive.org/documents/affirm-liability-clearance-july16.pdf",
    "https://kinslow-regulatory-archive.org/documents/affirm-managing-counsel-directive-july17.pdf",
    "https://kinslow-regulatory-archive.org/documents/cfpb-complaint-and-affirm-false-response.pdf",
    "https://kinslow-regulatory-archive.org/documents/morgan-lewis-correspondence.pdf",
    "https://kinslow-regulatory-archive.org/documents/louisiana-ag-dispute-submission.pdf",
    "https://kinslow-regulatory-archive.org/documents/california-ag-dispute-notice.pdf",
    "https://kinslow-regulatory-archive.org/documents/ca-ag-reply-1553638.pdf",
    "https://kinslow-regulatory-archive.org/documents/the-consumer-survival-playbook-udaap-escalation.pdf",
    "https://kinslow-regulatory-archive.org/documents/a-bizarre-legal-paradox-inside-affirms-cd-order.pdf",
    "https://kinslow-regulatory-archive.org/documents/sec-form-tcr-submission-confirmation-17867-223-108-883.pdf",
    "https://kinslow-regulatory-archive.org/documents/california-state-bar-misconduct-complaint-morgan-lewis.pdf",
    "https://kinslow-regulatory-archive.org/documents/all-linkedin-posts-archive.md",
    "https://kinslow-regulatory-archive.org/topics/affirm-cfpb-complaint-database-bbb-case-logs.html",
    "https://kinslow-regulatory-archive.org/topics/behind-the-portal-fintech-executive-aliases-disputes.html",
    "https://kinslow-regulatory-archive.org/topics/affirm-frozen-account-communication-paradox.html",
    "https://kinslow-regulatory-archive.org/topics/affirm-dispute-denied-automated-bot-guide.html",
    "https://kinslow-regulatory-archive.org/topics/affirm-account-locked-during-dispute-solution.html",
    "https://kinslow-regulatory-archive.org/topics/affirm-capital-stack-abs-warehouse-facility-risks.html",
    "https://kinslow-regulatory-archive.org/topics/affirm-institutional-whistleblower-memorandum.html",
    "https://kinslow-regulatory-archive.org/topics/regulation-z-apa-compliance.html",
    "https://kinslow-regulatory-archive.org/topics/fintech-bnpl-merchant-dispute-resolution.html",
    "https://kinslow-regulatory-archive.org/topics/udaap-customer-service-failures.html",
    "https://kinslow-regulatory-archive.org/topics/california-ag-regulatory-rebuttal.html",
    "https://kinslow-regulatory-archive.org/topics/bnpl-billing-disputes-regulation-z.html",
    "https://kinslow-regulatory-archive.org/topics/apa-fintech-rulemaking-exemptions.html",
    "https://kinslow-regulatory-archive.org/topics/tila-12cfr1026-closed-end-dispute-mechanics.html",
    "https://kinslow-regulatory-archive.org/topics/apa-notice-and-comment-reliance-defenses.html",
    "https://kinslow-regulatory-archive.org/topics/fintech-sox-ledger-friction-chargebacks.html",
    "https://kinslow-regulatory-archive.org/guides/affirm-bank-billpay-workaround.html",
    "https://kinslow-regulatory-archive.org/guides/affirm-dispute-denied-returned-item.html",
    "https://kinslow-regulatory-archive.org/guides/affirm-ceo-executive-contacts-escalation.html",
    "https://kinslow-regulatory-archive.org/guides/affirm-credit-bureau-dispute-letters.html",
    "https://kinslow-regulatory-archive.org/guides/affirm-merchant-return-tracking-proof.html",
    "https://kinslow-regulatory-archive.org/press-release.html",
    "https://github.com/chasekn43/regulatory-archive-2026",
    "https://chasekinslow1.substack.com/p/anatomy-of-an-atypical-consumer-dispute"
]

def submit_to_wayback(url):
    save_url = f"https://web.archive.org/save/{url}"
    req = urllib.request.Request(
        save_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return str(e)

def main():
    print(f"=== Submitting {len(URLS_TO_ARCHIVE)} URLs to Wayback Machine / Archive.org ===")
    success = 0
    for idx, url in enumerate(URLS_TO_ARCHIVE, 1):
        print(f"[{idx}/{len(URLS_TO_ARCHIVE)}] Archiving: {url} ...", end=" ", flush=True)
        status = submit_to_wayback(url)
        print(f"Status: {status}")
        if status in [200, 302, "200", "302"]:
            success += 1
        time.sleep(1.5) # respectful delay
    print(f"\nCompleted: {success}/{len(URLS_TO_ARCHIVE)} successfully queued for permanent snapshot.")

if __name__ == "__main__":
    main()
