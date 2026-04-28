# Research Impact

## Source

This document consolidates the most important product-level conclusions from the research bundles that informed LinkVault:

- self-hosted bookmark manager research
- browser import / API research
- UX / UI / GUI comparison work
- installation / requirements research
- Proxmox / community-scripts operating patterns

The purpose of this file is **not** to copy any single reference tool.
Its purpose is to explain which conclusions actually matter for LinkVault.

---

## Core conclusion

LinkVault should not become:

- a read-later-first product
- a reader app
- an archive-first platform
- a knowledge-base-first tool
- a heavy multi-service stack in the default path

LinkVault should become a **self-hosted bookmark, favorites, link-management, dedup, import/export and sync-capable platform**.

The research consistently points to the same opportunity:

> there is still a gap between  
> **lightweight self-hosting**  
> and  
> **strong bookmark data maintenance**

That gap is where LinkVault fits best.

---

## Product formula

LinkVault should follow this product direction:

```text id="xzi8nv"
linkding-like clarity, speed and URL handling
+ Karakeep-like organization, lists, rules and feature depth
+ Linkwarden-like collections and structured navigation
+ LinkAce-like management maturity and administrative clarity
+ Shiori-/Readeck-like lightweight self-hosting defaults
+ strong first-class duplicate review, merge and cleanup workflows
+ browser-aware import/export and metadata preservation
+ Proxmox / Debian LXC operational reliability
