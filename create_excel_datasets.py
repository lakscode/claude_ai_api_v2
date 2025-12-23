"""
Script to create Excel dataset files for each clause type.
Run this once to generate the Excel files in the dataset folder.
"""

import pandas as pd
from pathlib import Path

# Create dataset folder
dataset_dir = Path(__file__).parent / "dataset"
dataset_dir.mkdir(exist_ok=True)

# Dataset for each clause type
datasets = {
    "rent_payment": [
        "The monthly rent shall be $1,500, due on the first day of each month.",
        "Tenant agrees to pay rent in the amount of $2,000 per month.",
        "Rent payments must be received by the 5th of each month to avoid late fees.",
        "The base rent for the premises is $1,800 monthly, payable in advance.",
        "Tenant shall pay landlord the sum of $1,200 on the first day of each calendar month.",
        "Late payment of rent will incur a fee of 5% of the monthly rent amount.",
        "Rent may be paid by check, money order, or electronic transfer.",
        "Annual rent increases shall not exceed 3% of the current rent.",
        "All rental payments shall be made to the landlord at the address specified.",
        "Failure to pay rent by the due date will result in a late charge of $50.",
        "The first month's rent is due upon signing of this lease agreement.",
        "Rent shall be prorated for any partial month of occupancy.",
        "Landlord reserves the right to increase rent with 60 days written notice.",
        "Payment of rent by personal check is subject to a 10-day clearance period.",
        "Tenant agrees that rent is payable without demand or notice.",
    ],

    "security_deposit": [
        "A security deposit of $3,000 is required prior to move-in.",
        "The security deposit shall be returned within 30 days of lease termination.",
        "Landlord may deduct from security deposit for unpaid rent or damages beyond normal wear.",
        "Tenant shall pay a refundable security deposit equal to one month's rent.",
        "The deposit will be held in a separate escrow account as required by law.",
        "Security deposit refunds will include an itemized statement of deductions.",
        "No interest shall be paid on the security deposit during the lease term.",
        "The security deposit cannot be applied as last month's rent without written consent.",
        "Upon move-out, tenant must provide forwarding address for deposit refund.",
        "Deductions from deposit may include cleaning, repairs, and unpaid utilities.",
        "The maximum security deposit allowed by law is two months rent.",
        "Tenant will receive deposit refund within 21 days after returning keys.",
        "Security deposit will be forfeited if tenant abandons the property.",
        "Landlord must provide written notice of any deposit deductions.",
        "The security deposit secures faithful performance of all lease terms.",
    ],

    "maintenance": [
        "Tenant is responsible for routine maintenance and minor repairs under $100.",
        "Landlord shall maintain all major systems including HVAC, plumbing, and electrical.",
        "Tenant must report any maintenance issues within 48 hours of discovery.",
        "The landlord will provide regular pest control services at no additional cost.",
        "Tenant agrees to keep the premises in clean and sanitary condition.",
        "All repairs must be performed by licensed contractors approved by landlord.",
        "Landlord shall respond to emergency maintenance requests within 24 hours.",
        "Tenant is responsible for lawn care and snow removal on the premises.",
        "Tenant shall not make alterations without prior written consent from landlord.",
        "Landlord will maintain common areas in good condition.",
        "Tenant must replace air filters monthly at their own expense.",
        "Any damage caused by tenant negligence will be repaired at tenant's cost.",
        "Landlord shall ensure all appliances are in working order at move-in.",
        "Tenant agrees to promptly unclog drains and maintain plumbing fixtures.",
        "Regular maintenance inspections will be conducted with proper notice.",
    ],

    "termination": [
        "Either party may terminate this lease with 60 days written notice.",
        "Early termination requires payment of two months rent as penalty.",
        "This lease shall terminate automatically at the end of the term.",
        "Tenant may terminate early due to military deployment with proper documentation.",
        "Upon termination, tenant must return all keys and access devices.",
        "Lease termination notice must be sent via certified mail.",
        "The landlord may terminate the lease for material breach after proper notice.",
        "Month-to-month tenancy requires 30 days notice to terminate.",
        "Tenant must vacate the premises by noon on the termination date.",
        "Failure to provide proper notice will result in automatic lease renewal.",
        "Early termination fee is waived for victims of domestic violence.",
        "Landlord may terminate immediately for illegal activity on premises.",
        "Notice of non-renewal must be given at least 90 days before expiration.",
        "Tenant may terminate with 14 days notice if unit becomes uninhabitable.",
        "Upon termination, tenant must leave premises in broom-clean condition.",
    ],

    "utilities": [
        "Tenant is responsible for all utilities including gas, electric, and water.",
        "Landlord pays for water and trash removal; tenant pays electric and gas.",
        "All utility accounts must be transferred to tenant's name before move-in.",
        "Internet and cable services are the sole responsibility of the tenant.",
        "Common area utilities are included in the monthly rent.",
        "Tenant shall not exceed normal utility usage for residential purposes.",
        "Utility deposits required by service providers are tenant's responsibility.",
        "Landlord provides heating; tenant is responsible for air conditioning costs.",
        "Tenant must maintain utility services throughout the lease term.",
        "Failure to pay utilities may result in service disconnection.",
        "Landlord is not liable for utility service interruptions.",
        "Tenant agrees to use energy-efficient practices to conserve utilities.",
        "Hot water is provided by landlord and included in rent.",
        "Tenant shall pay for any utility usage during the lease term.",
        "Sewer and garbage collection fees are included in monthly rent.",
    ],

    "pets": [
        "No pets are allowed on the premises without prior written consent.",
        "A non-refundable pet deposit of $500 is required for each approved pet.",
        "Dogs over 50 pounds are not permitted in this property.",
        "Tenant must provide proof of pet vaccination and liability insurance.",
        "Service animals are permitted as required by law without additional deposit.",
        "Pet owners are liable for all damages caused by their animals.",
        "Maximum of two pets allowed with landlord approval.",
        "Exotic animals and dangerous breeds are strictly prohibited.",
        "Monthly pet rent of $25 per pet will be added to base rent.",
        "Pets must be kept on leash in all common areas.",
        "Tenant must clean up after pets immediately on the property.",
        "Fish tanks under 20 gallons are permitted without approval.",
        "Barking or aggressive pets may result in lease termination.",
        "Pet approval may be revoked for repeated violations of pet policy.",
        "Tenant must notify landlord of any new pets within 7 days.",
    ],

    "subletting": [
        "Tenant may not sublet the premises without prior written consent from landlord.",
        "Any sublease must be approved in writing and does not release tenant from obligations.",
        "Subletting for periods longer than 30 days requires a formal agreement.",
        "Tenant remains fully responsible for subtenant actions and rent payment.",
        "Assignment of this lease requires landlord approval and may incur a transfer fee.",
        "Short-term rentals such as Airbnb are expressly prohibited.",
        "Landlord shall not unreasonably withhold consent to sublease requests.",
        "Subletting is permitted only to immediate family members.",
        "Sublease rent may not exceed the rent charged to the primary tenant.",
        "Tenant must provide subtenant information to landlord before subletting.",
        "Unauthorized subletting is grounds for immediate lease termination.",
        "A subletting fee of $200 will be charged for processing approved subleases.",
        "Sublease term cannot extend beyond the original lease expiration.",
        "Landlord may interview and approve any proposed subtenant.",
        "Tenant must provide 30 days notice of intent to sublet.",
    ],

    "insurance": [
        "Tenant must maintain renter's insurance with minimum coverage of $100,000.",
        "Proof of insurance must be provided to landlord before move-in.",
        "Landlord's insurance does not cover tenant's personal property.",
        "Tenant's insurance policy must name landlord as additional insured.",
        "Failure to maintain required insurance is grounds for lease termination.",
        "Tenant is responsible for any insurance deductibles for claims arising from their actions.",
        "Renter's insurance must include liability coverage for guest injuries.",
        "Insurance policies must remain active throughout the entire lease term.",
        "Tenant must notify landlord of any insurance claims filed.",
        "Minimum liability coverage required is $300,000 per occurrence.",
        "Tenant waives all claims against landlord covered by tenant's insurance.",
        "Insurance policy must cover fire, theft, and water damage.",
        "Tenant must provide updated proof of insurance upon policy renewal.",
        "Landlord recommends coverage for personal belongings of at least $30,000.",
        "Loss of use coverage is recommended in case of temporary displacement.",
    ],

    "default": [
        "Failure to pay rent within 10 days constitutes default under this lease.",
        "Upon default, landlord may pursue all legal remedies including eviction.",
        "Tenant shall have 30 days to cure any non-monetary default after written notice.",
        "Repeated violations of lease terms constitute grounds for immediate termination.",
        "In case of default, tenant shall be liable for landlord's attorney fees.",
        "Material breach of any lease provision may result in forfeiture of security deposit.",
        "Landlord may accelerate all remaining rent due upon tenant default.",
        "Default includes unauthorized occupants, illegal activities, or nuisance behavior.",
        "Three or more late payments in a year constitute chronic default.",
        "Landlord may pursue collection of unpaid rent after tenant vacates.",
        "Default notice will be sent by certified mail to tenant's address.",
        "Tenant in default waives right to any grace periods for future violations.",
        "Landlord may terminate utilities upon tenant default where permitted by law.",
        "Cure period does not apply to defaults involving health or safety violations.",
        "Tenant agrees to pay all costs associated with enforcing this lease.",
    ],

    "other": [
        "This lease shall be governed by the laws of the State of California.",
        "All notices must be in writing and delivered to the addresses specified herein.",
        "This agreement constitutes the entire understanding between the parties.",
        "Modifications to this lease must be in writing and signed by both parties.",
        "Tenant acknowledges receipt of lead-based paint disclosure.",
        "The premises shall be used exclusively for residential purposes.",
        "Landlord reserves the right to enter with 24-hour notice for inspections.",
        "Smoking is prohibited in all indoor areas of the premises.",
        "Tenant shall comply with all applicable laws and HOA regulations.",
        "Quiet hours are observed between 10 PM and 8 AM.",
        "Tenant may not operate a business from the residential premises.",
        "All disputes shall be resolved through binding arbitration.",
        "Landlord is not liable for personal injury except due to negligence.",
        "Tenant has inspected premises and accepts them in current condition.",
        "This lease is binding upon heirs, successors, and assigns of both parties.",
    ],
}

# Create Excel file for each clause type
for clause_type, texts in datasets.items():
    df = pd.DataFrame({"text": texts})
    filepath = dataset_dir / f"{clause_type}.xlsx"
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"Created: {filepath} ({len(texts)} samples)")

print(f"\nTotal: {len(datasets)} Excel files created in 'dataset' folder")
print("\nTo add more training data, open each Excel file and add rows to the 'text' column.")
