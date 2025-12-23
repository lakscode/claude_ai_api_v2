"""
Create a sample lease agreement PDF for testing the classifier.
"""

import fitz  # PyMuPDF


def create_sample_lease_pdf(output_path="sample_lease.pdf"):
    """Create a sample lease agreement PDF with various clause types."""

    # Create a new PDF document
    doc = fitz.open()

    # Page 1 - Title and Rent/Deposit clauses
    page1 = doc.new_page()
    text1 = """
RESIDENTIAL LEASE AGREEMENT

This Lease Agreement is entered into between the Landlord and Tenant.

1. RENT PAYMENT

The monthly rent for the premises shall be One Thousand Five Hundred Dollars ($1,500.00),
due and payable on the first day of each calendar month. Rent payments must be received
by the fifth of each month to avoid late fees. Late payment of rent will incur a penalty
of five percent (5%) of the monthly rent amount. Rent may be paid by check, money order,
or electronic bank transfer to the Landlord's designated account.

2. SECURITY DEPOSIT

Tenant shall pay a security deposit of Three Thousand Dollars ($3,000.00) prior to
move-in. The security deposit shall be returned within thirty (30) days of lease
termination, less any deductions for unpaid rent or damages beyond normal wear and tear.
Landlord may deduct from the security deposit for cleaning, repairs, and any outstanding
utility charges. The deposit cannot be applied as last month's rent without written consent.

3. UTILITIES

Tenant is responsible for all utilities including gas, electricity, water, and trash
removal. All utility accounts must be transferred to Tenant's name before move-in date.
Internet and cable television services are the sole responsibility of the Tenant.
Landlord is not liable for any utility service interruptions.
"""
    page1.insert_text((50, 50), text1, fontsize=10)

    # Page 2 - Maintenance, Pets, and Termination clauses
    page2 = doc.new_page()
    text2 = """
4. MAINTENANCE AND REPAIRS

Tenant is responsible for routine maintenance and minor repairs costing under $100.
Landlord shall maintain all major systems including HVAC, plumbing, electrical, and
structural components. Tenant must report any maintenance issues to Landlord within
48 hours of discovery. All repairs must be performed by licensed contractors approved
by Landlord. Landlord shall respond to emergency maintenance requests within 24 hours.

5. PET POLICY

No pets are allowed on the premises without prior written consent from the Landlord.
A non-refundable pet deposit of $500 is required for each approved pet. Dogs over 50
pounds and exotic animals are not permitted. Tenant must provide proof of pet vaccination
and liability insurance. Service animals are permitted as required by law without
additional deposit. Pet owners are fully liable for all damages caused by their animals.

6. TERMINATION

Either party may terminate this lease with sixty (60) days written notice. Early
termination by Tenant requires payment of two months rent as a penalty fee. Upon
termination, Tenant must return all keys and access devices to the Landlord. This
lease shall terminate automatically at the end of the lease term unless renewed in
writing. Lease termination notices must be sent via certified mail.

7. SUBLETTING

Tenant may not sublet or assign the premises without prior written consent from Landlord.
Any sublease must be approved in writing and does not release Tenant from obligations
under this lease. Short-term rentals including Airbnb are expressly prohibited.
Unauthorized subletting constitutes grounds for immediate lease termination.
"""
    page2.insert_text((50, 50), text2, fontsize=10)

    # Page 3 - Insurance, Default, and General clauses
    page3 = doc.new_page()
    text3 = """
8. INSURANCE

Tenant must maintain renter's insurance with minimum liability coverage of $100,000.
Proof of insurance must be provided to Landlord before move-in and upon each policy
renewal. Tenant's insurance policy must name Landlord as additional insured party.
Landlord's insurance does not cover Tenant's personal property or liability. Failure
to maintain required insurance coverage is grounds for lease termination.

9. DEFAULT AND REMEDIES

Failure to pay rent within ten (10) days of the due date constitutes default under
this lease agreement. Upon default, Landlord may pursue all legal remedies including
eviction proceedings. Tenant shall have thirty (30) days to cure any non-monetary
default after receiving written notice. In case of default, Tenant shall be liable
for Landlord's reasonable attorney fees and court costs. Repeated violations of lease
terms constitute grounds for immediate termination without cure period.

10. GENERAL PROVISIONS

This lease agreement shall be governed by the laws of the State. The premises shall
be used exclusively for residential purposes only. Landlord reserves the right to
enter the premises with 24-hour advance notice for inspections, repairs, or to show
the property to prospective tenants. Smoking is prohibited in all indoor areas of
the premises. This agreement constitutes the entire understanding between the parties.
All modifications must be in writing and signed by both Landlord and Tenant.


_______________________          _______________________
Landlord Signature               Tenant Signature

Date: _______________            Date: _______________
"""
    page3.insert_text((50, 50), text3, fontsize=10)

    # Save the document
    doc.save(output_path)
    doc.close()

    print(f"Sample lease PDF created: {output_path}")
    return output_path


if __name__ == '__main__':
    create_sample_lease_pdf()
