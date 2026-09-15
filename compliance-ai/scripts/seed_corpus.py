"""Generate sample legal document corpus for LegalLens demo.

Covers employment agreements, NDAs, service agreements, rental agreements,
and data processing agreements across multiple jurisdictions.

Run:  python scripts/seed_corpus.py  (from repo root)
Writes to ./backend/data/txt/*.md
"""
from __future__ import annotations

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "backend" / "data" / "txt"

DOCS: list[tuple[str, str]] = []


def doc(id_, front, body):
    fm = "---\n" + front.strip() + "\n---\n"
    DOCS.append((f"{id_}.md", fm + "\n" + body.strip() + "\n"))


def make():
    DOCS.clear()

    # ── 1) Employment Agreement (India) — ACTIVE, primary demo document ──
    doc(
        "EMP-AGR-001",
        """document_id: EMP-AGR-001
title: Employment Agreement — Arjun Mehta
document_type: CONTRACT
department: Legal
jurisdiction: IN
country: IN
state: Maharashtra
governing_law: Indian Contract Act, 1872
version: 1
effective_date: 2026-01-15
expiry_date: 2028-01-14
status: ACTIVE
authority: official
authority_type: CONTRACT
access_roles: Employee
citation: Employment Agreement dated 15 January 2026
tags: employment, contract, India, IP assignment, termination""",
        """
# Employment Agreement

This Employment Agreement ("Agreement") is entered into as of 15 January 2026 between TechVista Solutions Pvt. Ltd., a company incorporated under the Companies Act, 2013, with its registered office at Plot 42, Goregaon East, Mumbai 400063 ("Employer"), and Arjun Mehta, residing at 15 Lotus Colony, Andheri West, Mumbai 400058 ("Employee").

# 1. Position and Duties

The Employer hereby employs the Employee as Senior Software Engineer in the Technology Division. The Employee shall report to the Vice President of Engineering and shall perform such duties as are reasonably assigned.

# 2. Compensation

## 2.1 Base Salary
The Employee shall receive an annual base salary of INR 18,00,000 (Eighteen Lakh Rupees), payable monthly in arrears, subject to applicable tax deductions.

## 2.2 Annual Bonus
The Employee is eligible for an annual performance bonus of up to 20% of base salary, contingent upon individual and company performance metrics as determined by the Board.

## 2.3 Benefits
The Employee shall be entitled to health insurance coverage, provident fund contributions, and gratuity benefits as per Company policy and applicable law.

# 3. Probation

The Employee shall be on probation for a period of six (6) months from the Effective Date. During probation, either party may terminate this Agreement with fourteen (14) days' written notice.

# 4. Working Hours

Standard working hours shall be 9:30 AM to 6:30 PM IST, Monday through Friday, with a one-hour lunch break. The Employee may be required to work additional hours as necessary to fulfill job responsibilities.

# 5. Leave Entitlement

The Employee shall be entitled to annual leave, sick leave, and casual leave as per the Company's Leave Policy. Annual leave entitlement is 24 days per calendar year.

# 6. Confidentiality

## 6.1 Definition
"Confidential Information" includes all trade secrets, proprietary data, client lists, source code, algorithms, business strategies, financial information, and any other information designated as confidential by the Employer.

## 6.2 Obligation
The Employee shall not disclose, publish, or otherwise reveal any Confidential Information to any third party during or after employment, except as required by law or with prior written consent of the Employer.

## 6.3 Return of Materials
Upon termination, the Employee shall immediately return all documents, data, equipment, and materials belonging to the Employer.

# 7. Intellectual Property

## 7.1 Work Product Assignment
All inventions, discoveries, source code, algorithms, designs, documentation, and other work product ("Work Product") created by the Employee during the term of this Agreement, whether or not during working hours, and using Company resources, shall be the sole and exclusive property of the Employer.

## 7.2 Prior Inventions
The Employee has listed any prior inventions in Schedule A attached hereto. Any invention not listed in Schedule A shall be presumed to have been created during employment.

## 7.3 Moral Rights
To the extent permitted by applicable law, the Employee irrevocably assigns to the Employer all moral rights in the Work Product.

# 8. Non-Compete

## 8.1 During Employment
The Employee shall not engage in any competing business or employment during the term of this Agreement without prior written consent.

## 8.2 Post-Employment
For a period of twelve (12) months following termination, the Employee shall not directly or indirectly engage in, be employed by, or provide services to any Competing Business within India. "Competing Business" means any company engaged in enterprise software, AI solutions, or data analytics services.

# 9. Non-Solicitation

For a period of eighteen (18) months following termination, the Employee shall not solicit, recruit, or encourage any employee, contractor, or client of the Employer to leave or reduce their relationship with the Employer.

# 10. Termination

## 10.1 By Employer for Cause
The Employer may terminate this Agreement immediately upon written notice for: (a) material breach of this Agreement; (b) gross misconduct; (c) conviction of a criminal offense; or (d) willful neglect of duties.

## 10.2 By Employer Without Cause
The Employer may terminate this Agreement with ninety (90) days' written notice or payment in lieu of notice.

## 10.3 By Employee
The Employee may terminate this Agreement with ninety (90) days' written notice. The Employee may opt for payment in lieu of notice at the Employer's discretion.

## 10.4 Effect of Termination
Upon termination: (a) all unpaid salary and accrued benefits shall be paid within 30 days; (b) the Employee shall return all Company property; (c) confidentiality and IP assignment obligations survive termination.

# 11. Indemnification

The Employee shall indemnify and hold harmless the Employer from any losses, claims, or damages arising from the Employee's breach of this Agreement, including breach of confidentiality or IP assignment obligations.

# 12. Dispute Resolution

## 12.1 Negotiation
Any dispute arising out of this Agreement shall first be referred to senior management of both parties for good-faith negotiation within thirty (30) days.

## 12.2 Arbitration
If negotiation fails, the dispute shall be resolved by binding arbitration under the Arbitration and Conciliation Act, 1996, with a sole arbitrator appointed by mutual agreement. The seat of arbitration shall be Mumbai, India.

## 12.3 Governing Law
This Agreement shall be governed by and construed in accordance with the laws of India, specifically the Indian Contract Act, 1872.

# 13. Entire Agreement

This Agreement, including all schedules and annexures, constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements relating to the subject matter.

# 14. Severability

If any provision of this Agreement is found to be invalid or unenforceable, the remaining provisions shall continue in full force and effect.

# Schedule A — Prior Inventions

No prior inventions are listed by the Employee.
""",
    )

    # ── 2) Employment Agreement v2 (SUPERSEDED) — for comparison demo ──
    doc(
        "EMP-AGR-001-v2",
        """document_id: EMP-AGR-001-v2
title: Employment Agreement — Arjun Mehta (Superseded v2)
document_type: CONTRACT
department: Legal
jurisdiction: IN
country: IN
state: Maharashtra
governing_law: Indian Contract Act, 1872
version: 2
effective_date: 2024-06-01
status: SUPERSEDED
authority: official
authority_type: CONTRACT
access_roles: Employee
citation: Employment Agreement dated 1 June 2024 (Superseded)
tags: employment, contract, India, superseded""",
        """
# Employment Agreement (Version 2)

This Employment Agreement was entered into as of 1 June 2024 between TechVista Solutions Pvt. Ltd. ("Employer") and Arjun Mehta ("Employee").

# 1. Position and Duties

The Employee is employed as Software Engineer in the Technology Division.

# 2. Compensation

## 2.1 Base Salary
Annual base salary of INR 14,00,000 (Fourteen Lakh Rupees), payable monthly.

## 2.2 Annual Bonus
Eligible for annual performance bonus of up to 15% of base salary.

# 3. Probation

Probation period of six (6) months. During probation, either party may terminate with fourteen (14) days' notice.

# 4. Confidentiality

The Employee shall not disclose Confidential Information during or after employment.

# 5. Intellectual Property

## 5.1 Work Product
All work product created during employment hours using Company resources shall belong to the Employer.

# 6. Non-Compete

For six (6) months following termination, the Employee shall not engage in competing business within India.

# 7. Termination

## 7.1 By Employee
The Employee may terminate with thirty (30) days' written notice.

## 7.2 By Employer
The Employer may terminate with sixty (60) days' written notice or payment in lieu.

# 8. Dispute Resolution

Disputes shall be resolved by arbitration under the Arbitration and Conciliation Act, 1996. Governing law: laws of India.

# Status Notice

This version has been superseded by the current Employment Agreement (v3, effective 15 January 2026) and should not be treated as authoritative.
""",
    )

    # ── 3) Non-Disclosure Agreement (NDA) — ACTIVE ──
    doc(
        "NDA-001",
        """document_id: NDA-001
title: Mutual Non-Disclosure Agreement — TechVista & DataFlow Inc.
document_type: NDA
department: Legal
jurisdiction: US
country: US
state: Delaware
governing_law: Delaware General Corporation Law
version: 1
effective_date: 2026-03-01
expiry_date: 2028-02-28
status: ACTIVE
authority: official
authority_type: CONTRACT
access_roles: Employee
citation: Mutual NDA dated 1 March 2026
tags: NDA, confidentiality, mutual, US""",
        """
# Mutual Non-Disclosure Agreement

This Mutual Non-Disclosure Agreement ("Agreement") is entered into as of 1 March 2026 between TechVista Solutions Pvt. Ltd., with its registered office at Mumbai, India ("Disclosing Party A"), and DataFlow Inc., a Delaware corporation with its principal office at 500 Innovation Drive, Wilmington, DE 19801 ("Disclosing Party B").

# 1. Purpose

The parties wish to explore a potential business relationship concerning artificial intelligence and data analytics services ("Purpose"). In connection with the Purpose, each party may disclose Confidential Information to the other.

# 2. Definition of Confidential Information

"Confidential Information" means any non-public information disclosed by either party, including but not limited to: (a) trade secrets, inventions, and patent applications; (b) software, source code, and algorithms; (c) business plans, financial data, and customer lists; (d) product roadmaps and technical specifications; (e) marketing strategies and pricing information.

# 3. Exclusions

Confidential Information does not include information that: (a) is or becomes publicly available through no fault of the receiving party; (b) was known to the receiving party before disclosure; (c) is independently developed without use of Confidential Information; (d) is received from a third party without restriction.

# 4. Obligations

## 4.1 Non-Disclosure
Each party shall maintain the confidentiality of all Confidential Information and shall not disclose it to any third party without prior written consent.

## 4.2 Standard of Care
Each party shall use at least the same degree of care to protect Confidential Information as it uses to protect its own confidential information, but no less than reasonable care.

## 4.3 Permitted Disclosure
A party may disclose Confidential Information to its employees, contractors, and advisors who have a need to know and are bound by confidentiality obligations no less restrictive than this Agreement.

# 5. Term and Termination

## 5.1 Term
This Agreement shall remain in effect for two (2) years from the Effective Date.

## 5.2 Survival
Confidential Information obligations shall survive termination for a period of three (3) years.

# 6. Return of Materials

Upon termination or request, each party shall promptly return or destroy all Confidential Information and certify such return or destruction in writing.

# 7. Remedies

Each party acknowledges that breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate. The disclosing party shall be entitled to seek injunctive relief in addition to any other remedies available at law.

# 8. Governing Law

This Agreement shall be governed by the laws of the State of Delaware, without regard to conflict of laws principles.

# 9. Entire Agreement

This Agreement constitutes the entire understanding between the parties regarding the subject matter hereof.
""",
    )

    # ── 4) SaaS Service Agreement — ACTIVE ──
    doc(
        "SVC-AGR-001",
        """document_id: SVC-AGR-001
title: SaaS Service Agreement — CloudAnalytics Platform
document_type: AGREEMENT
department: Legal
jurisdiction: US
country: US
state: California
governing_law: California Commercial Code
version: 1
effective_date: 2026-02-01
expiry_date: 2027-01-31
status: ACTIVE
authority: official
authority_type: CONTRACT
access_roles: Employee
citation: SaaS Service Agreement dated 1 February 2026
tags: SaaS, service agreement, data processing, SLA, liability""",
        """
# SaaS Service Agreement

This SaaS Service Agreement ("Agreement") is entered into as of 1 February 2026 between CloudAnalytics Inc., a California corporation ("Provider"), and TechVista Solutions Pvt. Ltd. ("Customer").

# 1. Service Description

Provider shall make available the CloudAnalytics platform ("Service") for data analytics, reporting, and visualization. The Service is provided on a subscription basis via the internet.

# 2. Subscription Term

## 2.1 Initial Term
The initial subscription term is twelve (12) months from the Effective Date.

## 2.2 Renewal
The subscription shall automatically renew for successive twelve-month periods unless either party provides sixty (60) days' written notice of non-renewal.

# 3. Fees and Payment

## 3.1 Subscription Fee
Customer shall pay an annual subscription fee of USD 48,000 (Forty-Eight Thousand Dollars), payable in quarterly installments of USD 12,000.

## 3.2 Late Payment
Overdue amounts shall accrue interest at 1.5% per month or the maximum rate permitted by law, whichever is less.

## 3.3 Taxes
All fees are exclusive of taxes. Customer is responsible for applicable sales tax, use tax, or VAT.

# 4. Service Level Agreement (SLA)

## 4.1 Uptime
Provider guarantees 99.5% monthly uptime, measured as total minutes minus downtime divided by total minutes.

## 4.2 Downtime Exclusions
Scheduled maintenance windows (48 hours advance notice) and force majeure events are excluded from uptime calculations.

## 4.3 Service Credits
If uptime falls below 99.5%, Customer shall receive a service credit of 5% of the monthly fee for each 0.1% below the guarantee, up to a maximum of 25% of the monthly fee.

# 5. Data Processing

## 5.1 Data Ownership
Customer retains all rights, title, and interest in its data. Provider claims no ownership over Customer data.

## 5.2 Data Processing Addendum
Provider shall process Customer data in accordance with the Data Processing Addendum ("DPA") attached as Exhibit A.

## 5.3 Data Security
Provider shall implement and maintain industry-standard security measures including encryption at rest (AES-256) and in transit (TLS 1.3), access controls, and regular security audits.

# 6. Limitation of Liability

## 6.1 Cap
EXCEPT FOR INDEMNIFICATION OBLIGATIONS AND BREACH OF CONFIDENTIALITY, EACH PARTY'S TOTAL AGGREGATE LIABILITY UNDER THIS AGREEMENT SHALL NOT EXCEED THE TOTAL FEES PAID OR PAYABLE DURING THE TWELVE (12) MONTHS PRECEDING THE CLAIM.

## 6.2 Exclusion
NEITHER PARTY SHALL BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, REGARDLESS OF THE CAUSE OF ACTION.

# 7. Indemnification

## 7.1 Provider Indemnity
Provider shall indemnify Customer against third-party claims alleging that the Service infringes intellectual property rights.

## 7.2 Customer Indemnity
Customer shall indemnify Provider against claims arising from Customer's data or use of the Service in violation of applicable law.

# 8. Termination

## 8.1 For Cause
Either party may terminate immediately upon written notice if the other party materially breaches and fails to cure within thirty (30) days of notice.

## 8.2 For Convenience
Customer may terminate with ninety (90) days' written notice, but no refund of prepaid fees shall be provided.

## 8.3 Effect of Termination
Upon termination, Provider shall make Customer data available for export for sixty (60) days, after which data may be deleted.

# 9. Confidentiality

Each party shall maintain the confidentiality of the other party's Confidential Information for the duration of this Agreement and for two (2) years thereafter.

# 10. Governing Law

This Agreement shall be governed by the laws of the State of California. Any dispute shall be resolved in the state or federal courts located in San Francisco, California.

# 11. Data Processing Addendum (Exhibit A)

Provider shall: (a) process data only on documented instructions from Customer; (b) ensure personnel are bound by confidentiality; (c) implement appropriate technical and organizational measures; (d) assist Customer in responding to data subject requests; (e) delete or return all personal data upon termination.
""",
    )

    # ── 5) Rental Agreement (India) — ACTIVE ──
    doc(
        "REN-AGR-001",
        """document_id: REN-AGR-001
title: Residential Rental Agreement — Flat 12B, Malad West
document_type: AGREEMENT
department: Legal
jurisdiction: IN
country: IN
state: Maharashtra
governing_law: Maharashtra Rent Control Act, 1999
version: 1
effective_date: 2026-04-01
expiry_date: 2027-03-31
status: ACTIVE
authority: official
authority_type: CONTRACT
access_roles: Employee
citation: Rental Agreement dated 1 April 2026
tags: rental, lease, residential, India, deposit, maintenance""",
        """
# Residential Rental Agreement

This Rental Agreement ("Agreement") is entered into as of 1 April 2026 between Mrs. Sunita Kapoor ("Landlord") and Mr. Arjun Mehta ("Tenant").

# 1. Premises

The Landlord agrees to rent to the Tenant the residential flat bearing No. 12B on the 12th floor of Green Valley Apartments, Plot 88, Malad West, Mumbai 400064 ("Premises"), comprising 2 bedrooms, 2 bathrooms, 1 kitchen, and 1 living room, with a total area of 950 square feet.

# 2. Term

## 2.1 Initial Term
The tenancy shall commence on 1 April 2026 and expire on 31 March 2027, a period of twelve (12) months.

## 2.2 Renewal
The tenancy may be renewed by mutual written agreement at least thirty (30) days before expiry.

# 3. Rent

## 3.1 Monthly Rent
The Tenant shall pay a monthly rent of INR 35,000 (Thirty-Five Thousand Rupees) payable in advance on or before the 5th of each calendar month.

## 3.2 Payment Method
Rent shall be paid by bank transfer to the Landlord's designated account or by cheque.

## 3.3 Late Payment
If rent is not paid by the 10th of the month, the Tenant shall pay a late fee of INR 500 per day until payment is received.

# 4. Security Deposit

## 4.1 Amount
The Tenant has paid a security deposit of INR 1,05,000 (One Lakh Five Thousand Rupees), equivalent to three months' rent.

## 4.2 Refund
The deposit shall be refunded within thirty (30) days of the termination of this Agreement, after deducting any unpaid rent, damages beyond normal wear and tear, or outstanding utility bills.

# 5. Maintenance and Repairs

## 5.1 Landlord Responsibility
The Landlord shall be responsible for structural repairs, plumbing and electrical issues arising from normal wear and tear, and common area maintenance.

## 5.2 Tenant Responsibility
The Tenant shall maintain the Premises in good condition and be responsible for minor repairs, interior painting, and replacement of consumables (bulbs, fuses, etc.).

## 5.3 Alterations
The Tenant shall not make any structural alterations or modifications without the Landlord's prior written consent.

# 6. Utilities

The Tenant shall be responsible for payment of electricity, water, gas, internet, and maintenance charges. The Landlord shall pay property tax and society charges.

# 7. Subletting

The Tenant shall not sublet, assign, or part with possession of the Premises or any part thereof without the Landlord's prior written consent.

# 8. Termination

## 8.1 By Tenant
The Tenant may terminate this Agreement with sixty (60) days' written notice to the Landlord.

## 8.2 By Landlord
The Landlord may terminate this Agreement with ninety (90) days' written notice if: (a) the Tenant fails to pay rent for two consecutive months; (b) the Tenant breaches any term of this Agreement; (c) the Landlord requires the Premises for personal use.

## 8.3 Early Termination
If the Tenant terminates before the expiry of the initial term without cause, the security deposit shall be forfeited.

# 9. Restrictions

The Tenant shall not: (a) use the Premises for any illegal purpose; (b) cause nuisance or disturbance to neighbors; (c) keep pets without prior written consent; (d) use the Premises for commercial purposes.

# 10. Governing Law

This Agreement shall be governed by the Maharashtra Rent Control Act, 1999 and the laws of India. Any dispute shall be subject to the jurisdiction of the courts in Mumbai.

# 11. Entire Agreement

This Agreement constitutes the entire understanding between the parties and supersedes all prior discussions and agreements.
""",
    )

    # ── 6) GDPR Data Processing Agreement — ACTIVE ──
    doc(
        "DPA-001",
        """document_id: DPA-001
title: GDPR Data Processing Agreement — TechVista & CloudAnalytics
document_type: AGREEMENT
department: Legal
jurisdiction: EU
country: EU
state: ""
governing_law: General Data Protection Regulation (EU) 2016/679
version: 1
effective_date: 2026-02-01
status: ACTIVE
authority: official
authority_type: REGULATION
access_roles: Employee
citation: DPA dated 1 February 2026, pursuant to GDPR Article 28
tags: GDPR, data processing, privacy, EU, Article 28""",
        """
# Data Processing Agreement

This Data Processing Agreement ("DPA") is entered into as of 1 February 2026 between TechVista Solutions Pvt. Ltd. ("Controller") and CloudAnalytics Inc. ("Processor"), pursuant to Article 28 of the General Data Protection Regulation (EU) 2016/679 ("GDPR").

# 1. Scope and Purpose

This DPA governs the processing of personal data by Processor on behalf of Controller in connection with the SaaS Service Agreement dated 1 February 2026.

# 2. Definitions

"Personal Data" means any information relating to an identified or identifiable natural person, as defined in GDPR Article 4(1).

"Processing" means any operation performed on personal data, including collection, recording, organization, structuring, storage, adaptation, retrieval, consultation, use, disclosure, or erasure, as defined in GDPR Article 4(2).

"Data Subject" means the identified or identifiable natural person to whom the personal data relates.

# 3. Details of Processing

## 3.1 Subject Matter
Processor shall process personal data to provide the CloudAnalytics platform services.

## 3.2 Duration
Processing shall occur for the duration of the SaaS Service Agreement.

## 3.3 Nature and Purpose
Processing includes ingestion, storage, aggregation, and analysis of business data that may contain personal data of Controller's employees and customers.

## 3.4 Categories of Data Subjects
Employees, customers, and business contacts of Controller.

## 3.5 Types of Personal Data
Names, email addresses, phone numbers, job titles, IP addresses, usage data, and transaction records.

# 4. Processor Obligations

## 4.1 Documented Instructions
Processor shall process personal data only on documented instructions from Controller, including with regard to transfers to third countries, unless required by EU or Member State law.

## 4.2 Confidentiality
Processor shall ensure that all persons authorized to process personal data have committed themselves to confidentiality or are under an appropriate statutory obligation of confidentiality.

## 4.3 Security Measures
Processor shall implement appropriate technical and organizational measures in accordance with GDPR Article 32, including: (a) encryption of personal data; (b) the ability to ensure ongoing confidentiality, integrity, availability, and resilience; (c) the ability to restore availability and access in a timely manner; (d) regular testing and evaluation of measures.

## 4.4 Sub-Processors
Processor shall not engage another processor without prior specific or general written authorization of Controller. Where general authorization is given, Processor shall inform Controller of any intended changes, giving Controller the opportunity to object.

## 4.5 Data Subject Rights
Processor shall assist Controller by appropriate technical and organizational measures in fulfilling obligations to respond to data subject requests under GDPR Articles 15-22.

## 4.6 Breach Notification
Processor shall notify Controller without undue delay after becoming aware of a personal data breach under GDPR Article 33.

## 4.7 Data Protection Impact Assessment
Processor shall assist Controller in carrying out data protection impact assessments under GDPR Article 35.

# 5. Controller Obligations

## 5.1 Compliance
Controller warrants that it has a valid legal basis for processing personal data and has provided all necessary notices to data subjects.

## 5.2 Instructions
Controller shall ensure its instructions to Processor comply with GDPR and applicable law.

# 6. International Transfers

Processor shall not transfer personal data outside the European Economic Area without Controller's prior written consent and appropriate safeguards under GDPR Chapter V, including Standard Contractual Clauses.

# 7. Audit Rights

Controller shall have the right to audit Processor's compliance with this DPA. Processor shall make available all information necessary to demonstrate compliance and shall allow for and contribute to audits and inspections.

# 8. Data Deletion

Upon termination of the SaaS Service Agreement, Processor shall, at Controller's choice, delete or return all personal data and delete existing copies, unless EU or Member State law requires continued storage.

# 9. Liability

Each party shall be liable for damage caused by processing that violates the GDPR, in accordance with GDPR Article 82.

# 10. Governing Law

This DPA shall be governed by the laws of the European Union, specifically the General Data Protection Regulation (EU) 2016/679.
""",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in DOCS:
        (OUT_DIR / name).write_text(content, encoding="utf-8")
        written.append(name)
    print(f"Wrote {len(written)} legal docs to {OUT_DIR}")
    for n in written:
        print("  -", n)


if __name__ == "__main__":
    make()
