// CreditScore visualization and update handling
class CreditScore {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.score = 0;
        this.history = [];
        this.factors = {
            age: { score: 0, weight: 0.05 },
            gender: { score: 0, weight: 0.02 },
            marital_status: { score: 0, weight: 0.03 },
            dependents: { score: 0, weight: 0.05 },
            education: { score: 0, weight: 0.05 },
            work_sector: { score: 0, weight: 0.24 },
            work_experience: { score: 0, weight: 0.08 },
            credit_history: { score: 0, weight: 0.28 },
            income_ratio: { score: 0, weight: 0.20 }
        };
        this.initialize();
    }

    initialize() {
        this.fetchCurrentScore();
        this.setupEventListeners();
        this.setupAutoUpdate();
    }

    async fetchCurrentScore() {
        try {
            const response = await fetch('/api/credit-score/current');
            const data = await response.json();
            this.updateScores(data);
            this.render();
        } catch (error) {
            console.error('Error fetching credit score:', error);
        }
    }

    updateScores(data) {
        this.score = data.score;
        this.history = data.history || [];
        Object.entries(data.factors).forEach(([key, value]) => {
            if (this.factors[key]) {
                this.factors[key].score = value;
            }
        });
    }

    render() {
        this.renderTotalScore();
        this.renderFactorScores();
        this.renderHistoryChart();
        this.updateScoreInterpretation();
    }

    renderTotalScore() {
        const totalScoreElement = document.getElementById('credit-score');
        if (totalScoreElement) {
            totalScoreElement.textContent = this.score.toFixed(0);
            totalScoreElement.className = `display-4 fw-bold ${this.getScoreColorClass(this.score)}`;
        }
    }

    renderFactorScores() {
        Object.entries(this.factors).forEach(([key, factor]) => {
            const element = document.getElementById(`${key}-score`);
            if (element) {
                element.textContent = factor.score.toFixed(0);
                element.className = `badge ${this.getScoreColorClass(factor.score)}`;
            }

            const progressBar = document.getElementById(`${key}-progress`);
            if (progressBar) {
                progressBar.style.width = `${(factor.score / this.getMaxScore(key)) * 100}%`;
                progressBar.className = `progress-bar ${this.getScoreColorClass(factor.score)}`;
            }
        });
    }

    renderHistoryChart() {
        if (this.history.length > 0 && typeof Chart !== 'undefined') {
            const ctx = document.getElementById('creditHistoryChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: this.history.map(h => new Date(h.date).toLocaleDateString()),
                        datasets: [{
                            label: 'Kredit Skoru',
                            data: this.history.map(h => h.score),
                            borderColor: '#0d6efd',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 1000
                            }
                        }
                    }
                });
            }
        }
    }

    updateScoreInterpretation() {
        const interpretationElement = document.getElementById('credit-score-interpretation');
        if (interpretationElement) {
            const interpretation = this.getScoreInterpretation(this.score);
            interpretationElement.textContent = interpretation.text;
            interpretationElement.className = `alert ${interpretation.class}`;
        }
    }

    getScoreColorClass(score) {
        if (score >= 850) return 'text-success';
        if (score >= 700) return 'text-primary';
        if (score >= 600) return 'text-warning';
        return 'text-danger';
    }

    getScoreInterpretation(score) {
        if (score >= 850) {
            return {
                text: 'Əla kredit skoru (Excellent Credit Score)',
                class: 'alert-success'
            };
        }
        if (score >= 700) {
            return {
                text: 'Yaxşı kredit skoru (Good Credit Score)',
                class: 'alert-primary'
            };
        }
        if (score >= 600) {
            return {
                text: 'Orta kredit skoru (Average Credit Score)',
                class: 'alert-warning'
            };
        }
        return {
            text: 'Riskli kredit skoru (Risky Credit Score)',
            class: 'alert-danger'
        };
    }

    getMaxScore(factor) {
        const maxScores = {
            age: 50,
            gender: 20,
            marital_status: 30,
            dependents: 50,
            education: 50,
            work_sector: 240,
            work_experience: 80,
            credit_history: 280,
            income_ratio: 200
        };
        return maxScores[factor] || 100;
    }

    setupEventListeners() {
        // Listen for score update events
        document.addEventListener('questionnaireUpdated', (e) => this.handleQuestionnaireUpdate(e.detail));
        document.addEventListener('creditHistoryUpdated', (e) => this.handleCreditHistoryUpdate(e.detail));
        document.addEventListener('incomeUpdated', (e) => this.handleIncomeUpdate(e.detail));
    }

    setupAutoUpdate() {
        // Update scores every 5 minutes
        setInterval(() => this.fetchCurrentScore(), 300000);
    }

    handleQuestionnaireUpdate(data) {
        this.updateFactorsFromQuestionnaire(data);
        this.calculateTotalScore();
        this.render();
    }

    handleCreditHistoryUpdate(data) {
        this.factors.credit_history.score = this.calculateCreditHistoryScore(data);
        this.calculateTotalScore();
        this.render();
    }

    handleIncomeUpdate(data) {
        this.factors.income_ratio.score = this.calculateIncomeRatioScore(data);
        this.calculateTotalScore();
        this.render();
    }

    updateFactorsFromQuestionnaire(data) {
        // Update scores based on questionnaire responses
        this.factors.age.score = this.calculateAgeScore(data.age);
        this.factors.gender.score = this.calculateGenderScore(data.gender);
        this.factors.marital_status.score = this.calculateMaritalStatusScore(data.marital_status);
        this.factors.dependents.score = this.calculateDependentsScore(data.dependents);
        this.factors.education.score = this.calculateEducationScore(data.education);
        this.factors.work_sector.score = this.calculateWorkSectorScore(data.work_sector);
        this.factors.work_experience.score = this.calculateWorkExperienceScore(data.work_experience);
    }

    calculateAgeScore(age) {
        if (age >= 27 && age < 50) return 50;
        if (age >= 20 && age < 27) return 30;
        if (age >= 50 && age < 60) return 40;
        if (age >= 60 && age < 65) return 30;
        if (age >= 65 && age < 68) return 20;
        return 0;
    }

    calculateGenderScore(gender) {
        return gender === 'Qadın' ? 20 : 15;
    }

    calculateMaritalStatusScore(status) {
        return status === 'Evli' ? 30 : 20;
    }

    calculateDependentsScore(dependents) {
        return dependents <= 3 ? 50 : 35;
    }

    calculateEducationScore(education) {
        return education === 'Ali' ? 50 : 30;
    }

    calculateWorkSectorScore(sector) {
        const sectorGroups = {
            'Ən az riskli qrup': 240,
            'Az riskli qrup': 200,
            'Orta riskli qrup': 160,
            'Nisbətən yüksək riskli qrup': 120,
            'Rəsmi gəliri olmayanlar': 80
        };
        return sectorGroups[sector] || 0;
    }

    calculateWorkExperienceScore(experience) {
        if (experience > 12) return 80;
        if (experience > 6) return 70;
        if (experience > 3) return 60;
        return 0;
    }

    calculateCreditHistoryScore(history) {
        if (history.last_6_months_late_days === 0) return 280;
        if (history.last_6_months_late_days <= 30) return 280;
        if (history.last_6_months_late_days <= 90) return 200;
        return 0;
    }

    calculateIncomeRatioScore(data) {
        const ratio = data.planned_rent / (data.monthly_income - data.monthly_expenses);
        if (ratio > 0.9) return 0;
        if (ratio >= 0.7) return 100;
        if (ratio >= 0.5) return 150;
        return 200;
    }

    calculateTotalScore() {
        this.score = Object.entries(this.factors).reduce((total, [_, factor]) => {
            return total + (factor.score * factor.weight);
        }, 0);
    }
}

// Initialize CreditScore when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const creditScore = new CreditScore('credit-score-container');
}); 