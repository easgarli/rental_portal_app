from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, TenantQuestionnaire

questionnaire_bp = Blueprint('questionnaire', __name__)

# Scoring rules from your tez_score.py
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

@questionnaire_bp.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    if current_user.role != 'tenant':
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        data = request.form
        credit_score = calculate_credit_score(data)
        
        questionnaire = TenantQuestionnaire(
            tenant_id=current_user.id,
            age_group=data['age_group'],
            gender=data['gender'],
            marital_status=data['marital_status'],
            dependents=data['dependents'],
            education=data['education'],
            work_sector=data['work_sector'],
            work_experience=data['work_experience'],
            credit_history=data['credit_history'],
            monthly_income=float(data['monthly_income']),
            monthly_expenses=float(data['monthly_expenses']),
            planned_rent=float(data['planned_rent']),
            credit_score=credit_score
        )
        
        print(f"Calculated credit score: {credit_score}")
        
        db.session.add(questionnaire)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
        
    return render_template('questionnaire.html', scoring_rules=SCORING_RULES, sector_risk_mapping=sector_risk_mapping) 