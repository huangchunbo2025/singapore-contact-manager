"""
新加坡活动联系人管理系统
使用 Flask + SQLite 数据库
"""

import os
import csv
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

"""

# 检测是否在生产环境（Render/Heroku 等会设置 PORT 环境变量）
IS_PRODUCTION = os.environ.get('PORT') is not None

if IS_PRODUCTION:
    # 生产环境：使用持久化存储 /data 目录
    app.config['UPLOAD_FOLDER'] = '/data/uploads'
    app.config['DATABASE'] = '/data/contacts.db'
    print("🌐 生产环境模式：数据库位置 /data/contacts.db")
else:
    # 本地开发环境
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DATABASE'] = 'contacts.db'
    print("💻 开发环境模式：数据库位置 contacts.db")

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库初始化
"""

# Detect production mode when PORT is provided by the hosting platform.
IS_PRODUCTION = os.environ.get('PORT') is not None

if IS_PRODUCTION:
    app.config['UPLOAD_FOLDER'] = '/data/uploads'
    app.config['DATABASE'] = '/data/contacts.db'
    print("Production mode: using /data/contacts.db")
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DATABASE'] = 'contacts.db'
    print("Development mode: using contacts.db")

# Ensure the upload directory exists.
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    try:
        print(f"📊 初始化数据库：{app.config['DATABASE']}")
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        raise

    # 联系人表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            company TEXT,
            email TEXT UNIQUE,
            website TEXT,
            linkedin TEXT,
            industry TEXT,
            employees TEXT,
            priority TEXT,
            background TEXT,
            approach TEXT,
            ms_products TEXT,
            marketing_tech TEXT,
            is_global TEXT,
            global_reason TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 检查是否需要添加新列（兼容旧版本）
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_deleted' not in columns:
        cursor.execute('ALTER TABLE contacts ADD COLUMN is_deleted INTEGER DEFAULT 0')
        print("✓ 已添加 is_deleted 列")
    if 'phone' not in columns:
        cursor.execute('ALTER TABLE contacts ADD COLUMN phone TEXT')
        print("✓ 已添加 phone 列")

    # 联系状态表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            linkedin_contacted INTEGER DEFAULT 0,
            whatsapp_contacted INTEGER DEFAULT 0,
            email_contacted INTEGER DEFAULT 0,
            phone_contacted INTEGER DEFAULT 0,
            responded INTEGER DEFAULT 0,
            notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES contacts(email)
        )
    ''')

    cursor.execute("PRAGMA table_info(contact_status)")
    status_columns = [column[1] for column in cursor.fetchall()]
    if 'responded' not in status_columns:
        cursor.execute('ALTER TABLE contact_status ADD COLUMN responded INTEGER DEFAULT 0')
        print("Added responded column to contact_status")

    conn.commit()

    # 检查数据库是否为空，如果为空则自动导入初始数据
    cursor.execute('SELECT COUNT(*) FROM contacts WHERE is_deleted = 0')
    count = cursor.fetchone()[0]

    if count == 0:
        print("📦 数据库为空，正在导入初始数据...")
        # 检查 data.csv 文件是否存在
        data_file = os.path.join(os.path.dirname(__file__), 'data.csv')
        if os.path.exists(data_file):
            try:
                # 关闭当前连接，使用 import_csv_data 函数
                conn.close()
                import_csv_data(data_file)
                print(f"✅ 成功导入初始数据（{data_file}）")
            except Exception as e:
                print(f"⚠️ 导入初始数据失败：{e}")
        else:
            print(f"⚠️ 初始数据文件不存在：{data_file}")
            conn.close()
    else:
        print(f"ℹ️ 数据库已有 {count} 条记录，跳过初始导入")
        conn.close()

    print("✅ 数据库初始化完成")

# 导入CSV数据
def import_csv_data(filepath):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    # 清空现有数据
    cursor.execute('DELETE FROM contacts')
    cursor.execute('DELETE FROM contact_status')

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # 检测CSV格式（Apollo格式 vs 旧格式）
                is_apollo_format = 'First Name' in row or 'Email' in row

                if is_apollo_format:
                    # Apollo CSV 格式
                    first_name = row.get('First Name', '')
                    last_name = row.get('Last Name', '')
                    name = f"{first_name} {last_name}".strip()
                    title = row.get('Title', '')
                    company = row.get('Company Name', '')
                    email = row.get('Email', '')
                    website = row.get('Website', '')
                    linkedin = row.get('Person Linkedin Url', '')
                    industry = row.get('Industry', '')
                    employees = row.get('# Employees', '')
                    # 获取手机号：优先 Mobile Phone > Work Direct Phone > Corporate Phone
                    phone = row.get('Mobile Phone', '') or row.get('Work Direct Phone', '') or row.get('Corporate Phone', '')
                    # Apollo格式没有这些字段
                    priority = ''
                    background = row.get('Keywords', '')[:500] if row.get('Keywords') else ''
                    approach = ''
                    ms_products = ''
                    marketing_tech = row.get('Technologies', '')[:500] if row.get('Technologies') else ''
                    is_global = ''
                    global_reason = ''
                else:
                    # 旧的中文 CSV 格式
                    name = row.get('姓名', '')
                    title = row.get('职位', '')
                    company = row.get('公司', '')
                    email = row.get('邮箱', '')
                    website = row.get('Website', '')
                    linkedin = row.get('LinkedIn', '')
                    industry = row.get('Industry', '')
                    employees = row.get('Employees', '')
                    phone = row.get('手机', '') or row.get('电话', '')
                    priority = row.get('优先级', '')
                    background = row.get('背景说明', '')
                    approach = row.get('邀约切入点', '')
                    ms_products = row.get('微软产品', '')
                    marketing_tech = row.get('营销技术栈产品', '')
                    is_global = row.get('全球性企业标记', '')
                    global_reason = row.get('全球化判定依据', '')

                cursor.execute('''
                    INSERT OR REPLACE INTO contacts
                    (name, title, company, email, website, linkedin, industry, employees,
                     priority, background, approach, ms_products, marketing_tech, is_global, global_reason, phone, is_deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (
                    name, title, company, email, website, linkedin, industry, employees,
                    priority, background, approach, ms_products, marketing_tech, is_global, global_reason, phone
                ))

                # 初始化联系状态
                if email:
                    cursor.execute('''
                        INSERT OR IGNORE INTO contact_status (email)
                        VALUES (?)
                    ''', (email,))

            except Exception as e:
                print(f"Error importing row: {e}")
                continue

    conn.commit()
    conn.close()
    return True

# 获取所有联系人（排除已删除）
def get_all_contacts():
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT c.*,
                   COALESCE(s.linkedin_contacted, 0) as linkedin_contacted,
                   COALESCE(s.whatsapp_contacted, 0) as whatsapp_contacted,
                   COALESCE(s.email_contacted, 0) as email_contacted,
                   COALESCE(s.phone_contacted, 0) as phone_contacted,
                   COALESCE(s.responded, 0) as responded,
                   COALESCE(s.notes, '') as notes,
                   s.last_updated
            FROM contacts c
            LEFT JOIN contact_status s ON c.email = s.email
            WHERE c.is_deleted = 0
            ORDER BY CAST(c.employees AS INTEGER) DESC
        ''')

        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        print(f"✅ 成功获取 {len(contacts)} 条联系人记录")
        return contacts
    except Exception as e:
        print(f"❌ 获取联系人失败：{e}")
        return []

# 更新联系状态
def update_contact_status(email, field, value):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    # 确保记录存在
    cursor.execute('INSERT OR IGNORE INTO contact_status (email) VALUES (?)', (email,))

    # 更新字段
    if field in ['linkedin_contacted', 'whatsapp_contacted', 'email_contacted', 'phone_contacted', 'responded']:
        cursor.execute(f'''
            UPDATE contact_status
            SET {field} = ?, last_updated = CURRENT_TIMESTAMP
            WHERE email = ?
        ''', (value, email))
    elif field == 'notes':
        cursor.execute('''
            UPDATE contact_status
            SET notes = ?, last_updated = CURRENT_TIMESTAMP
            WHERE email = ?
        ''', (value, email))

    conn.commit()
    conn.close()
    return True

# 软删除联系人
def soft_delete_contact(email):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE contacts
        SET is_deleted = 1
        WHERE email = ?
    ''', (email,))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# 恢复已删除的联系人
def restore_contact(email):
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE contacts
        SET is_deleted = 0
        WHERE email = ?
    ''', (email,))

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# 获取已删除的联系人列表
def get_deleted_contacts():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.*,
               COALESCE(s.linkedin_contacted, 0) as linkedin_contacted,
               COALESCE(s.whatsapp_contacted, 0) as whatsapp_contacted,
               COALESCE(s.email_contacted, 0) as email_contacted,
               COALESCE(s.phone_contacted, 0) as phone_contacted,
               COALESCE(s.responded, 0) as responded,
               COALESCE(s.notes, '') as notes,
               s.last_updated
        FROM contacts c
        LEFT JOIN contact_status s ON c.email = s.email
        WHERE c.is_deleted = 1
        ORDER BY c.name
    ''')

    contacts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return contacts

# 导出数据到CSV
def export_to_csv(filename):
    contacts = get_all_contacts()

    if not contacts:
        return None

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = [
            '姓名', '职位', '公司', '邮箱', 'Website', 'LinkedIn',
            'Industry', 'Employees', '优先级', '背景说明', '邀约切入点',
            '微软产品', '营销技术栈产品', '全球性企业标记', '全球化判定依据',
            'LinkedIn联系状态', 'WhatsApp联系状态', 'Email联系状态', '电话联系状态', '有响应',
            '备注', '最后更新时间'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            writer.writerow({
                '姓名': contact['name'],
                '职位': contact['title'],
                '公司': contact['company'],
                '邮箱': contact['email'],
                'Website': contact['website'],
                'LinkedIn': contact['linkedin'],
                'Industry': contact['industry'],
                'Employees': contact['employees'],
                '优先级': contact['priority'],
                '背景说明': contact['background'],
                '邀约切入点': contact['approach'],
                '微软产品': contact['ms_products'],
                '营销技术栈产品': contact['marketing_tech'],
                '全球性企业标记': contact['is_global'],
                '全球化判定依据': contact['global_reason'],
                'LinkedIn联系状态': '已联系' if contact['linkedin_contacted'] else '未联系',
                'WhatsApp联系状态': '已联系' if contact['whatsapp_contacted'] else '未联系',
                'Email联系状态': '已联系' if contact['email_contacted'] else '未联系',
                '电话联系状态': '已联系' if contact['phone_contacted'] else '未联系',
                '有响应': '已响应' if contact['responded'] else '未响应',
                '备注': contact['notes'],
                '最后更新时间': contact['last_updated'] or ''
            })

    return filepath

def export_responded_contacts_csv(filename):
    contacts = [contact for contact in get_all_contacts() if contact.get('responded')]

    if not contacts:
        return None

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['姓名', '岗位', '公司', 'LinkedIn', '邮箱']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            writer.writerow({
                '姓名': contact.get('name', ''),
                '岗位': contact.get('title', ''),
                '公司': contact.get('company', ''),
                'LinkedIn': contact.get('linkedin', ''),
                '邮箱': contact.get('email', '')
            })

    return filepath

# 路由
# 处理 favicon 请求（避免404日志）
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            import_csv_data(filepath)
            return jsonify({'success': True, 'message': '导入成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})

    return jsonify({'success': False, 'message': '请上传CSV文件'})

@app.route('/api/contacts')
def get_contacts():
    try:
        contacts = get_all_contacts()
        return jsonify({'success': True, 'data': contacts})
    except Exception as e:
        print(f"❌ API错误：{e}")
        return jsonify({'success': False, 'message': str(e), 'data': []})

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.json
    email = data.get('email')
    field = data.get('field')
    value = data.get('value')

    if not email or not field:
        return jsonify({'success': False, 'message': '参数错误'})

    try:
        update_contact_status(email, field, value)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete_contact', methods=['POST'])
def delete_contact():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'success': False, 'message': '缺少邮箱参数'})

    try:
        success = soft_delete_contact(email)
        if success:
            return jsonify({'success': True, 'message': '联系人已删除'})
        else:
            return jsonify({'success': False, 'message': '删除失败，未找到该联系人'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/deleted_contacts')
def deleted_contacts():
    contacts = get_deleted_contacts()
    return jsonify({'success': True, 'data': contacts})

@app.route('/api/restore_contact', methods=['POST'])
def restore_contact_route():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'success': False, 'message': '缺少邮箱参数'})

    try:
        success = restore_contact(email)
        if success:
            return jsonify({'success': True, 'message': '联系人已恢复'})
        else:
            return jsonify({'success': False, 'message': '恢复失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/export')
def export_data():
    filename = f'联系记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = export_to_csv(filename)

    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        return jsonify({'success': False, 'message': '导出失败'})

@app.route('/api/export_responded')
def export_responded_data():
    filename = f'responded_contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = export_responded_contacts_csv(filename)

    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        return jsonify({'success': False, 'message': '没有有响应联系人可导出'})

def _generate_message_content(contact):
    """生成个性化LinkedIn邀请消息，返回标题和消息内容"""
    name = contact.get('name', '').split()[0] if contact.get('name') else 'there'
    title = contact.get('title', '')
    company = contact.get('company', '')
    industry = contact.get('industry', '')
    employees = contact.get('employees', '')

    # 生成吸引人的标题
    if industry:
        subject = f"Exclusive Invite: AI Roundtable for {industry} Leaders at Microsoft Singapore"
    elif company:
        subject = f"Exclusive Invite: AI Executive Roundtable at Microsoft Singapore"
    else:
        subject = "Exclusive Invite: AI Roundtable at Microsoft Singapore - 12 Seats Only"

    # 根据职位确定称呼
    if any(term in title.upper() for term in ['CEO', 'CHIEF', 'PRESIDENT', 'FOUNDER', 'MANAGING DIRECTOR']):
        greeting = f"Dear {name}"
    elif any(term in title.upper() for term in ['VP', 'DIRECTOR', 'HEAD', 'GENERAL MANAGER']):
        greeting = f"Hi {name}"
    else:
        greeting = f"Hello {name}"

    # 基于职位和公司生成专业的个性化理由
    personalized_reason = _build_personalized_reason(title, company, industry, employees)

    # 活动报名链接
    event_link = "https://www.linkedin.com/events/7435129035216678912?viewAsMember=true"

    # 核心邀请内容
    message = f"""{greeting},

I'm Chunbo from Socialhub.AI, and I'm excited to invite you to an exclusive event we're co-hosting with Microsoft.

**Socialhub.AI Global Tour - 3rd Stop: Singapore**
**Topic: Retail AI - From Pilot to Infrastructure**

This is an intimate executive roundtable limited to just 12 seats, designed for senior leaders who are navigating the journey from AI experimentation to enterprise-scale implementation.

**Event Details:**
- Date: Wednesday, March 18th, 2026 (Morning session)
- Venue: Microsoft Office, Singapore
- Format: Closed-door roundtable discussion

{personalized_reason}

Would you be interested in joining us? I'd be happy to share more about the agenda and confirmed participants.

Register here: {event_link}

Looking forward to hearing from you!

Best regards,
Chunbo Huang
Founder & CEO, Socialhub.AI
+1 425-922-5280"""

    # 300字符浓缩版本（用于LinkedIn连接请求）
    short_message = f"""{greeting}, I'm Chunbo from Socialhub.AI. We're co-hosting an exclusive AI Roundtable with Microsoft Singapore on March 18th - only 12 seats. Topic: Retail AI - From Pilot to Infrastructure. Would love to have you join us! Details: {event_link}"""

    return {'subject': subject, 'message': message, 'short_message': short_message}

def _build_personalized_reason(title, company, industry, employees):
    """根据职位、公司、行业生成专业的个性化邀请理由"""
    title_upper = title.upper() if title else ''

    # 判断公司规模
    try:
        emp_count = int(str(employees).replace(',', '').replace('+', ''))
        is_large_enterprise = emp_count > 5000
    except:
        is_large_enterprise = False

    # 根据职位类型定制
    if any(term in title_upper for term in ['CEO', 'CHIEF EXECUTIVE', 'PRESIDENT', 'FOUNDER']):
        role_context = f"As a visionary leader at {company}"
    elif any(term in title_upper for term in ['CTO', 'CIO', 'CHIEF TECHNOLOGY', 'CHIEF INFORMATION', 'CHIEF DIGITAL']):
        role_context = f"Given your role driving technology strategy at {company}"
    elif any(term in title_upper for term in ['CMO', 'CHIEF MARKETING', 'CHIEF GROWTH']):
        role_context = f"With your expertise in driving growth and customer engagement at {company}"
    elif any(term in title_upper for term in ['VP', 'VICE PRESIDENT']):
        role_context = f"As a senior leader at {company}"
    elif any(term in title_upper for term in ['DIRECTOR', 'HEAD']):
        role_context = f"Given your leadership role at {company}"
    elif any(term in title_upper for term in ['MANAGER', 'LEAD']):
        role_context = f"With your hands-on experience at {company}"
    else:
        role_context = f"Given your role at {company}"

    # 根据行业定制
    industry_lower = industry.lower() if industry else ''
    if any(term in industry_lower for term in ['retail', 'e-commerce', 'ecommerce', 'consumer']):
        industry_context = "your insights on retail transformation and customer experience"
    elif any(term in industry_lower for term in ['hospitality', 'hotel', 'travel', 'tourism']):
        industry_context = "your perspective on hospitality innovation and guest experience"
    elif any(term in industry_lower for term in ['finance', 'banking', 'insurance', 'fintech']):
        industry_context = "your experience in financial services digital transformation"
    elif any(term in industry_lower for term in ['technology', 'software', 'internet', 'tech']):
        industry_context = "your deep understanding of technology adoption at scale"
    elif any(term in industry_lower for term in ['manufacturing', 'industrial']):
        industry_context = "your insights on industrial AI and operational excellence"
    elif any(term in industry_lower for term in ['healthcare', 'medical', 'pharma']):
        industry_context = "your perspective on healthcare innovation"
    elif any(term in industry_lower for term in ['media', 'entertainment', 'gaming']):
        industry_context = "your insights on content and audience engagement"
    elif any(term in industry_lower for term in ['food', 'beverage', 'restaurant', 'f&b']):
        industry_context = "your experience in F&B digital transformation"
    else:
        industry_context = "your valuable industry perspective"

    # 组合成完整的个性化理由
    if is_large_enterprise:
        scale_note = "would be particularly valuable as we discuss scaling AI from pilot to enterprise infrastructure"
    else:
        scale_note = "would greatly enrich our discussion on practical AI implementation"

    return f"{role_context}, {industry_context} {scale_note}."

@app.route('/api/generate_linkedin_message/<email>')
def generate_linkedin_message(email):
    """生成个性化LinkedIn邀请消息"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM contacts WHERE email = ? AND is_deleted = 0', (email,))
        contact = cursor.fetchone()
        conn.close()

        if not contact:
            return jsonify({'success': False, 'message': '未找到该联系人'})

        contact_dict = dict(contact)
        result = _generate_message_content(contact_dict)
        subject = result['subject']
        message = result['message']
        short_message = result['short_message']

        # LinkedIn InMail limits: Subject ~200 chars, Body ~1900 chars
        # Connection request: ~300 chars
        subject_limit = 200
        message_limit = 1900
        short_message_limit = 300

        subject_length = len(subject)
        message_length = len(message)
        short_message_length = len(short_message)

        subject_warning = subject_length > subject_limit
        message_warning = message_length > message_limit
        short_message_warning = short_message_length > short_message_limit

        return jsonify({
            'success': True,
            'subject': subject,
            'message': message,
            'short_message': short_message,
            'length_info': {
                'subject_length': subject_length,
                'subject_limit': subject_limit,
                'subject_warning': subject_warning,
                'message_length': message_length,
                'message_limit': message_limit,
                'message_warning': message_warning,
                'short_message_length': short_message_length,
                'short_message_limit': short_message_limit,
                'short_message_warning': short_message_warning
            },
            'contact': {
                'name': contact_dict.get('name'),
                'title': contact_dict.get('title'),
                'company': contact_dict.get('company'),
                'linkedin': contact_dict.get('linkedin')
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 在应用加载时初始化数据库（Gunicorn启动时也会执行）
try:
    init_db()
    print("🚀 应用启动：数据库初始化成功")
except Exception as e:
    print(f"⚠️ 数据库初始化警告：{e}")

if __name__ == '__main__':
    # 本地开发模式
    print("=" * 60)
    print("🎯 新加坡活动联系人管理系统")
    print("=" * 60)
    print("🌐 本地开发服务器启动中...")
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"📍 服务器地址: {host}:{port}")
    print("=" * 60)
    app.run(debug=False, host=host, port=port)
