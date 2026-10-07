"""Read-only downloads of selected public research sources; no credentials."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCES = {
    "official_proposal_173": ("https://smartsandbox.hsinchu.gov.tw/home/pageproposalcontent.html?ProposalSN=173", "official-proposal-173.html"),
    "official_competition": ("https://smartsandbox.hsinchu.gov.tw/home/pagesmartsand.html", "official-competition.html"),
    "official_how_to_play": ("https://smartsandbox.hsinchu.gov.tw/home/pagehowtoplay.html", "official-how-to-play.html"),
    "official_news": ("https://smartsandbox.hsinchu.gov.tw/home/pagenews.html", "official-news.html"),
    "official_wishpool": ("https://smartsandbox.hsinchu.gov.tw/home/pagewishpage.html", "official-wishpool.html"),
    "freeway_vd_static": ("https://tisvcloud.freeway.gov.tw/history/motc20/VD.xml", "vd-static.xml"),
    "freeway_history_catalog": ("https://tisvcloud.freeway.gov.tw/history-list.php", "history-catalog.html"),
    "freeway_m05_catalog": ("https://tisvcloud.freeway.gov.tw/history/TDCS/M05A/", "m05a-catalog.html"),
    "freeway_m04_catalog": ("https://tisvcloud.freeway.gov.tw/history/TDCS/M04A/", "m04a-catalog.html"),
    "tdx_traffic_oas": ("https://tdx.transportdata.tw/webapi/File/Swagger/V3/7f07d940-91a4-495d-9465-1c9df89d709c", "tdx-traffic-oas.json"),
    "freeway_m05_sample_day": ("https://tisvcloud.freeway.gov.tw/history/TDCS/M05A/20261006/", "m05a-day-catalog.html"),
    "freeway_vdlive_catalog": ("https://tisvcloud.freeway.gov.tw/history/motc20/VDLive/", "vdlive-catalog.html"),
    "freeway_etag_static": ("https://tisvcloud.freeway.gov.tw/history/motc20/ETag.xml", "etag-static.xml"),
    "freeway_tdcs_manual": ("https://tisvcloud.freeway.gov.tw/documents/TDCS%E4%BD%BF%E7%94%A8%E6%89%8B%E5%86%8Av41b.pdf", "tdcs-manual.pdf"),
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", choices=SOURCES)
    args = parser.parse_args()
    output = Path(__file__).resolve().parents[1] / "data" / "research"
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for key in args.sources:
        url, filename = SOURCES[key]
        record = {"source": key, "url": url, "fetched_at": datetime.now(timezone.utc).isoformat()}
        try:
            request = Request(url, headers={"User-Agent": "SandboxProposalResearch/1.0"})
            with urlopen(request, timeout=25) as response:
                payload = response.read(25_000_001)
                if len(payload) > 25_000_000:
                    raise ValueError("Source exceeds research download limit")
                record.update(status=response.status, bytes=len(payload), content_type=response.headers.get("Content-Type"))
            (output / filename).write_bytes(payload)
            record["saved_as"] = filename
        except Exception as error:
            record["error"] = f"{type(error).__name__}: {error}"
        records.append(record)
        print(json.dumps(record, ensure_ascii=False))
    log = output / "source-fetch-log.json"
    previous = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    log.write_text(json.dumps(previous + records, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
