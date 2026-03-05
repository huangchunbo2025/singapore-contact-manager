"""
个性化LinkedIn邀请消息生成器
Socialhub.AI Global Tour - Singapore 活动邀请
"""

import sqlite3
import sys

# 活动信息
EVENT_INFO = {
    'name': 'Socialhub.AI Global Tour - Singapore',
    'subtitle': 'From Pilot to Infrastructure',
    'date': '2026年3月18日（星期三）',
    'time': '9:30 AM',
    'location': 'Microsoft Singapore, Frasers Tower',
    'seats': '12',
    'focus': 'AI从试点到基础设施的转变',
    'register_link': 'https://www.linkedin.com/events/7435129035216678912?viewAsMember=true'
}

def generate_message(contact):
    """根据联系人信息生成个性化消息"""

    name = contact.get('name', '').split()[0] if contact.get('name') else 'Hi'
    title = contact.get('title', '')
    company = contact.get('company', '')
    industry = contact.get('industry', '')
    employees = contact.get('employees', '')
    background = contact.get('background', '')
    approach = contact.get('approach', '')
    ms_products = contact.get('ms_products', '')

    # 根据职位确定称呼
    if any(term in title.upper() for term in ['CEO', 'CHIEF', 'PRESIDENT', 'FOUNDER']):
        greeting = f"Dear {name}"
    elif any(term in title.upper() for term in ['VP', 'DIRECTOR', 'HEAD']):
        greeting = f"Hi {name}"
    else:
        greeting = f"Hello {name}"

    # 个性化开场
    if 'AI' in background or 'AI' in approach:
        opening = f"I noticed {company}'s progressive work in AI transformation, particularly in the {industry} sector."
    elif ms_products and 'Azure' in ms_products:
        opening = f"As {company} leverages Azure for digital transformation, I thought you'd be interested in this exclusive opportunity."
    elif 'digital' in background.lower() or 'transformation' in background.lower():
        opening = f"Given {company}'s digital transformation journey in {industry}, I believe this would be highly relevant for you."
    else:
        opening = f"As a leader driving innovation at {company}, I wanted to personally invite you to an exclusive event."

    # 根据公司规模定制内容
    if employees and int(employees.replace('+', '').replace(',', '')) > 1000:
        scale_note = "This enterprise-focused roundtable addresses the unique challenges large organizations face when scaling AI initiatives."
    else:
        scale_note = "This intimate roundtable brings together forward-thinking leaders to discuss practical AI implementation strategies."

    # 核心邀请内容
    message = f"""{greeting},

{opening}

We're hosting an exclusive **invite-only roundtable** at **Microsoft Singapore on March 18th** (limited to just 12 C-level executives):

**🎯 Socialhub.AI Global Tour - Singapore: From Pilot to Infrastructure**

**Why This Matters:**
• 74% of AI initiatives never move beyond pilot stage
• Focus: Architecture, governance & operational models (not just tools)
• Real talk: Transitioning from fragmented pilots to enterprise-ready AI infrastructure

**Two Key Discussions:**
1. From Pilot to Production-Ready AI Systems
2. Loyalty Architecture Evolution in the AI Era

{scale_note}

**🗓️ March 18, 2026 | 9:30 AM**
**📍 Microsoft Singapore, Frasers Tower (Level 23-25)**

Given your role as {title} at {company}, your insights would be invaluable to this conversation."""

    # 根据切入点添加个性化结尾
    register_link = EVENT_INFO['register_link']

    if approach:
        closing = f"""

**Why I'm reaching out:** {approach}

Would you be available to join us? I'd be happy to share more details about the agenda and participants.

Register here: {register_link}

Looking forward to your thoughts!

Best regards,
Chunbo"""
    else:
        closing = f"""

This is a unique opportunity to connect with peers tackling similar challenges. Would you be available to join us?

I'd be happy to share more details about the full agenda and confirmed participants.

Register here: {register_link}

Looking forward to hearing from you!

Best regards,
Chunbo"""

    return message + closing


def generate_batch_messages(db_path='contacts.db'):
    """批量生成所有联系人的个性化消息"""

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM contacts
            WHERE is_deleted = 0
            ORDER BY CAST(employees AS INTEGER) DESC
        ''')

        contacts = cursor.fetchall()
        conn.close()

        if not contacts:
            print("❌ 数据库中没有联系人")
            return

        print(f"📊 共找到 {len(contacts)} 个联系人")
        print("=" * 80)

        # 生成每个联系人的消息
        for i, contact in enumerate(contacts, 1):
            contact_dict = dict(contact)
            print(f"\n{'='*80}")
            print(f"联系人 #{i}: {contact_dict.get('name')} - {contact_dict.get('title')}")
            print(f"公司: {contact_dict.get('company')}")
            print(f"邮箱: {contact_dict.get('email')}")
            print(f"LinkedIn: {contact_dict.get('linkedin')}")
            print("=" * 80)
            print(generate_message(contact_dict))
            print("\n" + "=" * 80)
            print()

        return contacts

    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


def generate_single_message(email, db_path='contacts.db'):
    """为单个联系人生成消息"""

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM contacts WHERE email = ? AND is_deleted = 0', (email,))
        contact = cursor.fetchone()
        conn.close()

        if not contact:
            print(f"❌ 未找到邮箱为 {email} 的联系人")
            return None

        contact_dict = dict(contact)
        message = generate_message(contact_dict)

        print(f"\n{'='*80}")
        print(f"联系人: {contact_dict.get('name')} - {contact_dict.get('title')}")
        print(f"公司: {contact_dict.get('company')}")
        print(f"LinkedIn: {contact_dict.get('linkedin')}")
        print("=" * 80)
        print(message)
        print("=" * 80)

        return message

    except Exception as e:
        print(f"❌ 错误: {e}")
        return None


if __name__ == '__main__':
    print("🎯 Socialhub.AI Global Tour - Singapore")
    print("📧 个性化LinkedIn邀请消息生成器")
    print("=" * 80)

    if len(sys.argv) > 1:
        # 为指定邮箱生成消息
        email = sys.argv[1]
        print(f"\n为 {email} 生成个性化消息...")
        generate_single_message(email)
    else:
        # 批量生成所有联系人的消息
        print("\n批量生成模式...")
        generate_batch_messages()
