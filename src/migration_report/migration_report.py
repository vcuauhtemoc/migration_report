import pandas as pd
import json 
import os
from typing import Union
import re
from pprint import pprint
import logging
logger = logging.getLogger(__name__)
from datetime import datetime as dt

def parse_json(path) -> Union[dict,None]:
    result = {
        "rx_olt": "",
        "rx_ont": "",
        "olt": "",
        "csw": "",
        "hosts": [],
    }
    with open(path) as j:
        try:
            service_dict = json.load(j)
        except Exception as ex:
            print(f"Not a JSON:{ex.args[0]}")
            return None
        try:
            service_dict = service_dict[0]
        except Exception as ex:
            print(ex.args[0])
            print("json contents:")
            print(service_dict)
            return None
        result["rx_ont"] = service_dict["ont"]["UPLINK"]["GPON"]["ONT"]["Receive Power"]
        result["rx_olt"] = service_dict["ont"]["UPLINK"]["GPON"]["OLT"]["Receive Power"]
        result["olt"] = service_dict["olt"]["hostname"]
        vlans = service_dict["vlans"].keys()
        for e in vlans:
            macs = service_dict["vlans"][e]["mac_table"]
            for index,host in enumerate(macs):
                if type(host) != dict:
                    hostname = index
                    result["hosts"].append({
                        "mac" : host
                    })
                    continue 
                elif not host.get("ip"):
                    hostname = index
                else:
                    hostname = host.get("ip")
                result["hosts"].append({
                    "ip": host.get("ip"),
                    "mac" : host.get("mac"),
                    "vlan-id" : host.get("tag"),
                    "interface": host.get("csw_interface")
                })
        for host in result["hosts"]:
            if host.get("mac") and not host.get("ip"):
                host["ip"] = "No IP found"
        result["csw"] = service_dict["olt"]["access_switch"]
        return result


def compare_result(pre: dict, post: dict,sid: str):
    result = {}
    logging.debug("pre-check:")
    logging.debug(pre)
    logging.debug("post-check")
    logging.debug(post)
    is_gpon = False
    if "-" in str(post.get("olt")):
        is_gpon = True
    warn_low : int = -26
    gpon_warn_low : int = -28
    warn_high : int = -9

    if is_gpon:
        warn_low = gpon_warn_low
    try:
        if (warn_low > int(post["rx_olt"])) or (int(post["rx_olt"]) > warn_high):
            result["olt_light_alert"] = f"BAD ({post["rx_olt"]})"

        if (warn_low > int(post["rx_ont"])) or (int(post["rx_ont"]) > warn_high):
            result["ont_light_alert"] = f"BAD ({post["rx_ont"]})"

        hostlist = lambda hosts: [(h.get("ip"),h.get("mac")) for h in hosts]
        host_check_pre = hostlist(pre.get("hosts"))
        host_check_post = hostlist(post.get("hosts"))

        for index,host in enumerate(host_check_pre):
            index = index - 1
            if host not in host_check_post:
                if not result.get("missing_arp_alert"):
                    result["missing_arp_alert"] = []
                result["missing_arp_alert"].append(pre["hosts"][index])
                result["missing_arp_alert"][index]["prev. CSW"] = pre.get("csw")
    except Exception as ex:
        logging.info(f"Failed to verify s{sid}, please check manually.")
        logging.debug(ex.args[0])
        logging.debug("pre-check:")
        logging.debug(pre)
        logging.debug("post-check")
        logging.debug(post)
        return None
    if not result:
        return None
    return result
        
def generate_report(pre_dir,post_dir):
    services_pre = {}
    services_post = {}
    
    for file in os.listdir(pre_dir):
        filename = os.path.basename(file)
        slice_index = filename.find('.')
        service_id = filename[:slice_index]
        analyze_service = parse_json(f"{pre_dir}/{file}")
        if analyze_service:
            services_pre[service_id] = analyze_service
    # print(json.dumps(services_pre,indent=4))

    for file in os.listdir(post_dir):
        filename = os.path.basename(file)
        slice_index = filename.find('.')
        service_id = filename[:slice_index]
        analyze_service = parse_json(f"{post_dir}/{file}")
        if analyze_service:
            services_post[service_id] = analyze_service

    services_affected = {}
    for sname,content in services_pre.items():
        comparison = compare_result(content,services_post.get(sname),sname)
        if comparison:
            services_affected[sname] = comparison
    sa_df = pd.DataFrame.from_dict(services_affected,orient="index")
    sa_df.index.name = "Service ID"
    sa_df.rename(
        columns={
        "ont_light_alert": "ONT Rx Level",
        "olt_light_alert": "OLT Rx Level",
        },
    inplace=True
    )
    
    sa_df = sa_df.explode("missing_arp_alert")
    sa_df[["Prev IP", "MISSING MAC","prev. VLAN","prev. int","prev. csw"]] = sa_df["missing_arp_alert"].apply(
        lambda t: pd.Series(t) if pd.notnull(t) else pd.Series([None, None])
    )
    sa_df.drop("missing_arp_alert", axis=1, inplace=True)
    sa_df.fillna("N/A",inplace=True)
    print()
    print("Issues after migration:")
    print()
    print(sa_df.to_markdown(tablefmt="rounded_outline"))
    print()
    now = dt.now()
    timestamp = int(now.timestamp())
    print(timestamp)
    sa_df.to_csv(f"services_affected_{timestamp}.csv")

def test():
    services = {}
    for file in os.listdir("src/migration_report/analyze"):
        svc_timestamp = re.search(r"\d+\.\d+",file)
        if not svc_timestamp:
            continue
        svc_timestamp = svc_timestamp.group(0)
        if os.path.islink(f"src/migration_report/analyze/{file}"):
            continue
        analyze_service = parse_json(f"src/migration_report/analyze/{file}")
        if analyze_service:
            # print(f"{file} succeeded")
            services[svc_timestamp] = analyze_service
    return services