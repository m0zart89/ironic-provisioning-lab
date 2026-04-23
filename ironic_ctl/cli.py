#!/usr/bin/env python3
"""
ironic-ctl — CLI for bare-metal node lifecycle management via OpenStack Ironic.

Usage:
  ironic-ctl list [--state <state>]
  ironic-ctl inspect <node-id>
  ironic-ctl provision <node-id> --image <url> --checksum <sha256>
  ironic-ctl clean <node-id>
  ironic-ctl power <node-id> <on|off|reboot>
  ironic-ctl show <node-id>
"""
import argparse
import json
import sys
from ironic_ctl.client import IronicClient


CLEAN_STEPS = [
    {"interface": "deploy", "step": "erase_devices_metadata", "priority": 10},
    {"interface": "deploy", "step": "erase_devices", "priority": 20},
]


def cmd_list(client: IronicClient, args):
    nodes = client.list_nodes(provision_state=args.state)
    fmt = "{:<38} {:<16} {:<16} {}"
    print(fmt.format("UUID", "PROVISION STATE", "POWER STATE", "NAME"))
    print("-" * 90)
    for n in nodes:
        print(fmt.format(
            n["uuid"],
            n.get("provision_state", "—"),
            n.get("power_state", "—"),
            n.get("name", ""),
        ))


def cmd_show(client: IronicClient, args):
    node = client.get_node(args.node_id)
    print(json.dumps(node, indent=2, default=str))


def cmd_inspect(client: IronicClient, args):
    print(f"Starting inspection for {args.node_id}...")
    client.set_provision_state(args.node_id, "inspect")
    print("Inspection triggered — node will move to 'inspecting', then 'manageable'")


def cmd_provision(client: IronicClient, args):
    print(f"Setting deploy image for {args.node_id}...")
    client.update_node(args.node_id, [
        {"op": "add", "path": "/instance_info/image_url", "value": args.image},
        {"op": "add", "path": "/instance_info/image_checksum", "value": args.checksum},
        {"op": "add", "path": "/instance_info/image_disk_format", "value": "raw"},
    ])
    client.set_provision_state(args.node_id, "active")
    print("Provisioning started — node will move through 'deploying' to 'active'")


def cmd_clean(client: IronicClient, args):
    print(f"Cleaning {args.node_id} (erase metadata + full disk wipe)...")
    client.set_provision_state(args.node_id, "clean", clean_steps=CLEAN_STEPS)
    print("Clean started — node will return to 'available' when done")


def cmd_power(client: IronicClient, args):
    target_map = {"on": "power on", "off": "power off", "reboot": "rebooting"}
    target = target_map.get(args.action)
    if not target:
        print(f"Unknown power action: {args.action}", file=sys.stderr)
        sys.exit(1)
    client.set_power_state(args.node_id, target)
    print(f"Power state change to '{target}' requested for {args.node_id}")


def main():
    parser = argparse.ArgumentParser(description="Ironic bare-metal lifecycle CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List nodes")
    p_list.add_argument("--state", help="Filter by provision state")

    p_show = sub.add_parser("show", help="Show node details")
    p_show.add_argument("node_id")

    p_inspect = sub.add_parser("inspect", help="Trigger hardware inspection")
    p_inspect.add_argument("node_id")

    p_prov = sub.add_parser("provision", help="Deploy OS image to node")
    p_prov.add_argument("node_id")
    p_prov.add_argument("--image", required=True, help="HTTP URL to raw disk image")
    p_prov.add_argument("--checksum", required=True, help="SHA256 checksum of image")

    p_clean = sub.add_parser("clean", help="Wipe node and return to available")
    p_clean.add_argument("node_id")

    p_power = sub.add_parser("power", help="Control node power state")
    p_power.add_argument("node_id")
    p_power.add_argument("action", choices=["on", "off", "reboot"])

    args = parser.parse_args()
    client = IronicClient()

    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "inspect": cmd_inspect,
        "provision": cmd_provision,
        "clean": cmd_clean,
        "power": cmd_power,
    }
    dispatch[args.command](client, args)


if __name__ == "__main__":
    main()
