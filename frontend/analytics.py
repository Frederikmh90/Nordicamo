import html
import json
import os


DEFAULT_UMAMI_SCRIPT_URL = "https://cloud.umami.is/script.js"
DEFAULT_UMAMI_WEBSITE_ID = "e19eb77a-55dc-4fc6-8386-296bc2d26420"
DEFAULT_UMAMI_DOMAINS = "nordicamo.org,www.nordicamo.org"


def get_umami_script_url() -> str:
    return os.getenv("UMAMI_SCRIPT_URL", DEFAULT_UMAMI_SCRIPT_URL).strip()


def get_umami_website_id() -> str:
    return os.getenv("UMAMI_WEBSITE_ID", DEFAULT_UMAMI_WEBSITE_ID).strip()


def get_umami_domains() -> str:
    return os.getenv("UMAMI_DOMAINS", DEFAULT_UMAMI_DOMAINS).strip()


def umami_enabled() -> bool:
    return bool(get_umami_script_url() and get_umami_website_id())


def build_umami_script_tag() -> str:
    """
    Return a minimal Umami tracking script tag.
    """
    if not umami_enabled():
        return ""

    src = html.escape(get_umami_script_url(), quote=True)
    website_id = html.escape(get_umami_website_id(), quote=True)
    domains = html.escape(get_umami_domains(), quote=True)
    domain_attr = f' data-domains="{domains}"' if domains else ""

    return (
        f'<script defer src="{src}" data-website-id="{website_id}"{domain_attr}></script>'
    )


def build_umami_bootstrap_html() -> str:
    """
    Return executable HTML that mounts Umami into the top-level document.
    Streamlit markdown can render <script> tags without executing them; this uses
    a tiny JS bootstrap executed inside a component iframe.
    """
    if not umami_enabled():
        return "<div></div>"

    payload = {
        "src": get_umami_script_url(),
        "websiteId": get_umami_website_id(),
        "domains": get_umami_domains(),
        "hostUrl": "https://cloud.umami.is",
    }
    payload_js = json.dumps(payload, ensure_ascii=True)
    return f"""
<div style="display:none"></div>
<script>
(function() {{
  const cfg = {payload_js};
  const targetDoc = (window.parent && window.parent.document) ? window.parent.document : document;
  const existing = targetDoc.querySelector(
    'script[src="' + cfg.src + '"][data-website-id="' + cfg.websiteId + '"]'
  );
  if (existing) return;

  const s = targetDoc.createElement('script');
  s.defer = true;
  s.src = cfg.src;
  s.setAttribute('data-website-id', cfg.websiteId);
  if (cfg.domains) s.setAttribute('data-domains', cfg.domains);
  if (cfg.hostUrl) s.setAttribute('data-host-url', cfg.hostUrl);
  targetDoc.head.appendChild(s);
}})();
</script>
"""
