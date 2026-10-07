import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

folder = Path(__file__).resolve().parents[1] / "data" / "research"
spec = json.loads((folder / "tdx-traffic-oas.json").read_text(encoding="utf-8-sig"))
print("SERVERS", spec.get("servers"))
for path, methods in spec["paths"].items():
    if "/City/" in path and any(key in path for key in ["VD", "Section", "LiveTraffic", "ETagPair"]):
        print("ENDPOINT", path, methods["get"].get("summary"))
        for param in methods["get"].get("parameters", []):
            if param.get("name") == "City":
                print("CITY_PARAMETER", json.dumps(param, ensure_ascii=False))
root = ET.parse(folder / "vd-static.xml").getroot()
print("XML_ROOT", root.tag)
ns = {"t": "http://traffic.transportdata.tw/standard/traffic/schema/"}
all_vds = root.findall(".//t:VD", ns)
selected = []
for vd in all_vds:
    lat = float(vd.findtext("t:PositionLat", namespaces=ns) or 0)
    lon = float(vd.findtext("t:PositionLon", namespaces=ns) or 0)
    if 24.70 <= lat <= 24.95 and 120.90 <= lon <= 121.15:
        selected.append({tag: vd.findtext("t:" + tag, namespaces=ns) for tag in ["VDID", "RoadName", "LocationMile", "PositionLat", "PositionLon"]})
print("FREEWAY_VD_COUNTS", {"all": len(all_vds), "hsinchu_bounding_box": len(selected)})
(folder / "hsinchu-freeway-vd.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
print("SELECTED_SAMPLE", json.dumps(selected[:8], ensure_ascii=False))
for name in ["m05a-catalog.html", "history-catalog.html"]:
    content = (folder / name).read_text(encoding="utf-8")
    links = re.findall(r'href="([^"]+)"', content)
    print("CATALOG", name, links[:15])
    if name == "m05a-catalog.html":
        print("M05_20261006", [x for x in links if "20261006" in x][:8])
