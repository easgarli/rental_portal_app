// TenantScore visualization and update handling
class TenantScore {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.components = {
            payment: { weight: 0.30, score: 0 },
            property: { weight: 0.25, score: 0 },
            rental: { weight: 0.20, score: 0 },
            compliance: { weight: 0.15, score: 0 },
            contract: { weight: 0.10, score: 0 }
        };
        this.totalScore = 0;
        this.history = [];
        this.initialize();
    }

    initialize() {
        this.fetchCurrentScore();
        this.setupEventListeners();
        this.setupAutoUpdate();
    }

    async fetchCurrentScore() {
        try {
            const response = await fetch('/api/tenant-score/current');
            const data = await response.json();
            this.updateScores(data);
            this.render();
        } catch (error) {
            console.error('Error fetching tenant score:', error);
        }
    }

    updateScores(data) {
        this.components.payment.score = data.payment_score;
        this.components.property.score = data.property_score;
        this.components.rental.score = data.rental_score;
        this.components.compliance.score = data.compliance_score;
        this.components.contract.score = data.contract_score;
        this.totalScore = data.total_score;
        this.history = data.history || [];
    }

    render() {
        this.renderTotalScore();
        this.renderComponentScores();
        this.renderHistoryChart();
        this.updateScoreInterpretation();
    }

    renderTotalScore() {
        const totalScoreElement = document.getElementById('total-score');
        if (totalScoreElement) {
            totalScoreElement.textContent = this.totalScore.toFixed(1);
            totalScoreElement.className = `display-4 fw-bold ${this.getScoreColorClass(this.totalScore)}`;
        }
    }

    renderComponentScores() {
        Object.entries(this.components).forEach(([key, component]) => {
            const element = document.getElementById(`${key}-score`);
            if (element) {
                element.textContent = component.score.toFixed(1);
                element.className = `badge ${this.getScoreColorClass(component.score)}`;
            }

            const progressBar = document.getElementById(`${key}-progress`);
            if (progressBar) {
                progressBar.style.width = `${component.score}%`;
                progressBar.className = `progress-bar ${this.getScoreColorClass(component.score)}`;
            }
        });
    }

    renderHistoryChart() {
        if (this.history.length > 0 && typeof Chart !== 'undefined') {
            const ctx = document.getElementById('scoreHistoryChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: this.history.map(h => new Date(h.date).toLocaleDateString()),
                        datasets: [{
                            label: 'TenantScore',
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
                                max: 100
                            }
                        }
                    }
                });
            }
        }
    }

    updateScoreInterpretation() {
        const interpretationElement = document.getElementById('score-interpretation');
        if (interpretationElement) {
            const interpretation = this.getScoreInterpretation(this.totalScore);
            interpretationElement.textContent = interpretation.text;
            interpretationElement.className = `alert ${interpretation.class}`;
        }
    }

    getScoreColorClass(score) {
        if (score >= 90) return 'text-success';
        if (score >= 75) return 'text-primary';
        if (score >= 50) return 'text-warning';
        return 'text-danger';
    }

    getScoreInterpretation(score) {
        if (score >= 90) {
            return {
                text: 'Çox etibarlı icarədar (Very Reliable Tenant)',
                class: 'alert-success'
            };
        }
        if (score >= 75) {
            return {
                text: 'Yaxşı icarədar (Good Tenant)',
                class: 'alert-primary'
            };
        }
        if (score >= 50) {
            return {
                text: 'Orta riskli icarədar (Medium Risk Tenant)',
                class: 'alert-warning'
            };
        }
        return {
            text: 'Yüksək riskli icarədar (High Risk Tenant)',
            class: 'alert-danger'
        };
    }

    setupEventListeners() {
        // Listen for score update events
        document.addEventListener('paymentUpdated', (e) => this.handlePaymentUpdate(e.detail));
        document.addEventListener('complaintResolved', (e) => this.handleComplaintUpdate(e.detail));
        document.addEventListener('contractViolation', (e) => this.handleViolationUpdate(e.detail));
    }

    setupAutoUpdate() {
        // Update scores every 5 minutes
        setInterval(() => this.fetchCurrentScore(), 300000);
    }

    handlePaymentUpdate(paymentData) {
        this.components.payment.score = this.calculatePaymentScore(paymentData);
        this.updateTotalScore();
        this.render();
    }

    handleComplaintUpdate(complaintData) {
        this.components.compliance.score = this.calculateComplianceScore(complaintData);
        this.updateTotalScore();
        this.render();
    }

    handleViolationUpdate(violationData) {
        this.components.contract.score = this.calculateContractScore(violationData);
        this.updateTotalScore();
        this.render();
    }

    calculatePaymentScore(paymentData) {
        // Implementation based on payment history
        let baseScore = 100;
        const deductions = paymentData.latePayments * 10;
        const bonuses = paymentData.onTimePayments * 5;
        return Math.max(0, Math.min(100, baseScore - deductions + bonuses));
    }

    calculateComplianceScore(complaintData) {
        // Implementation based on complaint history
        let baseScore = 100;
        const deductions = complaintData.seriousComplaints * 25;
        const bonuses = complaintData.resolvedComplaints * 10;
        return Math.max(0, Math.min(100, baseScore - deductions + bonuses));
    }

    calculateContractScore(violationData) {
        // Implementation based on contract violations
        let baseScore = 100;
        const deductions = violationData.majorViolations * 30;
        const bonuses = violationData.earlyRenewals * 10;
        return Math.max(0, Math.min(100, baseScore - deductions + bonuses));
    }

    updateTotalScore() {
        this.totalScore = Object.entries(this.components).reduce((total, [_, component]) => {
            return total + (component.score * component.weight);
        }, 0);
    }
}

// Initialize TenantScore when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const tenantScore = new TenantScore('tenant-score-container');
}); 