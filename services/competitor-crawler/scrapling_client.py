"""
Scrapling 抓取包装层
把 Scrapling 的 Response 转换为现有 ProductSnapshot，避免改动 API、调度和存储层。
"""
import hashlib
import os
import re
from typing import Dict, List, Optional, Any
from urllib.parse import parse_qs, urlparse

from loguru import logger

from anti_crawler import AntiCrawlerManager, get_anti_crawler
from storage import Platform, ProductSnapshot


PLATFORM_SELECTORS: Dict[Platform, Dict[str, Any]] = {
    Platform.DOUYIN: {
        "product_id_params": ["product_id", "id"],
        "wait_selector": ".product-info",
        "title": [".product-title", ".goods-title", "h1", "[class*='title']"],
        "price": [".price", ".product-price", ".current-price", "[class*='price']"],
        "original_price": [".original-price", ".line-price", "[class*='original']"],
        "sales": [".sales-count", ".sold-count", "[class*='sales']", "[class*='sold']"],
        "shop": [".shop-name", ".store-name", "[class*='shop']", "[class*='store']"],
        "comments": [
            ".comment-content",
            ".comment-text",
            ".review-content",
            "[class*='comment'] p",
            "[class*='review'] p",
        ],
    },
    Platform.KUAISHOU: {
        "product_id_params": ["goods_id", "id"],
        "wait_selector": ".goods-detail",
        "title": [".goods-title", "h1", "[class*='title']"],
        "price": [".price", ".goods-price", "[class*='price']"],
        "original_price": [".original-price", "[class*='original']"],
        "sales": [".sales-count", ".sold-count", "[class*='sales']", "[class*='sold']"],
        "shop": [".shop-name", ".store-name", "[class*='shop']", "[class*='store']"],
        "comments": [".comment-text", ".review-content", "[class*='comment'] p"],
    },
    Platform.PDD: {
        "product_id_params": ["goods_id", "id"],
        "wait_selector": ".goods-detail-page",
        "title": [".goods-detail-page h1", ".goods-title", "h1", "[class*='title']"],
        "price": [".goods-price", ".price", "[class*='price']"],
        "original_price": [".original-price", "[class*='original']"],
        "sales": [".sold-count", ".sales-count", "[class*='sales']", "[class*='sold']"],
        "shop": [".shop-name", ".store-name", "[class*='shop']", "[class*='store']"],
        "comments": [".comment-text", ".review-content", ".comment-content", "[class*='comment'] p"],
    },
    Platform.XIANYU: {
        "product_id_params": ["id", "item_id"],
        "wait_selector": ".item-detail",
        "title": [".item-title", "h1", "[class*='title']"],
        "price": [".item-price", ".price", "[class*='price']"],
        "original_price": [".original-price", "[class*='original']"],
        "sales": [".sold-count", ".sales-count", "[class*='sales']", "[class*='sold']"],
        "shop": [".seller-name", ".user-name", "[class*='seller']", "[class*='user']"],
        "comments": [".comment-text", ".review-content", "[class*='comment'] p"],
    },
}

PROMOTION_SELECTORS = [
    ".promotion-tag",
    ".coupon-tag",
    ".discount-tag",
    ".activity-tag",
    ".benefit-tag",
    ".label-list span",
    "[class*='promotion']",
    "[class*='coupon']",
    "[class*='discount']",
]

IMAGE_SELECTORS = [
    "img.main-img",
    "img.product-img",
    ".product-image img",
    "img[data-role='product-image']",
    ".swiper-slide img",
    "img[src*='product']",
    "img[src*='goods']",
    "img",
]


def scrapling_enabled() -> bool:
    """是否优先使用 Scrapling。"""
    engine = os.getenv("CRAWLER_ENGINE", "scrapling").strip().lower()
    return engine in {"scrapling", "auto"}


async def crawl_product_with_scrapling(
    platform: Platform,
    url: str,
    anti_crawler: Optional[AntiCrawlerManager] = None,
):
    """使用 Scrapling 爬取单个商品，返回现有 CrawlResult 类型。"""
    from crawler import CrawlResult

    try:
        _ensure_scrapling_fetchers_available()
    except Exception as e:
        return CrawlResult(success=False, error=str(e))

    anti_crawler = anti_crawler or get_anti_crawler()
    request_config = await anti_crawler.prepare_request()
    proxy = request_config.get("proxy")

    try:
        page = await _fetch_page(url, request_config, PLATFORM_SELECTORS[platform].get("wait_selector"))
        page_text = _page_text(page)
        if anti_crawler.detect_captcha(page_text):
            anti_crawler.report_failure(proxy)
            return CrawlResult(success=False, error="Scrapling detected captcha challenge")

        snapshot = _build_snapshot(platform, url, page)
        if not snapshot.title and not snapshot.price:
            anti_crawler.report_failure(proxy)
            return CrawlResult(success=False, error="Scrapling did not extract title or price")

        anti_crawler.report_success(proxy)
        return CrawlResult(success=True, data=snapshot)

    except Exception as e:
        anti_crawler.report_failure(proxy)
        logger.warning(f"Scrapling crawl failed for {platform.value}: {e}")
        return CrawlResult(success=False, error=str(e))


def _ensure_scrapling_fetchers_available() -> None:
    try:
        import scrapling.fetchers  # noqa: F401
    except ModuleNotFoundError as e:
        raise RuntimeError("Scrapling fetchers are not installed") from e


async def _fetch_page(url: str, request_config: Dict[str, Any], wait_selector: Optional[str]):
    fetcher = os.getenv("SCRAPLING_FETCHER", "dynamic").strip().lower()
    timeout_ms = float(os.getenv("SCRAPLING_TIMEOUT_MS", "30000"))
    wait_ms = int(os.getenv("SCRAPLING_WAIT_MS", "1000"))
    headless = os.getenv("SCRAPLING_HEADLESS", "true").strip().lower() not in {"0", "false", "no"}
    proxy = request_config.get("proxy")
    headers = request_config.get("headers") or {}

    if fetcher == "static":
        from scrapling.fetchers import AsyncFetcher

        return await AsyncFetcher.get(
            url,
            timeout=timeout_ms / 1000,
            stealthy_headers=True,
            proxy=proxy,
            headers=headers,
        )

    if fetcher == "stealthy":
        from scrapling.fetchers import StealthyFetcher

        return await StealthyFetcher.async_fetch(
            url,
            headless=headless,
            network_idle=True,
            wait=wait_ms,
            timeout=timeout_ms,
            wait_selector=wait_selector,
            extra_headers=headers,
            proxy=proxy,
            google_search=True,
        )

    dynamic_fetcher = _get_dynamic_fetcher()
    return await dynamic_fetcher.async_fetch(
        url,
        headless=headless,
        network_idle=True,
        wait=wait_ms,
        timeout=timeout_ms,
        wait_selector=wait_selector,
        useragent=request_config.get("user_agent"),
        extra_headers=headers,
        proxy=proxy,
        locale="zh-CN",
        stealth=True,
        google_search=True,
    )


def _get_dynamic_fetcher():
    import scrapling.fetchers as scrapling_fetchers

    dynamic_fetcher = getattr(scrapling_fetchers, "DynamicFetcher", None)
    if dynamic_fetcher is None:
        dynamic_fetcher = getattr(scrapling_fetchers, "PlayWrightFetcher")
    return dynamic_fetcher


def _build_snapshot(platform: Platform, url: str, page) -> ProductSnapshot:
    selectors = PLATFORM_SELECTORS[platform]

    title = _first_text(page, selectors["title"]) or ""
    price_text = _first_text(page, selectors["price"]) or "0"
    price = _extract_price(price_text) or 0.0

    original_price_text = _first_text(page, selectors["original_price"])
    original_price = _extract_price(original_price_text) if original_price_text else None

    image_url = _first_attr(page, IMAGE_SELECTORS, "src")
    image_hash = hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:16] if image_url else ""

    promotion_tags = _all_text(page, PROMOTION_SELECTORS, limit=20)
    comment_keywords = _all_text(page, selectors["comments"], limit=10, min_len=5)

    sales_text = _first_text(page, selectors["sales"])
    shop_name = _first_text(page, selectors["shop"])

    return ProductSnapshot(
        platform=platform,
        product_id=_extract_product_id(url, selectors["product_id_params"]),
        url=url,
        title=title.strip(),
        price=price,
        original_price=original_price,
        main_image_hash=image_hash,
        promotion_tags=promotion_tags,
        comment_keywords=comment_keywords,
        sales_count=_extract_sales_count(sales_text),
        shop_name=shop_name.strip() if shop_name else None,
        raw_data={
            "url": url,
            "engine": "scrapling",
            "fetcher": os.getenv("SCRAPLING_FETCHER", "dynamic"),
            "status": getattr(page, "status", None),
            "image_url": image_url,
        },
    )


def _first_text(page, selectors: List[str]) -> Optional[str]:
    for selector in selectors:
        text = _joined_text(page, selector)
        if text:
            return text
    return None


def _all_text(page, selectors: List[str], limit: int, min_len: int = 1) -> List[str]:
    values: List[str] = []
    seen = set()

    for selector in selectors:
        for value in _selector_texts(page, f"{selector}::text"):
            cleaned = value.strip()
            if len(cleaned) < min_len or cleaned in seen:
                continue
            values.append(cleaned)
            seen.add(cleaned)
            if len(values) >= limit:
                return values

        for value in _selector_texts(page, f"{selector} *::text"):
            cleaned = value.strip()
            if len(cleaned) < min_len or cleaned in seen:
                continue
            values.append(cleaned)
            seen.add(cleaned)
            if len(values) >= limit:
                return values

    return values


def _joined_text(page, selector: str) -> Optional[str]:
    values = _selector_texts(page, f"{selector}::text")
    if not values:
        values = _selector_texts(page, f"{selector} *::text")

    text = " ".join(value.strip() for value in values if value and value.strip())
    return text or None


def _selector_texts(page, query: str) -> List[str]:
    try:
        return page.css(query).getall()
    except Exception:
        return []


def _first_attr(page, selectors: List[str], attr: str) -> Optional[str]:
    for selector in selectors:
        try:
            value = page.css(f"{selector}::attr({attr})").get()
            if value:
                return value.strip()
        except Exception:
            continue
    return None


def _page_text(page) -> str:
    return " ".join(_selector_texts(page, "body::text") + _selector_texts(page, "body *::text"))


def _extract_product_id(url: str, query_params: List[str]) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    for param in query_params:
        if param in params and params[param]:
            return params[param][0]
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:16]


def _extract_price(text: Optional[str]) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"[¥￥]\s*(\d+\.?\d*)",
        r"(\d+\.?\d*)\s*元",
        r"价格[：:]\s*(\d+\.?\d*)",
        r"(\d+\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.replace(",", ""))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def _extract_sales_count(text: Optional[str]) -> Optional[int]:
    if not text:
        return None

    text = text.replace(",", "")
    match = re.search(r"(\d+\.?\d*)\s*万", text)
    if match:
        return int(float(match.group(1)) * 10000)

    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))

    return None
