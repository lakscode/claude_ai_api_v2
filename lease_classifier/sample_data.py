"""
Sample training data for lease clause classification.
"""


def get_sample_data():
    """
    Get sample lease clause data for training and testing.

    Returns:
        Tuple of (texts, labels) lists.
    """
    data = [
        # Rent Payment clauses
        ("The monthly rent shall be $1,500, due on the first day of each month.",
         "rent_payment"),
        ("Tenant agrees to pay rent in the amount of $2,000 per month.",
         "rent_payment"),
        ("Rent payments must be received by the 5th of each month to avoid late fees.",
         "rent_payment"),
        ("The base rent for the premises is $1,800 monthly, payable in advance.",
         "rent_payment"),
        ("Tenant shall pay landlord the sum of $1,200 on the first day of each calendar month.",
         "rent_payment"),
        ("Late payment of rent will incur a fee of 5% of the monthly rent amount.",
         "rent_payment"),
        ("Rent may be paid by check, money order, or electronic transfer.",
         "rent_payment"),
        ("Annual rent increases shall not exceed 3% of the current rent.",
         "rent_payment"),

        # Security Deposit clauses
        ("A security deposit of $3,000 is required prior to move-in.",
         "security_deposit"),
        ("The security deposit shall be returned within 30 days of lease termination.",
         "security_deposit"),
        ("Landlord may deduct from security deposit for unpaid rent or damages beyond normal wear.",
         "security_deposit"),
        ("Tenant shall pay a refundable security deposit equal to one month's rent.",
         "security_deposit"),
        ("The deposit will be held in a separate escrow account as required by law.",
         "security_deposit"),
        ("Security deposit refunds will include an itemized statement of deductions.",
         "security_deposit"),
        ("No interest shall be paid on the security deposit during the lease term.",
         "security_deposit"),
        ("The security deposit cannot be applied as last month's rent without written consent.",
         "security_deposit"),

        # Maintenance clauses
        ("Tenant is responsible for routine maintenance and minor repairs under $100.",
         "maintenance"),
        ("Landlord shall maintain all major systems including HVAC, plumbing, and electrical.",
         "maintenance"),
        ("Tenant must report any maintenance issues within 48 hours of discovery.",
         "maintenance"),
        ("The landlord will provide regular pest control services at no additional cost.",
         "maintenance"),
        ("Tenant agrees to keep the premises in clean and sanitary condition.",
         "maintenance"),
        ("All repairs must be performed by licensed contractors approved by landlord.",
         "maintenance"),
        ("Landlord shall respond to emergency maintenance requests within 24 hours.",
         "maintenance"),
        ("Tenant is responsible for lawn care and snow removal on the premises.",
         "maintenance"),

        # Termination clauses
        ("Either party may terminate this lease with 60 days written notice.",
         "termination"),
        ("Early termination requires payment of two months rent as penalty.",
         "termination"),
        ("This lease shall terminate automatically at the end of the term.",
         "termination"),
        ("Tenant may terminate early due to military deployment with proper documentation.",
         "termination"),
        ("Upon termination, tenant must return all keys and access devices.",
         "termination"),
        ("Lease termination notice must be sent via certified mail.",
         "termination"),
        ("The landlord may terminate the lease for material breach after proper notice.",
         "termination"),
        ("Month-to-month tenancy requires 30 days notice to terminate.",
         "termination"),

        # Utilities clauses
        ("Tenant is responsible for all utilities including gas, electric, and water.",
         "utilities"),
        ("Landlord pays for water and trash removal; tenant pays electric and gas.",
         "utilities"),
        ("All utility accounts must be transferred to tenant's name before move-in.",
         "utilities"),
        ("Internet and cable services are the sole responsibility of the tenant.",
         "utilities"),
        ("Common area utilities are included in the monthly rent.",
         "utilities"),
        ("Tenant shall not exceed normal utility usage for residential purposes.",
         "utilities"),
        ("Utility deposits required by service providers are tenant's responsibility.",
         "utilities"),
        ("Landlord provides heating; tenant is responsible for air conditioning costs.",
         "utilities"),

        # Pet clauses
        ("No pets are allowed on the premises without prior written consent.",
         "pets"),
        ("A non-refundable pet deposit of $500 is required for each approved pet.",
         "pets"),
        ("Dogs over 50 pounds are not permitted in this property.",
         "pets"),
        ("Tenant must provide proof of pet vaccination and liability insurance.",
         "pets"),
        ("Service animals are permitted as required by law without additional deposit.",
         "pets"),
        ("Pet owners are liable for all damages caused by their animals.",
         "pets"),
        ("Maximum of two pets allowed with landlord approval.",
         "pets"),
        ("Exotic animals and dangerous breeds are strictly prohibited.",
         "pets"),

        # Subletting clauses
        ("Tenant may not sublet the premises without prior written consent from landlord.",
         "subletting"),
        ("Any sublease must be approved in writing and does not release tenant from obligations.",
         "subletting"),
        ("Subletting for periods longer than 30 days requires a formal agreement.",
         "subletting"),
        ("Tenant remains fully responsible for subtenant actions and rent payment.",
         "subletting"),
        ("Assignment of this lease requires landlord approval and may incur a transfer fee.",
         "subletting"),
        ("Short-term rentals such as Airbnb are expressly prohibited.",
         "subletting"),
        ("Landlord shall not unreasonably withhold consent to sublease requests.",
         "subletting"),
        ("Subletting is permitted only to immediate family members.",
         "subletting"),

        # Insurance clauses
        ("Tenant must maintain renter's insurance with minimum coverage of $100,000.",
         "insurance"),
        ("Proof of insurance must be provided to landlord before move-in.",
         "insurance"),
        ("Landlord's insurance does not cover tenant's personal property.",
         "insurance"),
        ("Tenant's insurance policy must name landlord as additional insured.",
         "insurance"),
        ("Failure to maintain required insurance is grounds for lease termination.",
         "insurance"),
        ("Tenant is responsible for any insurance deductibles for claims arising from their actions.",
         "insurance"),
        ("Renter's insurance must include liability coverage for guest injuries.",
         "insurance"),
        ("Insurance policies must remain active throughout the entire lease term.",
         "insurance"),

        # Default clauses
        ("Failure to pay rent within 10 days constitutes default under this lease.",
         "default"),
        ("Upon default, landlord may pursue all legal remedies including eviction.",
         "default"),
        ("Tenant shall have 30 days to cure any non-monetary default after written notice.",
         "default"),
        ("Repeated violations of lease terms constitute grounds for immediate termination.",
         "default"),
        ("In case of default, tenant shall be liable for landlord's attorney fees.",
         "default"),
        ("Material breach of any lease provision may result in forfeiture of security deposit.",
         "default"),
        ("Landlord may accelerate all remaining rent due upon tenant default.",
         "default"),
        ("Default includes unauthorized occupants, illegal activities, or nuisance behavior.",
         "default"),

        # Other clauses
        ("This lease shall be governed by the laws of the State of California.",
         "other"),
        ("All notices must be in writing and delivered to the addresses specified herein.",
         "other"),
        ("This agreement constitutes the entire understanding between the parties.",
         "other"),
        ("Modifications to this lease must be in writing and signed by both parties.",
         "other"),
        ("Tenant acknowledges receipt of lead-based paint disclosure.",
         "other"),
        ("The premises shall be used exclusively for residential purposes.",
         "other"),
        ("Landlord reserves the right to enter with 24-hour notice for inspections.",
         "other"),
        ("Smoking is prohibited in all indoor areas of the premises.",
         "other"),
    ]

    texts = [item[0] for item in data]
    labels = [item[1] for item in data]

    return texts, labels


def get_clause_descriptions():
    """
    Get descriptions for each clause type.

    Returns:
        Dictionary mapping clause types to descriptions.
    """
    return {
        'rent_payment': 'Clauses about rent amounts, due dates, payment methods, and late fees',
        'security_deposit': 'Clauses about deposits, refunds, deductions, and escrow requirements',
        'maintenance': 'Clauses about repairs, upkeep, and maintenance responsibilities',
        'termination': 'Clauses about lease ending, notice periods, and early termination',
        'utilities': 'Clauses about utility payments and service responsibilities',
        'pets': 'Clauses about pet policies, deposits, and restrictions',
        'subletting': 'Clauses about sublease rights, assignments, and restrictions',
        'insurance': 'Clauses about renter\'s insurance and liability requirements',
        'default': 'Clauses about breach of lease, remedies, and penalties',
        'other': 'Miscellaneous clauses including governing law and general provisions'
    }
