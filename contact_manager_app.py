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

# 检测是否在生产环境（Render/Heroku 等会设置 PORT 环境变量）
IS_PRODUCTION = os.environ.get('PORT') is not None

if IS_PRODUCTION:
    # 生产环境：使用 /tmp 目录（可写）
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    app.config['DATABASE'] = '/tmp/contacts.db'
    print("🌐 生产环境模式：数据库位置 /tmp/contacts.db")
else:
    # 本地开发环境
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['DATABASE'] = 'contacts.db'
    print("💻 开发环境模式：数据库位置 contacts.db")

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据库初始化
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

    # 检查是否需要添加 is_deleted 列（兼容旧版本）
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'is_deleted' not in columns:
        cursor.execute('ALTER TABLE contacts ADD COLUMN is_deleted INTEGER DEFAULT 0')
        print("✓ 已添加 is_deleted 列")

    # 联系状态表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            linkedin_contacted INTEGER DEFAULT 0,
            whatsapp_contacted INTEGER DEFAULT 0,
            email_contacted INTEGER DEFAULT 0,
            phone_contacted INTEGER DEFAULT 0,
            notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES contacts(email)
        )
    ''')

    conn.commit()
    conn.close()

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
                cursor.execute('''
                    INSERT OR REPLACE INTO contacts
                    (name, title, company, email, website, linkedin, industry, employees,
                     priority, background, approach, ms_products, marketing_tech, is_global, global_reason, is_deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (
                    row.get('姓名', ''),
                    row.get('职位', ''),
                    row.get('公司', ''),
                    row.get('邮箱', ''),
                    row.get('Website', ''),
                    row.get('LinkedIn', ''),
                    row.get('Industry', ''),
                    row.get('Employees', ''),
                    row.get('优先级', ''),
                    row.get('背景说明', ''),
                    row.get('邀约切入点', ''),
                    row.get('微软产品', ''),
                    row.get('营销技术栈产品', ''),
                    row.get('全球性企业标记', ''),
                    row.get('全球化判定依据', '')
                ))

                # 初始化联系状态
                email = row.get('邮箱', '')
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
    if field in ['linkedin_contacted', 'whatsapp_contacted', 'email_contacted', 'phone_contacted']:
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
            'LinkedIn联系状态', 'WhatsApp联系状态', 'Email联系状态', '电话联系状态',
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
                '备注': contact['notes'],
                '最后更新时间': contact['last_updated'] or ''
            })

    return filepath

# 路由
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

if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("🎯 新加坡活动联系人管理系统")
    print("=" * 60)
    print("📊 数据库已初始化")
    print("🌐 服务器启动中...")
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"📍 服务器地址: {host}:{port}")
    print("=" * 60)
    app.run(debug=False, host=host, port=port)
