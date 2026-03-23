import re

with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

campaign_update_code = """
class CampaignUpdate(BaseModel):
    client: Optional[str] = None
    destination: Optional[HttpUrl] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    planned_duration_days: Optional[int] = None
    industry: Optional[str] = None
    industry_sub: Optional[str] = None
    iab_tier1: Optional[str] = None
    campaign_type: Optional[str] = None
    campaign_objective: Optional[str] = None
    budget_tier: Optional[str] = None
    budget_currency: Optional[str] = None
    dooh_format: Optional[str] = None
    creative_type: Optional[str] = None
    product_name: Optional[str] = None
    venue_category: Optional[str] = None
    geo_region: Optional[str] = None
    geo_country: Optional[str] = None
    social_amplification: Optional[bool] = None
    social_platforms: Optional[str] = None
    influencer_support: Optional[bool] = None
    hashtag: Optional[str] = None
    target_scans: Optional[int] = None
    target_unique_visitors: Optional[int] = None
    target_ctr_pct: Optional[float] = None
    target_audience: Optional[str] = None
    campaign_status: Optional[str] = None
    campaign_phase: Optional[str] = None
    tags: Optional[str] = None
    internal_notes: Optional[str] = None
    account_manager: Optional[str] = None

"""

if "class CampaignUpdate(BaseModel):" not in c:
    # Inject it right before 'class DeviceCreate' or right after 'class CampaignCreate'
    # The safest is just to append it at the top level where schemas are defined. Let's find BaseModel
    # We will inject it before 'class ScanCreate'
    c = c.replace('class ScanCreate(', campaign_update_code + 'class ScanCreate(')
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Injected successfully.")
else:
    print("Already exists.")
