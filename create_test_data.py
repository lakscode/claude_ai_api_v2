"""
Create sample test_data folder with Excel files containing text and label columns.
Labels use IDs that map to data_mapping.json.
"""

import pandas as pd
from pathlib import Path

# Create test_data folder
test_data_dir = Path(__file__).parent / "test_data"
test_data_dir.mkdir(exist_ok=True)

# Sample data with clause IDs from data_mapping.json
# Format: (text, label_id)
sample_data = [
    # Rent (63f37d2c0d2f74adc82f4101)
    ("The monthly rent shall be $1,500, due on the first day of each month.", "63f37d2c0d2f74adc82f4101"),
    ("Tenant agrees to pay rent in the amount of $2,000 per month.", "63f37d2c0d2f74adc82f4101"),
    ("Rent payments must be received by the 5th of each month.", "63f37d2c0d2f74adc82f4101"),
    ("The base rent for the premises is $1,800 monthly, payable in advance.", "63f37d2c0d2f74adc82f4101"),
    ("All rental payments shall be made to the landlord at the address specified.", "63f37d2c0d2f74adc82f4101"),

    # Security Deposit (63f37d2c0d2f74adc82f4104)
    ("A security deposit of $3,000 is required prior to move-in.", "63f37d2c0d2f74adc82f4104"),
    ("The security deposit shall be returned within 30 days of lease termination.", "63f37d2c0d2f74adc82f4104"),
    ("Landlord may deduct from security deposit for unpaid rent or damages.", "63f37d2c0d2f74adc82f4104"),
    ("Tenant shall pay a refundable security deposit equal to one month's rent.", "63f37d2c0d2f74adc82f4104"),
    ("The deposit will be held in a separate escrow account as required by law.", "63f37d2c0d2f74adc82f4104"),

    # Termination (5d51128d18b40d3e38ed4359)
    ("Either party may terminate this lease with 60 days written notice.", "5d51128d18b40d3e38ed4359"),
    ("Early termination requires payment of two months rent as penalty.", "5d51128d18b40d3e38ed4359"),
    ("This lease shall terminate automatically at the end of the term.", "5d51128d18b40d3e38ed4359"),
    ("Upon termination, tenant must return all keys and access devices.", "5d51128d18b40d3e38ed4359"),
    ("Month-to-month tenancy requires 30 days notice to terminate.", "5d51128d18b40d3e38ed4359"),

    # Insurance (5d51128d18b40d3e38ed4369)
    ("Tenant must maintain renter's insurance with minimum coverage of $100,000.", "5d51128d18b40d3e38ed4369"),
    ("Proof of insurance must be provided to landlord before move-in.", "5d51128d18b40d3e38ed4369"),
    ("Landlord's insurance does not cover tenant's personal property.", "5d51128d18b40d3e38ed4369"),
    ("Tenant's insurance policy must name landlord as additional insured.", "5d51128d18b40d3e38ed4369"),
    ("Insurance policies must remain active throughout the entire lease term.", "5d51128d18b40d3e38ed4369"),

    # Assignment and Subleasing (63f37d2c0d2f74adc82f4103)
    ("Tenant may not sublet the premises without prior written consent.", "63f37d2c0d2f74adc82f4103"),
    ("Any sublease must be approved in writing by the landlord.", "63f37d2c0d2f74adc82f4103"),
    ("Short-term rentals such as Airbnb are expressly prohibited.", "63f37d2c0d2f74adc82f4103"),
    ("Assignment of this lease requires landlord approval.", "63f37d2c0d2f74adc82f4103"),
    ("Tenant remains fully responsible for subtenant actions.", "63f37d2c0d2f74adc82f4103"),

    # Repairs (64217b1a275caef553ece40b)
    ("Tenant is responsible for routine maintenance and minor repairs under $100.", "64217b1a275caef553ece40b"),
    ("Landlord shall maintain all major systems including HVAC and plumbing.", "64217b1a275caef553ece40b"),
    ("Tenant must report any maintenance issues within 48 hours.", "64217b1a275caef553ece40b"),
    ("All repairs must be performed by licensed contractors approved by landlord.", "64217b1a275caef553ece40b"),
    ("Landlord shall respond to emergency maintenance requests within 24 hours.", "64217b1a275caef553ece40b"),

    # Utilities (66fa76dc6bf9d16cddb69e49)
    ("Tenant is responsible for all utilities including gas, electric, and water.", "66fa76dc6bf9d16cddb69e49"),
    ("All utility accounts must be transferred to tenant's name before move-in.", "66fa76dc6bf9d16cddb69e49"),
    ("Landlord pays for water and trash removal; tenant pays electric and gas.", "66fa76dc6bf9d16cddb69e49"),
    ("Internet and cable services are the sole responsibility of the tenant.", "66fa76dc6bf9d16cddb69e49"),
    ("Common area utilities are included in the monthly rent.", "66fa76dc6bf9d16cddb69e49"),

    # Late Charge (63f37d2c0d2f74adc82f4102)
    ("Late payment of rent will incur a fee of 5% of the monthly rent amount.", "63f37d2c0d2f74adc82f4102"),
    ("A late charge of $50 will be applied for payments received after the 5th.", "63f37d2c0d2f74adc82f4102"),
    ("Failure to pay rent by the due date will result in late fees.", "63f37d2c0d2f74adc82f4102"),
    ("Late fees are cumulative and will be added to the next month's rent.", "63f37d2c0d2f74adc82f4102"),
    ("Tenant agrees to pay a late charge for any rent not paid within 5 days.", "63f37d2c0d2f74adc82f4102"),

    # Term (5d51128d18b40d3e38ed4358)
    ("The lease term shall be for a period of twelve months.", "5d51128d18b40d3e38ed4358"),
    ("This agreement commences on January 1, 2024 and ends on December 31, 2024.", "5d51128d18b40d3e38ed4358"),
    ("The initial lease term is 24 months from the date of execution.", "5d51128d18b40d3e38ed4358"),
    ("Lease term begins on the first day of the month following signing.", "5d51128d18b40d3e38ed4358"),
    ("The duration of this lease shall be three years.", "5d51128d18b40d3e38ed4358"),

    # Indemnification (5d51128d18b40d3e38ed435f)
    ("Tenant shall indemnify and hold landlord harmless from all claims.", "5d51128d18b40d3e38ed435f"),
    ("Landlord is not liable for any injury or damage on the premises.", "5d51128d18b40d3e38ed435f"),
    ("Tenant agrees to indemnify landlord against all losses and liabilities.", "5d51128d18b40d3e38ed435f"),
    ("The tenant shall defend landlord from any claims arising from tenant's use.", "5d51128d18b40d3e38ed435f"),
    ("Indemnification obligations survive termination of this lease.", "5d51128d18b40d3e38ed435f"),

    # Confidential Information (5d51128d18b40d3e38ed435c)
    ("All terms of this lease shall be kept confidential by both parties.", "5d51128d18b40d3e38ed435c"),
    ("Neither party shall disclose lease terms to third parties.", "5d51128d18b40d3e38ed435c"),
    ("Confidential information includes rent amounts and lease conditions.", "5d51128d18b40d3e38ed435c"),
    ("Breach of confidentiality constitutes a material breach of this lease.", "5d51128d18b40d3e38ed435c"),
    ("Confidentiality obligations survive termination of this agreement.", "5d51128d18b40d3e38ed435c"),

    # Governing Law (5d51128d18b40d3e38ed4366)
    ("This lease shall be governed by the laws of the State of California.", "5d51128d18b40d3e38ed4366"),
    ("Any disputes shall be resolved in the courts of New York.", "5d51128d18b40d3e38ed4366"),
    ("The parties agree that Texas law shall govern this agreement.", "5d51128d18b40d3e38ed4366"),
    ("This lease is subject to the laws of the jurisdiction where property is located.", "5d51128d18b40d3e38ed4366"),
    ("All legal proceedings shall be conducted in accordance with state law.", "5d51128d18b40d3e38ed4366"),

    # Force Majeure (5d51128d18b40d3e38ed4364)
    ("Neither party shall be liable for delays due to acts of God or natural disasters.", "5d51128d18b40d3e38ed4364"),
    ("Force majeure events include war, terrorism, and government actions.", "5d51128d18b40d3e38ed4364"),
    ("Obligations are suspended during force majeure events.", "5d51128d18b40d3e38ed4364"),
    ("Party affected by force majeure must notify the other party promptly.", "5d51128d18b40d3e38ed4364"),
    ("If force majeure continues for 90 days, either party may terminate.", "5d51128d18b40d3e38ed4364"),

    # Notices (5d51128d18b40d3e38ed4361)
    ("All notices must be in writing and delivered to the addresses specified.", "5d51128d18b40d3e38ed4361"),
    ("Notice is effective upon receipt or 3 days after mailing.", "5d51128d18b40d3e38ed4361"),
    ("Notices may be sent by certified mail, courier, or hand delivery.", "5d51128d18b40d3e38ed4361"),
    ("Either party may change notice address with 10 days written notice.", "5d51128d18b40d3e38ed4361"),
    ("Email notices are acceptable if receipt is confirmed.", "5d51128d18b40d3e38ed4361"),

    # Renewal (63f37d2c0d2f74adc82f4107)
    ("Tenant may renew this lease for an additional term with 90 days notice.", "63f37d2c0d2f74adc82f4107"),
    ("Renewal rent shall be at market rate determined by landlord.", "63f37d2c0d2f74adc82f4107"),
    ("Lease automatically renews on a month-to-month basis unless terminated.", "63f37d2c0d2f74adc82f4107"),
    ("Option to renew must be exercised in writing before expiration.", "63f37d2c0d2f74adc82f4107"),
    ("Renewal terms shall be the same except for rent adjustments.", "63f37d2c0d2f74adc82f4107"),
]

# Create single Excel file with all data
df = pd.DataFrame(sample_data, columns=['text', 'label'])
filepath = test_data_dir / "training_data.xlsx"
df.to_excel(filepath, index=False, engine='openpyxl')
print(f"Created: {filepath} ({len(df)} samples)")

# Also create separate files per category for organization
from collections import defaultdict
grouped = defaultdict(list)
for text, label in sample_data:
    grouped[label].append(text)

print(f"\nLabel distribution:")
for label_id, texts in sorted(grouped.items()):
    print(f"  {label_id}: {len(texts)} samples")

print(f"\nTotal: {len(sample_data)} samples in test_data folder")
print("\nTo add more training data:")
print("1. Open test_data/training_data.xlsx")
print("2. Add rows with 'text' (clause text) and 'label' (ID from data_mapping.json)")
