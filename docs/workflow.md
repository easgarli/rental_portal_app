Let's have closer look at the workflow: 
Note: The display language of the project is Azerbaijani. All buttons, page names, display texts etc should be in Azerbaijani language.
1. The Landlord registers himself at the portal by providing email and password
2. The Landlord provides personal information to be used in the contracts by providing the following information:
{LandlordFirstName}, {LandlordLastName}, {LandlordFatherName}, {LandlordID}, {LandlordFIN}, {LandlordBirthPlace}, {LandlordBirthDate}, and {LandlordAddress}
3. The Landlord posts his available for rent Properties by indicating the following details:
Property title, Property pictures, {PropertyAddress}, {PropertyArea}, {RentAmount}
4. All posted Properties by all landlords are seen on the home page of the Portal by public with the folloiwng detailes displayed
Property title, Property pictures, {PropertyAddress}, {PropertyArea}, {RentAmount}, Landlord's average rating by tenants
5. If the potential Tenant wants to apply for a Property he is forwarded to the registration page where he registers himself by providing email and password
6. The Tenant provides personal information to be used in the contracts by providing the following information:
{TenantFirstName}, {TenantLastName}, {TenantFatherName}, {TenantID}, {TenantFIN}, {TenantBirthPlace}, {TenantBirthDate}, and {TenantAddress}.
7. After Tenant is registered he can Apply for the Property for renting it.
8. The Landlord can see the Application to hsi Property and approves or rejects the Application
9. If the Landlord approves the Application he can escalate it to the Contract drafting stage where he adds missing personal and Property information to the Contract
10. The Property information required for the Contract drafting is:
* {PropertyRegistryNumber} {PropertyAddress} and {PropertyArea} should be replaced with the details of the property.
* {RentAmount} should be replaced with the agreed rent amount.
11. The Contract information for the Contract drafting is:
* {ContractNo} will be provided by the Portal 
* {ContractDate} will be the date when the Landlord drafted the Contract
* {ContractTerm} will be defined by the Landlord
12. The Contract needs to have the required information about Tenant, Landlord and Property in order the signing step to be allowed. 13. The template of the Contract is give in templates/contracts/contract_template.txt file. All the fields obtained from the Tenant and Landlord are placed into the respective placeholders marked with {{filed_name}} in this template file.
13. After the Contact is ready for signature, any party can sign it without waiting for the other party
14. The Contract is deemed to be signed when both parties signs it
15. The Contract should display the fact of signing by both parties and their date of signing
16. After Contract is signed the parties can rate one another
16.1. İcarəyə verənin icarədarı qiymətləndirməsi (0-5 bal):
* Ödəniş intizamı (vaxtında və tam ödəmələr)
* Əmlaka münasibət (əmlakı qoruyub saxlama səviyyəsi)
* Ünsiyyət və əməkdaşlıq (problemləri həll etmək üçün açıq və səmimi ünsiyyət)
* Qonşular və binaya münasibət (ətrafdakı insanlara və bina qaydalarına riayət)
* Müqavilə şərtlərinə uyğunluq (çıxış müddəti, depozit qaydalarına əməl etmə)
16.2. İcarədarın icarəyə verəni qiymətləndirməsi (0-5 bal):
* Əmlakın real vəziyyəti (verilən məlumatların doğruluğu)
* Müqavilə şəffaflığı (aydın və ədalətli şərtlər)
* Ünsiyyət və dəstək (problemlərin həllində aktiv iştirak)
* Təmir və texniki xidmət (gərəkli təmir işlərinin aparılması)
* Gizlilik və hörmət (icarədarın şəxsi həyatına hörmət)
17. The Tenant is offered to get KreditSkor with the call to action message: "Kredit skorunuzu hesablamaq üçün anketi doldurun və daha yaxşı şərtlərlə mənzil kirayəyə götürün."
17.1. The Tenant answers questionionnaire and given a KreditSkor
The logic of the KreditSkor is given as:
'''
SCORING_RULES = {
    'Yaşı': {'max_score': 50, 'options': {'20-27': 30, '27-50': 50, '50-60': 40, '60-65': 30, '65-68': 20, '68-dən çox': 0}},
    'Cinsi': {'max_score': 20, 'options': {'Kişi': 15, 'Qadın': 20}},
    'Ailə vəziyyəti': {'max_score': 30, 'options': {'Evli': 30, 'Evli olmayan': 20}},
    'Öhdəsində olanların sayı': {'max_score': 50, 'options': {'3 və ya 3-dən az': 50, '3-dən çox': 35}},
    'Təhsili': {'max_score': 50, 'options': {'Orta': 30, 'Ali': 50}},
    'Ümumi fəaliyyət sektoru': {'max_score': 240, 'options': {'Ən az riskli qrup': 240, 'Az riskli qrup': 200, 'Orta riskli qrup': 160, 'Nisbətən yüksək riskli qrup': 120, 'Rəsmi gəliri olmayanlar': 80}},
    'Hazırki iş yeri üzrə əmək stajı': {'max_score': 80, 'options': {'3 aydan az': 0, '3 ay-6 ay': 60, '6ay - 1 il': 70, '1 ildən çox': 80}},
    'Kredit tarixçəsi': {'max_score': 280, 'options': {'Kredit tarixçəsi yoxdur': 140, 'Son 6 ayda 0-30 gün gecikmə': 280, 'Son 6 ayda 30-90 gün gecikmə': 200, 'Son 6 ayda 90 gündən çox gecikmə': 0}},
    'Aylıq ödəniş məbləğinin Aylıq sərbəst vəsaitə nisbəti': {'max_score': 200, 'options': {'90%-dən çoxdursa': 0, '70-90%': 100, '50-70%': 150, '50%-dən az': 200}}
}
sector_risk_mapping = {
    'Ən az riskli qrup': ['Bank', 'Sığorta', 'Təhsil qrumları', 'Dövlət qrumları', 'Səhiyyə qrumları', 'Neft şirkəti'],
    'Az riskli qrup': ['Enerji', 'Məhkəmə', 'Hərbi və Güc strukturu', 'Təqaüdçü', 'Telekommunikasiya və rabitə'],
    'Orta riskli qrup': ['Turizim', 'Tv Nəşriyyat', 'Əyləncə Hotel Restoran', 'İncəsənət', 'Sahibkar'],
    'Nisbətən yüksək riskli qrup': ['İdman', 'Tikinti', 'Nəqliyyat', 'İstehsalat'],
    'Rəsmi gəliri olmayanlar': ['Rəsmi gəliri olmayan']
}

def calculate_credit_score(data):
    """Calculate credit score based on questionnaire responses"""
    total_score = 0
    field_to_rule = {
        'age_group': 'Yaşı',
        'gender': 'Cinsi',
        'marital_status': 'Ailə vəziyyəti',
        'dependents': 'Öhdəsində olanların sayı',
        'education': 'Təhsili',
        'work_experience': 'Hazırki iş yeri üzrə əmək stajı',
        'credit_history': 'Kredit tarixçəsi'
    }
    
    # Map work sector to risk group
    work_sector = data.get('work_sector')
    sector_group = None
    for group, sectors in sector_risk_mapping.items():
        if work_sector in sectors:
            sector_group = group
            break
    
    if sector_group:
        score = SCORING_RULES['Ümumi fəaliyyət sektoru']['options'].get(sector_group, 0)
        total_score += score

    # Calculate scores for each field
    for field, rule_key in field_to_rule.items():
        if field in data:
            value = data[field]
            score = SCORING_RULES[rule_key]['options'].get(value, 0)
            print(f"Field: {field}, Value: {value}, Score: {score}")  # Debug print
            total_score += score

    # Calculate score for income/rent ratio
    if all(key in data for key in ['monthly_income', 'monthly_expenses', 'planned_rent']):
        monthly_income = float(data['monthly_income'])
        monthly_expenses = float(data['monthly_expenses'])
        planned_rent = float(data['planned_rent'])
        net_monthly_income = monthly_income - monthly_expenses

        if net_monthly_income > 0:
            ratio = planned_rent / net_monthly_income
            ratio_score = 0
            if ratio > 0.9:
                ratio_score = 0
            elif 0.7 <= ratio <= 0.9:
                ratio_score = 100
            elif 0.5 <= ratio < 0.7:
                ratio_score = 150
            else:
                ratio_score = 200
            print(f"Income: {net_monthly_income}, Rent: {planned_rent}, Ratio: {ratio}, Score: {ratio_score}")
            total_score += ratio_score

    print(f"Total Score: {total_score}")  # Debug print
    return total_score
'''
17.2. The meaning of the KreditSkor:
* 850-1000: Əla kredit skoru
* 700-849: Yaxşı kredit skoru
* 600-699: Orta kredit skoru
* 0-599: Riskli kredit skoru
18. The Tenant will also be a TenantSkor that will summarize how relaible he is as a Tenant with the following logic:
18.1.TenantScore Components and Weights
* Ödəniş intizamı (30%) – Ödənişlərin gecikməsi və ya tam olmaması
   - On-time payments: 100 points
   - Late payments (1-3 days): 75 points
   - Late payments (4-7 days): 50 points
   - Late payments (8-15 days): 25 points
   - Late payments (>15 days): 0 points
   - Partial payments: -20 points per occurrence
   - Payment history duration: Last 24 months
* Əmlaka münasibət (25%) – Əmlaka ziyan vurub-vurmaması
   - No damage: 100 points
   - Minor damage (easily repairable): 75 points
   - Moderate damage (requires professional repair): 50 points
   - Major damage (significant repair needed): 25 points
   - Severe damage (property uninhabitable): 0 points
   - Regular maintenance: +10 points
   - Property improvement: +15 points
* Əvvəlki icarə tarixçəsi (20%) – Digər icarəyə verənlərdən aldığı ortalama reytinq
   - Average landlord rating (0-5 stars):
     * 5 stars: 100 points
     * 4 stars: 80 points
     * 3 stars: 60 points
     * 2 stars: 40 points
     * 1 star: 20 points
     * 0 stars: 0 points
   - Number of previous rentals:
     * 1-2 rentals: Base score
     * 3-5 rentals: +10 points
     * 6+ rentals: +20 points
   - Rental duration:
     * <6 months: -20 points
     * 6-12 months: Base score
     * 12-24 months: +10 points
     * >24 months: +20 points
* Qonşularla və bina qaydalarına uyğunluq (15%) – Şikayətlərin olub-olmaması
   - No complaints: 100 points
   - Minor complaints (resolved): 75 points
   - Moderate complaints (multiple): 50 points
   - Serious complaints (legal action): 25 points
   - Eviction due to complaints: 0 points
   - Positive neighbor feedback: +10 points
   - Community participation: +5 points
* Müqavilə şərtlərinə uyğunluq (10%) – Müqaviləyə riayət edib-etməməsi
- Full compliance: 100 points
   - Minor violations (resolved): 75 points
   - Moderate violations (multiple): 50 points
   - Major violations (legal action): 25 points
   - Contract termination due to violations: 0 points
   - Early contract renewal: +10 points
   - Additional contract terms fulfilled: +5 points
18.2. Score Calculation Algorithm
def calculate_tenant_score(tenant_data):
    """Calculate tenant score based on various factors"""
    total_score = 0
    
    # 1. Payment Discipline (30%)
    payment_score = calculate_payment_score(tenant_data.payment_history)
    total_score += payment_score * 0.30
    
    # 2. Property Care (25%)
    property_score = calculate_property_score(tenant_data.property_history)
    total_score += property_score * 0.25
    
    # 3. Previous Rental History (20%)
    rental_score = calculate_rental_score(tenant_data.rental_history)
    total_score += rental_score * 0.20
    
    # 4. Neighbor and Building Rules Compliance (15%)
    compliance_score = calculate_compliance_score(tenant_data.compliance_history)
    total_score += compliance_score * 0.15
    
    # 5. Contract Compliance (10%)
    contract_score = calculate_contract_score(tenant_data.contract_history)
    total_score += contract_score * 0.10
    
    return round(total_score, 2)

def calculate_payment_score(payment_history):
    """Calculate payment discipline score"""
    base_score = 100
    deductions = 0
    bonuses = 0
    
    for payment in payment_history:
        if payment.is_late:
            days_late = payment.days_late
            if days_late <= 3:
                deductions += 25
            elif days_late <= 7:
                deductions += 50
            elif days_late <= 15:
                deductions += 75
            else:
                deductions += 100
        
        if payment.is_partial:
            deductions += 20
    
    return max(0, base_score - deductions + bonuses)

def calculate_property_score(property_history):
    """Calculate property care score"""
    base_score = 100
    deductions = 0
    bonuses = 0
    
    for incident in property_history.damage_incidents:
        if incident.severity == 'minor':
            deductions += 25
        elif incident.severity == 'moderate':
            deductions += 50
        elif incident.severity == 'major':
            deductions += 75
        else:  # severe
            deductions += 100
    
    if property_history.regular_maintenance:
        bonuses += 10
    if property_history.improvements:
        bonuses += 15
    
    return max(0, base_score - deductions + bonuses)

def calculate_rental_score(rental_history):
    """Calculate previous rental history score"""
    base_score = rental_history.average_rating * 20  # Convert 0-5 to 0-100
    
    # Add points for number of rentals
    if rental_history.total_rentals >= 6:
        base_score += 20
    elif rental_history.total_rentals >= 3:
        base_score += 10
    
    # Add points for rental duration
    if rental_history.average_duration > 24:
        base_score += 20
    elif rental_history.average_duration > 12:
        base_score += 10
    elif rental_history.average_duration < 6:
        base_score -= 20
    
    return max(0, min(100, base_score))

def calculate_compliance_score(compliance_history):
    """Calculate neighbor and building rules compliance score"""
    base_score = 100
    deductions = 0
    bonuses = 0
    
    for complaint in compliance_history.complaints:
        if complaint.severity == 'minor':
            deductions += 25
        elif complaint.severity == 'moderate':
            deductions += 50
        elif complaint.severity == 'serious':
            deductions += 75
        else:  # eviction
            deductions += 100
    
    if compliance_history.positive_feedback:
        bonuses += 10
    if compliance_history.community_participation:
        bonuses += 5
    
    return max(0, base_score - deductions + bonuses)

def calculate_contract_score(contract_history):
    """Calculate contract compliance score"""
    base_score = 100
    deductions = 0
    bonuses = 0
    
    for violation in contract_history.violations:
        if violation.severity == 'minor':
            deductions += 25
        elif violation.severity == 'moderate':
            deductions += 50
        elif violation.severity == 'major':
            deductions += 75
        else:  # termination
            deductions += 100
    
    if contract_history.early_renewal:
        bonuses += 10
    if contract_history.additional_terms_fulfilled:
        bonuses += 5
    
    return max(0, base_score - deductions + bonuses)
18.3 Score Interpretation:
90-100: Çox etibarlı icarədar (Very Reliable Tenant)
- Excellent payment history
- No property damage
- High landlord ratings
- No neighbor complaints
- Full contract compliance

75-89: Yaxşı icarədar (Good Tenant)
- Mostly on-time payments
- Minor property issues
- Good landlord ratings
- Rare minor complaints
- Minor contract violations

50-74: Orta riskli icarədar (Medium Risk Tenant)
- Some late payments
- Some property damage
- Average landlord ratings
- Some neighbor complaints
- Some contract violations

0-49: Yüksək riskli icarədar (High Risk Tenant)
- Frequent late payments
- Significant property damage
- Poor landlord ratings
- Multiple complaints
- Major contract violations
18.4. Score Update Frequency
- Real-time updates for:
  * Payment status changes
  * New complaints
  * Contract violations
  * Property damage reports

- Monthly updates for:
  * Payment history
  * Average ratings
  * Compliance status

- Quarterly reviews for:
  * Overall score recalculation
  * Historical trend analysis
  * Score adjustments

19. Payment Tracking Workflow
A. Payment Creation and Scheduling:
   1. System automatically creates monthly rent payments based on contract terms
   2. Landlord can create additional payments (utilities, maintenance, etc.)
   3. Tenant can schedule payments in advance
   4. System sends payment reminders:
      - 7 days before due date
      - 3 days before due date
      - On due date
      - After due date (for late payments)

B. Payment Processing:
   1. Tenant initiates payment:
      - Selects payment method
      - Confirms amount
      - Submits payment
   2. System processes payment:
      - Validates payment details
      - Processes through payment gateway
      - Updates payment status
   3. Payment confirmation:
      - System notifies both parties
      - Updates contract payment history
      - Updates tenant's payment score

C. Late Payment Handling:
   1. Automatic late fee calculation:
      - 1-3 days late: 5% of rent
      - 4-7 days late: 10% of rent
      - 8+ days late: 15% of rent
   2. Late payment notifications:
      - Daily reminders
      - Warning about potential contract violation
   3. Escalation process:
      - After 15 days: Formal notice
      - After 30 days: Contract violation
      - After 45 days: Potential eviction process

D. Payment Disputes:
   1. Dispute initiation:
      - Either party can initiate dispute
      - Must provide reason and evidence
   2. Dispute resolution:
      - System notifies both parties
      - 7-day response period
      - Mediation process if needed
   3. Resolution outcomes:
      - Payment adjustment
      - Full refund
      - Partial refund
      - Dispute dismissed

E. Payment History and Reporting:
   1. Detailed payment history:
      - All payments and their status
      - Payment method used
      - Transaction IDs
      - Timestamps
   2. Payment analytics:
      - On-time payment percentage
      - Average payment delay
      - Payment method preferences
   3. Exportable reports:
      - Monthly payment summaries
      - Year-end statements
      - Tax documentation

F. Security Deposit Management:
   1. Initial deposit:
      - Collection and verification
      - Escrow account management
   2. Deposit deductions:
      - Property damage assessment
      - Utility bill settlements
      - Cleaning fees
   3. Deposit return:
      - Final inspection
      - Deduction approval
      - Refund processing

G. Automated Payment Features:
   1. Recurring payments:
      - Automatic monthly rent collection
      - Scheduled utility payments
   2. Payment splitting:
      - Multiple payment methods
      - Partial payments
   3. Payment scheduling:
      - Future-dated payments
      - Payment frequency options

H. Integration with TenantScore:
   1. Payment history impact:
      - On-time payments: +10 points
      - Late payments: -5 points per occurrence
      - Partial payments: -3 points per occurrence
   2. Payment pattern analysis:
      - Consistent on-time payments
      - Payment reliability score
      - Risk assessment

20. State Machines
20.1. Property State Machine:
States:
- available: Property is available for rent
- pending_contract: Property has an approved application
- rented: Property is currently rented
- unavailable: Property is not available for rent (maintenance, etc.)

Transitions:
available -> pending_contract:
  - Trigger: Application approved
  - Required: Valid application exists
  - Actions: Update property status, notify tenant

pending_contract -> available:
  - Trigger: Contract not signed within timeframe
  - Required: No active contract
  - Actions: Reset property status, notify landlord

pending_contract -> rented:
  - Trigger: Contract signed by both parties
  - Required: Valid contract exists
  - Actions: Update property status, notify both parties

rented -> available:
  - Trigger: Contract terminated or completed
  - Required: Contract end date reached or termination confirmed
  - Actions: Update property status, notify landlord

available -> unavailable:
  - Trigger: Landlord marks property as unavailable
  - Required: No active applications
  - Actions: Update property status

unavailable -> available:
  - Trigger: Landlord marks property as available
  - Required: None
  - Actions: Update property status

20.2. Application State Machine
States:
- draft: Application is being created
- submitted: Application is submitted by tenant
- under_review: Landlord is reviewing application
- approved: Application is approved
- rejected: Application is rejected
- expired: Application not acted upon in time

Transitions:
draft -> submitted:
  - Trigger: Tenant submits application
  - Required: All required fields completed
  - Actions: Send notification to landlord

submitted -> under_review:
  - Trigger: Landlord starts review
  - Required: None
  - Actions: Update application status

under_review -> approved:
  - Trigger: Landlord approves application
  - Required: None
  - Actions: Update status, notify tenant, create contract draft

under_review -> rejected:
  - Trigger: Landlord rejects application
  - Required: None
  - Actions: Update status, notify tenant

submitted -> expired:
  - Trigger: Timeout (e.g., 7 days)
  - Required: No action taken by landlord
  - Actions: Update status, notify both parties

approved -> draft:
  - Trigger: Contract not created within timeframe
  - Required: No contract exists
  - Actions: Reset application status

20.3. Contract State Machine:
States:
- draft: Contract is being created
- pending_signatures: Contract is ready for signatures
- active: Contract is signed by both parties
- completed: Contract has ended normally
- terminated: Contract was terminated early

Transitions:
draft -> pending_signatures:
  - Trigger: All required information added
  - Required: Complete tenant, landlord, and property info
  - Actions: Enable signature functionality

pending_signatures -> active:
  - Trigger: Both parties sign contract
  - Required: Both signatures present
  - Actions: Activate contract, notify both parties

active -> completed:
  - Trigger: Contract end date reached
  - Required: All obligations fulfilled
  - Actions: Update status, trigger final payments

active -> terminated:
  - Trigger: Early termination requested
  - Required: Valid termination reason
  - Actions: Process termination, handle penalties

pending_signatures -> draft:
  - Trigger: Information needs updating
  - Required: No signatures yet
  - Actions: Allow editing of contract details

20.4. Payment State Machine
States:
- pending: Payment is due
- processing: Payment is being processed
- completed: Payment is successful
- failed: Payment failed
- refunded: Payment was refunded

Transitions:
pending -> processing:
  - Trigger: Payment initiated
  - Required: Valid payment method
  - Actions: Start payment processing

processing -> completed:
  - Trigger: Payment successful
  - Required: Payment confirmed
  - Actions: Update payment status, notify both parties

processing -> failed:
  - Trigger: Payment failed
  - Required: Payment attempt failed
  - Actions: Update status, notify tenant

completed -> refunded:
  - Trigger: Refund requested
  - Required: Valid refund reason
  - Actions: Process refund, update status

21. Data Retention Policies
21.1. User Data Retention
Active User Data:
- Retention: Indefinite while account is active
- Includes: Profile information, contact details, preferences
- Deletion: Only upon explicit user request or account deletion

Inactive User Data:
- Retention: 5 years after last login
- Includes: Basic profile, contact information
- Action: Archive after 2 years, delete after 5 years

User Contract Information:
- Retention: 10 years after last contract
- Includes: ID, FIN, address, birth information
- Action: Archive after 5 years, delete after 10 years

User Financial Information:
- Retention: 7 years after last transaction
- Includes: Payment methods, transaction history
- Action: Archive after 3 years, delete after 7 years

21.2. Property Data Retention
Active Properties:
- Retention: Indefinite while active
- Includes: Property details, images, descriptions
- Action: Keep current and update as needed

Inactive Properties:
- Retention: 3 years after becoming unavailable
- Includes: Property details, images, rental history
- Action: Archive after 1 year, delete after 3 years

Property Images:
- Retention: 5 years after property becomes inactive
- Includes: All uploaded images
- Action: Archive after 2 years, delete after 5 years

21.3. Contract Data Retention
Active Contracts:
- Retention: Indefinite while active
- Includes: Contract terms, signatures, amendments
- Action: Keep current and update as needed

Completed Contracts:
- Retention: 10 years after completion
- Includes: Full contract details, signatures, amendments
- Action: Archive after 5 years, delete after 10 years

Terminated Contracts:
- Retention: 7 years after termination
- Includes: Contract details, termination reason, final state
- Action: Archive after 3 years, delete after 7 years

21.4. Application Data Retention
Approved Applications:
- Retention: 10 years after contract completion
- Includes: Application details, supporting documents
- Action: Archive after 5 years, delete after 10 years

Rejected Applications:
- Retention: 2 years after rejection
- Includes: Application details, rejection reason
- Action: Archive after 1 year, delete after 2 years

Expired Applications:
- Retention: 1 year after expiration
- Includes: Application details
- Action: Delete after 1 year

21.5. Payment Data Retention
Successful Payments:
- Retention: 7 years after payment
- Includes: Payment details, receipts, transaction records
- Action: Archive after 3 years, delete after 7 years

Failed Payments:
- Retention: 2 years after attempt
- Includes: Payment attempt details, failure reason
- Action: Delete after 2 years

Refunded Payments:
- Retention: 7 years after refund
- Includes: Original payment and refund details
- Action: Archive after 3 years, delete after 7 years

21.6. Rating and Score Data Retention
User Ratings:
- Retention: 10 years after last rating
- Includes: All ratings given and received
- Action: Archive after 5 years, delete after 10 years

Credit Scores:
- Retention: 5 years after last update
- Includes: Score history, calculation factors
- Action: Archive after 2 years, delete after 5 years

Tenant Scores:
- Retention: 10 years after last contract
- Includes: Score history, contributing factors
- Action: Archive after 5 years, delete after 10 years

21.7. Communication Data Retention
Messages:
- Retention: 2 years after last message
- Includes: All communication between parties
- Action: Archive after 1 year, delete after 2 years

Notifications:
- Retention: 1 year after creation
- Includes: System notifications, alerts
- Action: Delete after 1 year

21.8. Audit and Log Data Retention
Security Logs:
- Retention: 2 years
- Includes: Login attempts, security events
- Action: Archive after 1 year, delete after 2 years

System Logs:
- Retention: 1 year
- Includes: System operations, errors
- Action: Delete after 1 year

Audit Trails:
- Retention: 7 years
- Includes: All system changes, user actions
- Action: Archive after 3 years, delete after 7 years

22. Security Requirements
22.1. Authentication and Authorization
User Authentication:
- Password Requirements:
  * Minimum 12 characters
  * Must include uppercase, lowercase, numbers, and special characters
  * Must be changed every 90 days
  * Cannot reuse last 5 passwords
  * Must use secure password hashing (bcrypt with work factor 12)

- Multi-Factor Authentication (MFA):
  * Required for all admin users
  * Optional for landlords and tenants
  * Supports SMS 

- Session Management:
  * Session timeout after 30 minutes of inactivity
  * Maximum session duration of 24 hours
  * Single session per user
  * Secure session cookies with HttpOnly and Secure flags

Role-Based Access Control:
- Admin:
  * Full system access
  * User management
  * System configuration
  * Audit log access

- Landlord:
  * Property management
  * Application review
  * Contract management
  * Tenant rating
  * Payment management

- Tenant:
  * Property search
  * Application submission
  * Contract viewing
  * Landlord rating
  * Payment submission

22.2. Data Encryption
- At Rest:
  * All sensitive data encrypted using AES-256
  * Database encryption enabled
  * File system encryption for uploaded documents
  * Regular key rotation (every 90 days)

- In Transit:
  * TLS 1.3 required
  * HSTS enabled
  * Perfect Forward Secrecy
  * Certificate pinning

Sensitive Data Handling:
- Personal Information:
  * ID numbers encrypted
  * FIN numbers encrypted
  * Address information encrypted
  * Birth dates encrypted

- Financial Information:
  * Payment details tokenized
  * Bank account numbers encrypted
  * Transaction history encrypted
  * Credit card information not stored

- Contract Information:
  * Signatures encrypted
  * Contract terms encrypted
  * Amendments encrypted

22.3. Application Security
Input Validation:
- All user inputs sanitized
- SQL injection prevention
- XSS prevention
- CSRF protection
- File upload validation
- Content Security Policy (CSP)

API Security:
- Rate limiting
- API key authentication
- Request signing
- Input validation
- Response encryption
- Error handling without sensitive data

File Security:
- Upload restrictions:
  * Maximum file size: 10MB
  * Allowed formats: PDF, JPG, PNG
  * Virus scanning
  * Content validation

- Storage:
  * Secure cloud storage
  * Access control
  * Encryption at rest
  * Regular backups

22.4. Infrastructure Security
Network Security:
- Firewall configuration
- DDoS protection
- VPN access for admin
- Network segmentation
- Regular security scans

Server Security:
- Regular updates
- Minimal services
- Secure configuration
- Intrusion detection
- File integrity monitoring

Database Security:
- Regular backups
- Access control
- Audit logging
- Encryption
- Connection pooling

22.5. Monitoring and Logging
Security Monitoring:
- Real-time alerting
- Anomaly detection
- Failed login tracking
- Suspicious activity monitoring
- Regular security audits

Logging Requirements:
- All security events logged
- User actions logged
- System changes logged
- Access attempts logged
- Error logging

22.6. Compliance and Legal
Data Protection:
- GDPR compliance
- Data subject rights
- Privacy policy
- Data processing agreements
- Data breach notification

Legal Requirements:
- Contract validity
- Electronic signature compliance
- Payment processing compliance
- Tax reporting requirements
- Dispute resolution process

22.7. Incident Response
Security Incidents:
- Incident response plan
- Breach notification process
- Recovery procedures
- Communication plan
- Post-incident review

Backup and Recovery:
- Regular backups
- Disaster recovery plan
- Business continuity plan
- Data recovery procedures
- System restoration process

22.8. Incident Response
Secure Development:
- Code review process
- Security testing
- Dependency scanning
- Vulnerability assessment
- Penetration testing

Deployment Security:
- Secure deployment process
- Environment separation
- Configuration management
- Access control
- Change management

23. Performance Requirements
23.1. System Capacity
Concurrent Users:
- Normal Load: Support 500 concurrent users
- Peak Load: Support 1000 concurrent users
- Maximum Load: Support 5000 concurrent users

Database Capacity:
- Active Properties: 100,000
- Active Users: 200,000
- Active Contracts: 30,000
- Monthly Transactions: 500,000

Storage Requirements:
- Property Images: 1TB
- User Documents: 500GB
- Contract Storage: 100GB
- Log Storage: 200GB

23.2. API Performance
Rate Limiting:
- Standard Users: 100 requests/minute
- Landlords: 200 requests/minute
- Admins: 500 requests/minute
- API Keys: 1000 requests/minute

Response Sizes:
- JSON Responses: < 100KB
- Image Responses: < 1MB
- Document Responses: < 10MB
- Batch Responses: < 5MB

23.3. Caching Strategy
Cache Duration:
- Static Content: 1 week
- Dynamic Content: 1 hour
- User Data: 5 minutes
- Property Data: 1 hour

Cache Size:
- Memory Cache: 4GB
- Disk Cache: 20GB
- Distributed Cache: 100GB

23.4. Monitoring and Alerts
Performance Metrics:
- CPU Usage: Alert at 80%
- Memory Usage: Alert at 85%
- Disk Usage: Alert at 90%
- Network Usage: Alert at 80%

Response Time Alerts:
- Page Load: Alert at > 5 seconds
- API Response: Alert at > 3 seconds
- Database Query: Alert at > 1 second

23.5. Load Testing Requirements
Test Scenarios:
- User Registration: 1000 users/hour
- Property Search: 5000 searches/hour
- Contract Creation: 100 contracts/hour
- Payment Processing: 1000 transactions/hour

Performance Targets:
- Error Rate: < 0.1%
- Response Time: < 3 seconds (95th percentile)
- Throughput: 1000 requests/second

23.6. Resource Optimization
Image Optimization:
- Maximum Size: 1920x1080
- Compression: 80% quality
- Format: WebP preferred
- Lazy Loading: Enabled

Code Optimization:
- Minification: Enabled
- Bundling: Enabled
- Tree Shaking: Enabled
- Code Splitting: Enabled


