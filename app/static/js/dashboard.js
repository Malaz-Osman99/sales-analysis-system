// dashboard.js - الرسوم البيانية والتفاعلات

// تهيئة المكتبات
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Dashboard جاهز');
    
    // تهيئة جميع الرسوم البيانية
    initAllCharts();
    
    // تهيئة علامات التبويب
    initTabs();
    
    // تحديث الوقت
    updateDateTime();
});

// تحديث التاريخ والوقت
function updateDateTime() {
    const now = new Date();
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    const dateStr = now.toLocaleDateString('ar-SA', options);
    const timeElements = document.querySelectorAll('.current-time');
    timeElements.forEach(el => {
        if (el) el.textContent = dateStr;
    });
}

// تهيئة جميع الرسوم البيانية
function initAllCharts() {
    // الرسم البياني للمبيعات الشهرية
    if (document.getElementById('monthlySalesChart')) {
        createMonthlySalesChart();
    }
    
    // الرسم البياني لأفضل المنتجات
    if (document.getElementById('topProductsChart')) {
        createTopProductsChart();
    }
    
    // الرسم البياني للمبيعات حسب الفئة
    if (document.getElementById('categoryChart')) {
        createCategoryChart();
    }
    
    // الرسم البياني لأوقات الذروة
    if (document.getElementById('peakHoursChart')) {
        createPeakHoursChart();
    }
    
    // الرسم البياني لأيام الأسبوع
    if (document.getElementById('weekdayChart')) {
        createWeekdayChart();
    }
    
    // الرسم البياني لاتجاه المبيعات
    if (document.getElementById('salesTrendChart')) {
        createSalesTrendChart();
    }
}

// الرسم البياني للمبيعات الشهرية
function createMonthlySalesChart() {
    const ctx = document.getElementById('monthlySalesChart').getContext('2d');
    
    // الحصول على البيانات من عنصر مخفي
    const monthlyData = JSON.parse(document.getElementById('monthlyData').value || '[]');
    
    const labels = monthlyData.map(item => item.label);
    const sales = monthlyData.map(item => item.total_sales);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'المبيعات الشهرية',
                data: sales,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: '#764ba2',
                pointBorderColor: 'white',
                pointRadius: 5,
                pointHoverRadius: 8,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#333',
                    titleColor: 'white',
                    bodyColor: '#ddd',
                    callbacks: {
                        label: function(context) {
                            return `المبيعات: ${context.raw.toLocaleString()} ريال`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString() + ' ريال';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// الرسم البياني لأفضل المنتجات
function createTopProductsChart() {
    const ctx = document.getElementById('topProductsChart').getContext('2d');
    
    const productsData = JSON.parse(document.getElementById('topProductsData').value || '[]');
    
    const labels = productsData.map(item => item.product_name);
    const sales = productsData.map(item => item.total_sales);
    const quantities = productsData.map(item => item.total_quantity);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'المبيعات (ريال)',
                    data: sales,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'الكمية المباعة',
                    data: quantities,
                    backgroundColor: 'rgba(118, 75, 162, 0.8)',
                    borderColor: '#764ba2',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'المبيعات (ريال)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'الكمية'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// الرسم البياني للمبيعات حسب الفئة
function createCategoryChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    const categoryData = JSON.parse(document.getElementById('categoryData').value || '[]');
    
    const labels = categoryData.map(item => item.category);
    const sales = categoryData.map(item => item.total_sales);
    const percentages = categoryData.map(item => item.percentage);
    
    // ألوان عشوائية جميلة
    const colors = [
        '#667eea', '#764ba2', '#28a745', '#dc3545', 
        '#ffc107', '#17a2b8', '#e83e8c', '#fd7e14',
        '#20c997', '#6f42c1', '#007bff', '#6610f2'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: sales,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const percentage = percentages[context.dataIndex];
                            return `${context.label}: ${value.toLocaleString()} ريال (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// الرسم البياني لأوقات الذروة
function createPeakHoursChart() {
    const ctx = document.getElementById('peakHoursChart').getContext('2d');
    
    const hoursData = JSON.parse(document.getElementById('peakHoursData').value || '[]');
    
    const labels = hoursData.map(item => item.label);
    const sales = hoursData.map(item => item.total_sales);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'المبيعات',
                data: sales,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#28a745',
                pointRadius: 4,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// الرسم البياني لأيام الأسبوع
function createWeekdayChart() {
    const ctx = document.getElementById('weekdayChart').getContext('2d');
    
    const weekdayData = JSON.parse(document.getElementById('weekdayData').value || '[]');
    
    const labels = weekdayData.map(item => item.weekday_ar);
    const sales = weekdayData.map(item => item.total_sales);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'المبيعات',
                data: sales,
                backgroundColor: 'rgba(255, 193, 7, 0.8)',
                borderColor: '#ffc107',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                }
            }
        }
    });
}

// الرسم البياني لاتجاه المبيعات
function createSalesTrendChart() {
    const ctx = document.getElementById('salesTrendChart').getContext('2d');
    
    const dailyData = JSON.parse(document.getElementById('dailyData').value || '[]');
    
    const labels = dailyData.map(item => item.date);
    const sales = dailyData.map(item => item.total_price);
    const transactions = dailyData.map(item => item.sale_id);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'المبيعات اليومية',
                    data: sales,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.05)',
                    borderWidth: 2,
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'عدد العمليات',
                    data: transactions,
                    borderColor: '#17a2b8',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    yAxisID: 'y1',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'المبيعات (ريال)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'عدد العمليات'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// تهيئة علامات التبويب
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // إزالة الفئة النشطة من جميع الأزرار
            tabBtns.forEach(b => b.classList.remove('active'));
            
            // إضافة الفئة النشطة للزر الحالي
            this.classList.add('active');
            
            // إظهار المحتوى المناسب
            const tables = document.querySelectorAll('.products-table');
            tables.forEach(table => table.style.display = 'none');
            
            const activeTable = document.getElementById(`products-${tabId}`);
            if (activeTable) {
                activeTable.style.display = 'table';
            }
        });
    });
}

// تصدير التقرير
function exportReport() {
    const reportType = document.getElementById('exportType').value;
    
    // هنا يمكن إضافة منطق تصدير التقرير
    alert(`جاري تصدير التقرير بصيغة ${reportType}...`);
}

// تحديث البيانات
function refreshData() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.innerHTML = 'جاري التحديث...';
    refreshBtn.disabled = true;
    
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// تغيير الفترة الزمنية
function changePeriod(period) {
    const periodBtns = document.querySelectorAll('.period-btn');
    periodBtns.forEach(btn => btn.classList.remove('active'));
    
    const activeBtn = document.querySelector(`[data-period="${period}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    // هنا يمكن إضافة منطق تغيير الفترة
    showLoading();
    
    setTimeout(() => {
        hideLoading();
        // تحديث الرسوم البيانية حسب الفترة
    }, 500);
}

// إظهار التحميل
function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'block';
}

// إخفاء التحميل
function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.style.display = 'none';
}

// تنسيق الأرقام
function formatNumber(num) {
    return num?.toLocaleString() || '0';
}

// تنسيق العملة
function formatCurrency(num) {
    return num?.toLocaleString() + ' ريال' || '0 ريال';
}

// تحديث تلقائي كل 5 دقائق
setInterval(() => {
    console.log('تحديث تلقائي...');
    // يمكن إضافة تحديث خفيف هنا
}, 300000);