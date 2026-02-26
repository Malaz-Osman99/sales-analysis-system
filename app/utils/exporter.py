import pandas as pd
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import arabic_reshaper
from bidi.algorithm import get_display
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import os
import tempfile

class ReportExporter:
    """فئة تصدير التقارير بصيغ متعددة"""
    
    def __init__(self, user_name="مستخدم"):
        self.user_name = user_name
        self.styles = getSampleStyleSheet()
        self.setup_arabic_support()
    
    def setup_arabic_support(self):
        """إعداد دعم اللغة العربية في PDF"""
        try:
            # محاولة استخدام خط يدعم العربية
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # البحث عن خطوط النظام التي تدعم العربية
            font_paths = [
                '/usr/share/fonts/truetype/arial/arial.ttf',  # Linux
                '/System/Library/Fonts/Arial.ttf',  # Mac
                'C:/Windows/Fonts/Arial.ttf',  # Windows
            ]
            
            font_found = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Arabic', font_path))
                    font_found = True
                    break
            
            if not font_found:
                # استخدام الخط الافتراضي
                pdfmetrics.registerFont(TTFont('Arabic', 'Helvetica'))
        except:
            pass
    
    def reshape_arabic_text(self, text):
        """إعادة تشكيل النص العربي للعرض الصحيح"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            return text
    
    def export_to_excel(self, data, report_type='full'):
        """
        تصدير التقرير إلى Excel
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # تنسيقات Excel
            header_format = workbook.add_format({
                'bold': True,
                'fg_color': '#667eea',
                'font_color': 'white',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': '#,##0.00 [$ر.س]',
                'align': 'right'
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            })
            
            # 1. صفحة مؤشرات الأداء
            if 'kpis' in data:
                kpis_df = pd.DataFrame([
                    {'المؤشر': 'إجمالي المبيعات', 'القيمة': data['kpis'].get('total_sales', 0)},
                    {'المؤشر': 'عدد العمليات', 'القيمة': data['kpis'].get('total_transactions', 0)},
                    {'المؤشر': 'متوسط قيمة العملية', 'القيمة': data['kpis'].get('avg_transaction_value', 0)},
                    {'المؤشر': 'إجمالي الكميات', 'القيمة': data['kpis'].get('total_quantity', 0)},
                ])
                kpis_df.to_excel(writer, sheet_name='مؤشرات الأداء', index=False)
                
                # تنسيق صفحة KPIs
                worksheet = writer.sheets['مؤشرات الأداء']
                for col_num, value in enumerate(kpis_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 25)
            
            # 2. صفحة أفضل المنتجات
            if 'top_products' in data and data['top_products']:
                top_df = pd.DataFrame(data['top_products'])
                top_df.columns = ['المنتج', 'الفئة', 'إجمالي المبيعات', 'الكمية', 'عدد العمليات']
                top_df.to_excel(writer, sheet_name='أفضل المنتجات', index=False)
                
                worksheet = writer.sheets['أفضل المنتجات']
                for col_num, value in enumerate(top_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # تنسيق الأعمدة الرقمية
                worksheet.set_column('D:D', 20, currency_format)
                worksheet.set_column('E:E', 15, number_format)
            
            # 3. صفحة المبيعات الشهرية
            if 'monthly_sales' in data and data['monthly_sales']:
                monthly_df = pd.DataFrame(data['monthly_sales'])
                if 'label' in monthly_df.columns and 'total_sales' in monthly_df.columns:
                    monthly_df = monthly_df[['label', 'total_sales', 'quantity']]
                    monthly_df.columns = ['الشهر', 'المبيعات', 'الكمية']
                    monthly_df.to_excel(writer, sheet_name='المبيعات الشهرية', index=False)
                    
                    worksheet = writer.sheets['المبيعات الشهرية']
                    for col_num, value in enumerate(monthly_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    worksheet.set_column('B:B', 20, currency_format)
            
            # 4. صفحة التنبؤات
            if 'predictions' in data and data['predictions']:
                pred_df = pd.DataFrame(data['predictions'])
                if pred_df is not None and not pred_df.empty:
                    # اختيار الأعمدة المناسبة
                    cols = []
                    if 'date' in pred_df.columns:
                        cols.append('date')
                    if 'predicted_sales' in pred_df.columns:
                        cols.append('predicted_sales')
                    if 'predicted_profit' in pred_df.columns:
                        cols.append('predicted_profit')
                    
                    if cols:
                        pred_df = pred_df[cols]
                        pred_df.columns = ['التاريخ', 'المبيعات المتوقعة', 'الربح المتوقع']
                        pred_df.to_excel(writer, sheet_name='التنبؤات', index=False)
                        
                        worksheet = writer.sheets['التنبؤات']
                        for col_num, value in enumerate(pred_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                        
                        worksheet.set_column('B:C', 20, currency_format)
            
            # 5. صفحة ملخص
            summary_data = {
                'تاريخ التقرير': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'اسم المستخدم': self.user_name,
                'إجمالي المبيعات': data['kpis'].get('total_sales', 0) if 'kpis' in data else 0,
                'إجمالي العمليات': data['kpis'].get('total_transactions', 0) if 'kpis' in data else 0,
            }
            
            summary_df = pd.DataFrame([
                {'العنصر': k, 'القيمة': v} for k, v in summary_data.items()
            ])
            summary_df.to_excel(writer, sheet_name='ملخص', index=False)
            
            worksheet = writer.sheets['ملخص']
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 30)
        
        output.seek(0)
        return output.getvalue()
    
    def export_to_pdf(self, data, report_type='full'):
        """
        تصدير التقرير إلى PDF
        """
        buffer = io.BytesIO()
        
        # إعداد المستند
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # قائمة العناصر
        elements = []
        
        # عنوان التقرير
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            alignment=1,  # مركز
            spaceAfter=30,
        )
        
        title = Paragraph(self.reshape_arabic_text("تقرير تحليل المبيعات"), title_style)
        elements.append(title)
        
        # معلومات التقرير
        info_style = ParagraphStyle(
            'Info',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            alignment=1,
            spaceAfter=20,
        )
        
        info_text = f"""
        المستخدم: {self.reshape_arabic_text(self.user_name)}<br/>
        التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # مؤشرات الأداء
        if 'kpis' in data:
            elements.append(Paragraph(
                self.reshape_arabic_text("📊 مؤشرات الأداء الرئيسية"),
                self.styles['Heading2']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            kpis = data['kpis']
            kpi_data = [
                [self.reshape_arabic_text("المؤشر"), self.reshape_arabic_text("القيمة")],
                [self.reshape_arabic_text("إجمالي المبيعات"), f"{kpis.get('total_sales', 0):,.2f} ريال"],
                [self.reshape_arabic_text("عدد العمليات"), f"{kpis.get('total_transactions', 0):,}"],
                [self.reshape_arabic_text("متوسط العملية"), f"{kpis.get('avg_transaction_value', 0):,.2f} ريال"],
                [self.reshape_arabic_text("إجمالي الكميات"), f"{kpis.get('total_quantity', 0):,}"],
            ]
            
            kpi_table = Table(kpi_data, colWidths=[200, 200])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(kpi_table)
            elements.append(Spacer(1, 0.5*inch))
        
        # أفضل المنتجات
        if 'top_products' in data and data['top_products']:
            elements.append(Paragraph(
                self.reshape_arabic_text("🏆 أفضل 5 منتجات"),
                self.styles['Heading2']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            top_data = [[
                self.reshape_arabic_text("المنتج"),
                self.reshape_arabic_text("الفئة"),
                self.reshape_arabic_text("المبيعات"),
                self.reshape_arabic_text("الكمية")
            ]]
            
            for p in data['top_products'][:5]:
                top_data.append([
                    self.reshape_arabic_text(p.get('product_name', '')),
                    self.reshape_arabic_text(p.get('category', '')),
                    f"{p.get('total_sales', 0):,.2f}",
                    f"{p.get('total_quantity', 0):,}"
                ])
            
            top_table = Table(top_data, colWidths=[120, 80, 100, 70])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            elements.append(top_table)
            elements.append(Spacer(1, 0.5*inch))
        
        # التنبؤات
        if 'predictions' in data and data['predictions']:
            elements.append(Paragraph(
                self.reshape_arabic_text("🔮 توقعات المبيعات (الأيام القادمة)"),
                self.styles['Heading2']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            pred_data = [[
                self.reshape_arabic_text("التاريخ"),
                self.reshape_arabic_text("المبيعات المتوقعة"),
                self.reshape_arabic_text("الربح المتوقع")
            ]]
            
            for p in data['predictions'][:10]:  # أول 10 أيام
                pred_data.append([
                    p.get('date', ''),
                    f"{p.get('predicted_sales', 0):,.2f} ريال",
                    f"{p.get('predicted_profit', 0):,.2f} ريال"
                ])
            
            pred_table = Table(pred_data, colWidths=[100, 120, 120])
            pred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(pred_table)
        
        # إنشاء PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_to_csv(self, data, data_type='sales'):
        """
        تصدير البيانات إلى CSV
        """
        output = io.BytesIO()
        
        if data_type == 'sales' and 'monthly_sales' in data:
            df = pd.DataFrame(data['monthly_sales'])
            df.to_csv(output, index=False, encoding='utf-8-sig')
        elif data_type == 'products' and 'top_products' in data:
            df = pd.DataFrame(data['top_products'])
            df.to_csv(output, index=False, encoding='utf-8-sig')
        elif data_type == 'predictions' and 'predictions' in data:
            df = pd.DataFrame(data['predictions'])
            df.to_csv(output, index=False, encoding='utf-8-sig')
        else:
            # تصدير كل البيانات
            df = pd.DataFrame()
            if 'kpis' in data:
                df['KPIs'] = pd.Series(data['kpis'])
            df.to_csv(output, index=False, encoding='utf-8-sig')
        
        output.seek(0)
        return output.getvalue()
    
    def create_chart_image(self, data, chart_type='monthly'):
        """
        إنشاء صورة رسم بياني لإضافتها للـ PDF
        """
        plt.figure(figsize=(8, 4))
        
        if chart_type == 'monthly' and 'monthly_sales' in data:
            df = pd.DataFrame(data['monthly_sales'])
            if 'label' in df.columns and 'total_sales' in df.columns:
                plt.plot(df['label'], df['total_sales'], marker='o', color='#667eea', linewidth=2)
                plt.title('المبيعات الشهرية', fontsize=14, pad=20)
                plt.xlabel('الشهر', fontsize=12)
                plt.ylabel('المبيعات (ريال)', fontsize=12)
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
        
        elif chart_type == 'top_products' and 'top_products' in data:
            df = pd.DataFrame(data['top_products'][:5])
            if 'product_name' in df.columns and 'total_sales' in df.columns:
                plt.bar(df['product_name'], df['total_sales'], color='#28a745')
                plt.title('أفضل 5 منتجات', fontsize=14, pad=20)
                plt.xlabel('المنتج', fontsize=12)
                plt.ylabel('المبيعات (ريال)', fontsize=12)
                plt.xticks(rotation=45)
        
        # حفظ الصورة
        img_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        img_buffer.seek(0)
        
        return img_buffer.getvalue()