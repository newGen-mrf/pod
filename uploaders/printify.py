"""
POD Automation Pipeline — Printify API Uploader
Full integration: upload design → create products → publish.
Uses Printify REST API v1 (official, documented, safe).
"""

import base64
import json
import logging
import os
import time

import requests

import config

logger = logging.getLogger("pod.printify")

HEADERS = {}


def _get_headers() -> dict:
    """Build authorization headers."""
    return {
        "Authorization": f"Bearer {config.PRINTIFY_API_TOKEN}",
        "Content-Type": "application/json",
    }


def upload_to_printify(design_path: str, seo: dict) -> dict:
    """
    Full Printify upload pipeline:
    1. Upload design image to Printify file library
    2. Create products (T-shirt, Hoodie, Mug)
    3. Publish products

    Returns dict with product IDs and URLs, or error info.
    """
    if not config.ENABLE_PRINTIFY:
        logger.info("Printify disabled (no credentials) — skipping")
        return {"status": "skipped", "reason": "no credentials"}

    headers = _get_headers()
    result = {"status": "success", "products": []}

    try:
        # Step 1: Upload image
        logger.info("Uploading design to Printify file library...")
        image_id = _upload_image(design_path, headers)
        logger.info(f"Image uploaded — ID: {image_id}")

        # Step 2: Get available blueprints and variants
        # Step 3: Create products for each configured type
        for product_config in config.PRINTIFY_PRODUCTS:
            try:
                product_result = _create_product(
                    image_id=image_id,
                    blueprint_id=product_config["blueprint_id"],
                    print_provider_id=product_config["print_provider_id"],
                    product_name=product_config["name"],
                    seo=seo,
                    headers=headers,
                )
                result["products"].append(product_result)
                logger.info(
                    f"Product created: {product_config['name']} — ID: {product_result.get('id', 'unknown')}"
                )

                # Small delay between product creations
                time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to create {product_config['name']}: {e}")
                result["products"].append(
                    {
                        "name": product_config["name"],
                        "status": "failed",
                        "error": str(e),
                    }
                )

        # Step 4: Publish all successful products
        for product in result["products"]:
            if product.get("status") != "failed" and product.get("id"):
                try:
                    _publish_product(product["id"], seo, headers)
                    product["published"] = True
                    logger.info(f"Published: {product['name']}")
                except Exception as e:
                    product["published"] = False
                    logger.error(f"Failed to publish {product['name']}: {e}")

                time.sleep(1)

    except Exception as e:
        logger.error(f"Printify upload pipeline failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result


def _upload_image(design_path: str, headers: dict) -> str:
    """Upload image to Printify file library. Returns the image ID."""
    # Read the image file and encode as base64
    with open(design_path, "rb") as f:
        image_data = f.read()

    filename = os.path.basename(design_path)
    base64_image = base64.b64encode(image_data).decode("utf-8")

    payload = {
        "file_name": filename,
        "contents": base64_image,
    }

    response = requests.post(
        f"{config.PRINTIFY_BASE_URL}/uploads/images.json",
        headers=headers,
        json=payload,
        timeout=120,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Image upload failed ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    return data["id"]


def _get_variants(blueprint_id: int, print_provider_id: int, headers: dict) -> list:
    """Get available variants for a blueprint + print provider."""
    response = requests.get(
        f"{config.PRINTIFY_BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to get variants ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    return data.get("variants", data) if isinstance(data, dict) else data


def _create_product(
    image_id: str,
    blueprint_id: int,
    print_provider_id: int,
    product_name: str,
    seo: dict,
    headers: dict,
) -> dict:
    """Create a single product on Printify."""
    # Get available variants
    variants_data = _get_variants(blueprint_id, print_provider_id, headers)

    # Enable a reasonable subset of variants (sizes/colors)
    # Take up to 20 variants to keep it manageable
    enabled_variants = []
    for v in variants_data[:20]:
        variant_id = v.get("id") if isinstance(v, dict) else v
        enabled_variants.append(
            {
                "id": variant_id,
                "price": _calculate_price(blueprint_id),
                "is_enabled": True,
            }
        )

    if not enabled_variants:
        raise RuntimeError(f"No variants found for blueprint {blueprint_id}")

    # Build the product payload
    title = f"{seo['title']} | {product_name}"
    if len(title) > 200:
        title = title[:197] + "..."

    payload = {
        "title": title,
        "description": seo["description"],
        "blueprint_id": blueprint_id,
        "print_provider_id": print_provider_id,
        "variants": enabled_variants,
        "print_areas": [
            {
                "variant_ids": [v["id"] for v in enabled_variants],
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {
                                "id": image_id,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1,
                                "angle": 0,
                            }
                        ],
                    }
                ],
            }
        ],
        "tags": seo.get("tags", [])[:13],
    }

    response = requests.post(
        f"{config.PRINTIFY_BASE_URL}/shops/{config.PRINTIFY_SHOP_ID}/products.json",
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Product creation failed ({response.status_code}): {response.text[:500]}"
        )

    data = response.json()
    return {
        "id": data.get("id"),
        "name": product_name,
        "title": title,
        "status": "created",
    }


def _publish_product(product_id: str, seo: dict, headers: dict) -> None:
    """Publish a product to the connected store."""
    payload = {
        "title": True,
        "description": True,
        "images": True,
        "variants": True,
        "tags": True,
    }

    response = requests.post(
        f"{config.PRINTIFY_BASE_URL}/shops/{config.PRINTIFY_SHOP_ID}/products/{product_id}/publish.json",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Publish failed ({response.status_code}): {response.text[:500]}"
        )


def _calculate_price(blueprint_id: int) -> int:
    """
    Calculate retail price in cents.
    Returns base cost + markup.
    """
    # Approximate base costs (cents) by product type
    base_costs = {
        6: 1300,    # T-shirt base ~$13
        77: 2500,   # Hoodie base ~$25
        638: 800,   # Mug base ~$8
    }
    base = base_costs.get(blueprint_id, 1500)
    return base + config.PRINTIFY_PRICE_MARKUP


def get_shop_info() -> dict:
    """Get information about the connected Printify shop."""
    if not config.PRINTIFY_API_TOKEN:
        return {"error": "No API token configured"}

    headers = _get_headers()
    response = requests.get(
        f"{config.PRINTIFY_BASE_URL}/shops.json",
        headers=headers,
        timeout=15,
    )

    if response.status_code == 200:
        return response.json()
    return {"error": f"API call failed: {response.status_code}"}
