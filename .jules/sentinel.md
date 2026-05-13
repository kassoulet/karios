## 2026-05-13 - XSS in HTML Report Generation
**Vulnerability:** Cross-Site Scripting (XSS) in generated HTML reports.
**Learning:** User-controlled strings from image metadata (filenames) and runtime configuration (title prefixes, DEM descriptions) were directly injected into HTML templates without sanitization. In geospatial tools, filenames and metadata are often derived from external sources and can be manipulated to include malicious payloads.
**Prevention:** Always use `html.escape()` when injecting dynamic strings into HTML templates, especially when not using a template engine with auto-escaping (like Jinja2).
